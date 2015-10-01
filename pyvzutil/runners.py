import sys
import sh
import subprocess

from templates import wrap_in_vz


__all__ = [
    'Runner',
    'SshRunner',
    'LocalRunner',
    'VzRunner',
    'RunnerError',
]


def pse(line):
    "Print a line of output to stderr of the python process."
    sys.stderr.write(line)


class Runner(object):

    def __init__(self):
        """
        Create a class which can run commands, open interactive
        sessions, and copy files to and from a computer. The computer could
        be the local machine, a remote host, a local vz instance, or a vz
        instance on a remote host.

        For most commands, errors are converted from sh exceptions - which
        know about the command, the exit code, and stdout/stderr - to
        RunnerErrors which also know about stdin. This is needed because many
        of the operations are run by opening remote sessions and then sending
        commands over stdin.

        Most commands have a `verbose` flag which will print the remote
        command's stdout and stderr to the python process' stderr. This can
        be useful for getting feedback about the progress of long-running
        operations.

        """
        self._raise()

    def run(self, commands, verbose=True):
        """
        Run the commands in the srting `command` on the target machine, and
        return a sh object representing the output.

        Return a sh object encapsulating the command, stderr, and stdout. If
        used as a string, the object evaluates to stdout.

        """
        self._raise()

    def copy_from(self, src, dest, verbose=True):
        """
        Copy from a location `src` on the target machine to a location
        `dest` on the local machine.

        """
        self._raise()

    def copy_to(self, src, dest, verbose=True):
        """
        Copy from a location `src` on the local machine to a location
        `dest` on the target machine.

        """
        self._raise()

    def sync_from(self, src, dest, verbose=True):
        """
        Sync from a location `src` on the target machine to a location
        `dest` on the local machine.

        Note: the behavior of copy_from should match cp / scp behavior,
        whereas the behavior of sync_from should match rsync -aH behavior.

        """
        self._raise()

    def sync_to(self, src, dest, verbose=True):
        """
        Copy from a location `src` on the local machine to a location
        `dest` on the target machine.

        Note: the behavior of copy_to should match cp / scp behavior,
        whereas the behavior of sync_to should match rsync -aH behavior.

        """
        self._raise()

    def interactive(self):
        """
        Open an interactive shell on the target machine.

        """
        self._raise()

    def cmd(self):
        """
        Return as a string the shell command that would open an interactive
        session on the target machine.

        """
        self._raise()

    def _raise(self):
        raise NotImplementedError("Runner is an abstract class")


class VzRunner(Runner):

    def __init__(self, ctid, outer_runner):
        """
        Create a Runner to access a vz container on a remote host.

        Parameters
        ----------
        ctid : int
            ctid of the target machine
        outer_runner : Runner
            A runner (e.g., a LocalRunner or an SshRunner) giving access to
            the host where the vz instance is running.

        """
        self.ctid = ctid
        self.outer_runner = outer_runner

    @classmethod
    def over_ssh(cls, ctid, host, user='root', port=22, ssh_options=[]):
        "Create a Runner for access to a remote vz container via ssh"
        if '-t' not in ssh_options:
            ssh_options.append('-t')
        ssh_runner = SshRunner(host, user, port, ssh_options)
        return cls(ctid, ssh_runner)

    @classmethod
    def local(cls, ctid):
        "Create a runner for access to a vz container running on localhost"
        local_runner = LocalRunner()
        return cls(ctid, local_runner)

    def run(self, commands, verbose=True):
        wrapped_commands = wrap_in_vz(commands, self.ctid)
        return self.outer_runner.run(wrapped_commands, verbose=verbose)

    def copy_from(self, src, dest, verbose=True):
        vz_src = self.get_vz_dir(src)
        return self.outer_runner.copy_from(vz_src, dest, verbose=verbose)

    def copy_to(self, src, dest, verbose=True):
        vz_dest = self.get_vz_dir(dest)
        return self.outer_runner.copy_to(src, vz_dest, verbose=verbose)

    def sync_from(self, src, dest, verbose=True):
        vz_src = self.get_vz_dir(src)
        return self.outer_runner.sync_from(vz_src, dest, verbose=verbose)

    def sync_to(self, src, dest, verbose=True):
        vz_dest = self.get_vz_dir(dest)
        return self.outer_runner.sync_to(src, vz_dest, verbose=verbose)

    def interactive(self):
        subprocess.call(self.cmd(), shell=True)

    def cmd(self):
        return "%s vzctl enter %s" % (self.outer_runner.cmd(), self.ctid)

    def get_vz_dir(self, path):
        """
        Get the directory (relative to the host) corresponding to path
        `path` withing the vz container.
        """
        return '/vz/root/%d/%s' % (self.ctid, path)


