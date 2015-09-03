import sh
import subprocess

from templates import wrap_in_env, wrap_in_vz


__all__ = [
    'LocalRunner',
    'VzRunner',
    'SshRunner',
    'SshToVzRunner',
]


class SshToVzRunner(object):

    def __init__(self, ctid, host, port=22, ssh_options=[]):
        """
        Create a Runner to access a vz container on a remote host.

        Parameters
        ----------
        host : string
            hostname or ip of the target machine
        ctid : int
            ctid of the target machine
        ssh_options : list of flags to ssh
            ssh options, e.g. ['-p', '2222', '-o', 'StrictHostKeyChecking=no']
        """
        self.ssh_runner = SshRunner(host, port, ssh_options)
        self.ctid = ctid

    def run(self, commands):
        """
        Run a command or a script of commands on the target machine.
        """
        wrapped_commands = wrap_in_vz(commands, self.ctid)
        return self.ssh_runner.run(wrapped_commands)

    def copy_from(self, src, dest):
        """
        Copy from a location `src` on the remote machine to a location
        `dest` on the local machine.
        """
        vz_src = self.get_vz_dir(src)
        return self.ssh_runner.copy_from(vz_src, dest)

    def copy_to(self, src, dest):
        """
        Copy from a location `src` on the local machine to a location
        `dest` on the remote machine.
        """
        vz_dest = self.get_vz_dir(dest)
        return self.ssh_runner.copy_to(src, vz_dest)

    def interactive(self):
        "Open an interactive shell on the target machine"
        subprocess.call(self.cmd(), shell=True)

    def cmd(self):
        """
        Return as a string the shell command to boot an interactive shell
        on the target
        """
        return "%s vzctl enter %s" % (self.ssh_runner.cmd(), self.ctid)

    def get_vz_dir(self, path):
        """
        Get the directory (relative to the host) corresponding to path
        `path` withing the vz container.
        """
        return '/vz/root/%d/%s' % (self.ctid, path)


class SshRunner(object):

    def __init__(self, host, port=22, ssh_options=[]):
        """
        Parameters
        ----------
        host : string
            hostname or ip of the target machine
        ssh_options : list of flags to ssh
            ssh options, e.g. ['-p', '2222', '-o', 'StrictHostKeyChecking=no']
        """
        self.host = host
        self.port = port
        self.ssh_options = ['-p', '%d' % port]
        self.scp_options = ['-P', '%d' % port]
        self.ssh_options.extend(ssh_options)
        self.scp_options.extend(ssh_options)
        self.ssh = sh.ssh.bake(self.ssh_options)
        self.scp = sh.scp.bake(self.scp_options)

    def run(self, commands):
        "Run a command or a script of commands on the target machine"
        return self.ssh(self.host, _in=commands)

    def copy_from(self, src, dest):
        """
        Copy from a location `src` on the remote machine to a location
        `dest` on the local machine.
        """
        return self.scp('-r', self.get_scp_dir(src), dest)

    def copy_to(self, src, dest):
        """
        Copy from a location `src` on the local machine to a location
        `dest` on the remote machine.
        """
        return self.scp('-r', src, self.get_scp_dir(dest))

    def get_scp_dir(self, path):
        return '%s:%s' % (self.host, path)

    def interactive(self):
        "Open an interactive shell on the target machine"
        subprocess.call(self.cmd('ssh'), shell=True)

    def cmd(self, which='ssh'):
        """
        Return as a string the shell command to boot an interactive shell
        on the target
        """
        if which == 'ssh':
            return "ssh %s %s" % (' '.join(self.ssh_options), self.host)
        elif which == 'scp':
            return "scp %s %s" % (' '.join(self.scp_options), self.host)
        else:
            raise ValueError('`which` should be either "ssh" or "scp"')


class VzRunner(object):

    def __init__(self, ctid):
        """
        Parameters
        ----------
        ctid : int
            ctid of the target machine
        """
        self.ctid = ctid

    def run(self, commands):
        """
        Run a command or a script of commands on the target machine.

        The run is with vzctl exec2, so the environment may not be quite right.
        We attempt to define HOME and USER, and source all the usual files, in
        order to minimize this problem.

        """
        wrapped_commands = wrap_in_env(commands)
        return sh.vzctl('exec2', self.ctid, 'bash', _in=wrapped_commands)

    def copy_from(self, src, dest):
        """
        Copy from a location `src` on the remote machine to a location
        `dest` on the local machine.
        """
        return sh.cp('-r', self.get_vz_dir(src), dest)

    def copy_to(self, src, dest):
        """
        Copy from a location `src` on the local machine to a location
        `dest` on the remote machine.
        """
        return sh.cp('-r', src, self.get_vz_dir(dest))

    def interactive(self):
        "Open an interactive shell on the target machine"
        subprocess.call(self.cmd(), shell=True)

    def cmd(self):
        """
        Return as a string the shell command to boot an interactive shell
        on the target
        """
        return "vzctl enter %s" % self.ctid

    def get_vz_dir(self, path):
        return '/vz/root/%d/%s' % (self.ctid, path)


class LocalRunner(object):

    def __init__(self, ctid):
        """
        Parameters
        ----------
        """
        self.ctid = ctid

    def run(self, commands):
        """
        Run a command or a script of commands on the local machine.

        Obviously this is silly, the point is to have the same api for all
        four environments: local, vz, ssh, and ssh to vz.

        """
        return sh.bash(_in=commands)

    def copy_from(self, src, dest):
        """
        Copy from a location `src` on the remote machine to a location
        `dest` on the local machine.
        """
        return sh.cp('-r', src, dest)

    def copy_to(self, src, dest):
        """
        Copy from a location `src` on the local machine to a location
        `dest` on the remote machine.
        """
        return sh.cp('-r', src, dest)

    def interactive(self):
        "Open an interactive shell on the target machine"
        subprocess.call(self.cmd(), shell=True)

    def cmd(self):
        """
        Return as a string the shell command to boot an interactive shell
        on the target
        """
        return "bash"
