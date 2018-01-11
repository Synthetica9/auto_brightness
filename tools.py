""" Grabbag collection of little tools """


from contextlib import contextmanager
from time import sleep


_sleep = sleep


def sleep(seconds, *args, **kwargs):
    try:
        _sleep(seconds, *args, **kwargs)
    except TypeError:
        _sleep(seconds.total_seconds(), *args, **kwargs)


@contextmanager
def running_once(program_name: str, per_user: bool=False):
    from fcntl import lockf, LOCK_EX, LOCK_NB, LOCK_UN
    from os import getpid, getuid

    if per_user:
        program_name += f'_{getuid()}'

    with open(f'/tmp/{program_name}.pid', 'w') as f:
        lockf(f, LOCK_EX | LOCK_NB)  # EXclusive, Non-Blocking
        f.write(str(getpid()))
        f.flush()

        yield

        lockf(f, LOCK_UN)


def between(lower, x, upper):
    return min(max(lower, x), upper)