class SshRunner(Runner):

    def __init__(self, host, user='root', port=22, ssh_options=[]):
        """
        Create a Runner for access to a remote host over ssh.

        Parameters
        ----------
        host : string
            hostname or ip of the target machine
        user : string
            username on the target machine
        port : int
            the port to use for ssh access
        ssh_options : list of flags to ssh
            ssh options, e.g. ['-p', '2222', '-o', 'StrictHostKeyChecking=no']
        """
        self.host = host
        self.user = user
        self.target = '%s@%s' % (user, host)
        self.port = port
        # set ssh and scp options. This code is needed because -p vs -P, and
        # because ssh needs -t in many cases, but scp doesn't take -t.
        self.ssh_options = ['-p', '%d' % port]
        self.scp_options = ['-P', '%d' % port]
        self.ssh_options.extend(ssh_options)
        self.scp_options.extend([o for o in ssh_options if o != '-t'])
        if '-t' not in self.ssh_options:
            self.ssh_options.append('-t')
        # set rsync options. The ssh options go inside the -e argument
        self.rsync_options = [
            '-e', 'ssh {}'.format(' '.join(self.ssh_options)),
            '-aHz'
        ]
        # bake the commands
        self.ssh = sh.ssh.bake(self.ssh_options)
        self.scp = sh.scp.bake(self.scp_options)
        self.rsync = sh.rsync.bake(self.rsync_options)

    def run(self, commands, verbose=True):
        return run_sh_function(self.ssh, [self.target], commands, verbose)

    def copy_from(self, src, dest, verbose=True):
        return run_sh_function(self.scp, ['-r', self.get_scp_dir(src), dest],
                               None, verbose)

    def copy_to(self, src, dest, verbose=True):
        return run_sh_function(self.scp, ['-r', src, self.get_scp_dir(dest)],
                               None, verbose)

    def sync_from(self, src, dest, verbose=True):
        return run_sh_function(self.rsync, [self.get_scp_dir(src), dest],
                               None, verbose)

    def sync_to(self, src, dest, verbose=True):
        return run_sh_function(self.rsync, [src, self.get_scp_dir(dest)],
                               None, verbose)

    def interactive(self):
        subprocess.call(self.cmd('ssh'), shell=True)

    def cmd(self, which='ssh'):
        return "ssh %s %s" % (' '.join(self.ssh_options), self.target)

    def scp_cmd(self):
        """
        Since scp and ssh flags differ somewhat, we provide a separate
        function to get the preamble for scp operations to/from this machine.
        """
        return "scp %s %s" % (' '.join(self.scp_options), self.target)

    def get_scp_dir(self, path):
        "Get the representation of a remote dir (e.g. myhost:/tmp) for scp"
        return '%s:%s' % (self.target, path)


class LocalRunner(Runner):

    def __init__(self):
        """
        Create a Runner with the local machine as the target.

        """
        self.rsync = sh.rsync.bake('-aH')

    def run(self, commands, verbose=True):
        return run_sh_function(sh.bash, [], commands, verbose)

    def copy_from(self, src, dest, verbose=True):
        return run_sh_function(sh.cp, ['-r', src, dest], None, verbose)

    def copy_to(self, src, dest, verbose=True):
        return run_sh_function(sh.cp, ['-r', src, dest], None, verbose)

    def sync_from(self, src, dest, verbose=True):
        return run_sh_function(self.rsync, [src, dest],
                               None, verbose)

    def sync_to(self, src, dest, verbose=True):
        return run_sh_function(self.rsync, [src, dest],
                               None, verbose)

    def interactive(self):
        subprocess.call(self.cmd(), shell=True)

    def cmd(self):
        return "bash"


class RunnerError(Exception):

    def __init__(self, full_cmd, stdin, stdout, stderr, exit_code):
        self.full_cmd = full_cmd
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.msg = """
        RAN: %s

        STDIN: %s

        STDOUT: %s

        STDERR: %s

        EXIT_CODE: %d
        """ % (full_cmd, stdin, stdout, stderr, exit_code)
        super(RunnerError, self).__init__(self.msg)


def run_sh_function(sh_function, args, stdin=None, verbose=False):
    try:
        if verbose:
            return sh_function(args, _in=stdin,
                               _out=pse, _err=pse, _tee=True)
        else:
            return sh_function(args, _in=stdin)
    except sh.ErrorReturnCode as e:
        raise RunnerError(e.full_cmd, stdin or '', e.stdout, e.stderr,
                          e.exit_code)
