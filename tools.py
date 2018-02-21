""" Grabbag collection of little tools """


from contextlib import contextmanager
from time import sleep
from signal import SIGALRM, signal, getsignal


_sleep = sleep


def sleep(seconds, *args, **kwargs):
    try:
        _sleep(seconds, *args, **kwargs)
    except TypeError:
        _sleep(seconds.total_seconds(), *args, **kwargs)


@contextmanager
def running_once(program_name: str, per_user: bool=False):
    from fcntl import lockf, LOCK_EX, LOCK_NB, LOCK_UN
    from os import getpid, getuid, SEEK_SET

    if per_user:
        program_name += f'_{getuid()}'

    with open(f'/tmp/{program_name}.pid', 'a') as f:
        lockf(f, LOCK_EX | LOCK_NB)  # EXclusive, Non-Blocking

        # Clear the file at this point.  We have acquired the lock, and since
        # we're opening in r+ instead of w this isn't done automatically for
        # us.  This is the right point to do it manually.
        f.seek(0, SEEK_SET)
        f.truncate()

        f.write(str(getpid()))
        f.flush()

        yield

        lockf(f, LOCK_UN)


@contextmanager
def signal_interruptable(sig=SIGALRM):
    class AlarmException(Exception):
        pass

    prev_handler = getsignal(sig)

    def handler(signal, frame):
        raise AlarmException()

    try:
        signal(sig, handler)
        yield
    except AlarmException:
        # Ignore it, but we are out of the block.
        pass
    finally:
        # Restore the saved handler.
        signal(sig, prev_handler)


def between(lower, x, upper):
    return min(max(lower, x), upper)
