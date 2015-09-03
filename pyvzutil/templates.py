"Templates and wrapper functions for shell scripting"
# Environment for login shell, from possibly non-login -----------------------

ENV_TEMPLATE = """
su - root -c bash << \\%s
%s
%s
"""


def wrap_in_env(commands, eof_id='_EOF'):
    "Wrap a set of commands in a bash call that sets env up"
    return ENV_TEMPLATE % (eof_id, commands, eof_id)


# Templates to produce bash scripts via heredocs -----------------------------

# TODO think about this... both wrap_in_bash and wrap_in_bash_env are
#      potentially useful, but neither is currently used anywhere.

BASH_TEMPLATE = """bash << \\%s
%s
%s
"""


def wrap_in_bash(commands, eof_id='_EOF'):
    "Wrap a set of commands in a bash call with a heredoc"
    return BASH_TEMPLATE % (eof_id, commands, eof_id)


def wrap_in_bash_env(commands, eof_id='_EOF'):
    "Wrap a set of commands in a bash call that sets env up"
    eof_bash = '%s_VZ' % eof_id
    eof_env = '%s_ENV' % eof_id
    commands_in_env = wrap_in_env(commands, eof_env)
    return VZ_TEMPLATE % (eof_bash, commands_in_env, eof_bash)


# Templates to run scripts via bash over vz, with env ------------------------

VZ_TEMPLATE = """vzctl exec2 %d bash << \\%s
%s
%s
"""


def wrap_in_vz(commands, ctid, eof_id='_EOF'):
    "Wrap a set of commands in a vzctl exec2 bash call that sets env up"
    eof_vz = '%s_VZ' % eof_id
    eof_env = '%s_ENV' % eof_id
    commands_in_env = wrap_in_env(commands, eof_env)
    return VZ_TEMPLATE % (ctid, eof_vz, commands_in_env, eof_vz)
