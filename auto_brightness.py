#! /usr/bin/env nix-shell
#! nix-shell -i python -p "with python36Packages; [ephem python]"

import subprocess
from signal import signal, SIGUSR1, SIGUSR2

from contextlib import contextmanager

from math import exp, log as ln, sin, ceil

from time import sleep
from datetime import timedelta, datetime

import ephem


LOCATION = ephem.city('Amsterdam')
CHANGE_HALFTIME = timedelta(minutes=30)
SLEEP_TIME = timedelta(seconds=5)
CHANGE_PERCENTAGE = 20/100


_sleep = sleep


def sleep(seconds, *args, **kwargs):
    try:
        _sleep(seconds, *args, **kwargs)
    except TypeError:
        _sleep(seconds.total_seconds(), *args, **kwargs)


def get_current_brightness(here=LOCATION):
    sun = ephem.Sun(here)

    print(f'{sun.alt}°')
    Θ = float(sun.alt)

    x = exp(2 * sin(Θ) - 2)
    return ceil(100 * x)


def set_brightness(x):
    print(f'setting brightness to {x}')
    subprocess.check_call(["xbacklight", "-set", str(x)])


def between(lower, x, upper):
    return min(max(lower, x), upper)


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


def main():
    with running_once('auto_brightness'):
        offset = 0

        def handler(signum, frame):
            b = get_current_brightness()
            multiplier = {
                SIGUSR1: 1 + CHANGE_PERCENTAGE,
                SIGUSR2: 1 - CHANGE_PERCENTAGE
            }[signum]
            nonlocal offset
            offset = between(1, (b + offset) * multiplier, 100) - b
            set_brightness(b + offset)
            # print(offset)

        for signum in [SIGUSR1, SIGUSR2]:
            signal(signum, handler)

        t = datetime.now()
        loop_time = timedelta()
        while True:
            b = get_current_brightness()
            set_brightness(b + offset)

            mult = exp(-ln(2) * loop_time / CHANGE_HALFTIME)
            offset *= mult
            offset = between(1, (b + offset), 100) - b
            print(f"offset: {offset}")

            sleep(SLEEP_TIME)
            loop_time, t = datetime.now() - t, datetime.now()
            print(f"loop time: {loop_time}")


if __name__ == "__main__":
    print("Starting")
    main()
    print("Done")
