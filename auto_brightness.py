#! /usr/bin/env nix-shell
#! nix-shell -i python -p "with python3Packages; [ephem python]" xorg.xbacklight

from tools import *

import subprocess
from signal import signal, SIGUSR1, SIGUSR2

from math import exp, log as ln, sin, ceil

from datetime import timedelta, datetime

import ephem


CITY = 'Amsterdam'
CHANGE_HALFTIME = timedelta(minutes=30)
SLEEP_TIME = timedelta(seconds=5)
CHANGE_PERCENTAGE = 20/100


def get_current_brightness(here=None, sun=None):
    assert sun is None or here is None

    if here is None:
        here = ephem.city(CITY)

    if sun is None:
        sun = ephem.Sun(here)

    Θ = sun.alt
    print(f'{Θ}°')

    x = exp(2 * sin(Θ) - 2)
    return ceil(100 * x)


def set_brightness(x):
    print(f'setting brightness to {x}')
    subprocess.check_call(["xbacklight", "-set", str(x)])


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
            offset = between(1, (offset + b) * multiplier, 100) - b
            set_brightness(b + offset)

        for signum in [SIGUSR1, SIGUSR2]:
            signal(signum, handler)

        t = datetime.now()
        loop_time = timedelta()
        while True:
            b = get_current_brightness()

            mult = exp(-ln(2) * loop_time / CHANGE_HALFTIME)
            offset *= mult
            offset = between(1, (offset + b), 100) - b
            print(f"offset: {offset}")

            set_brightness(b + offset)

            sleep(SLEEP_TIME)
            loop_time, t = datetime.now() - t, datetime.now()
            print(f"loop time: {loop_time}")


if __name__ == "__main__":
    print("Starting")
    main()
    print("Done")
