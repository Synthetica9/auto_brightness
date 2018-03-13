#! /usr/bin/env nix-shell
#! nix-shell -i python -p "with python3Packages; [ephem python]" xorg.xbacklight

from tools import *

import subprocess
from signal import signal, SIGUSR1, SIGUSR2, SIGALRM, SIG_IGN

from math import exp, log as ln, sin, ceil

from datetime import timedelta, datetime

import ephem

# CONFIGURABLES
CITY = 'Amsterdam'
CHANGE_HALFTIME = timedelta(minutes=60)
SLEEP_TIME = timedelta(seconds=5)
CHANGE_PERCENTAGE = 20/100

BRIGHTNESS_UP = SIGUSR1
BRIGHTNESS_DOWN = SIGUSR2

MAX_OVERDRIVE_PRESSES = 1
MAX_BRIGHTNESS = 100 * (1 + CHANGE_PERCENTAGE) ** MAX_OVERDRIVE_PRESSES

DOCKED_BRIGHTNESS = 100
# END OF CONFIGURABLES


def get_num_displays():
    result = subprocess.check_output(["xrandr", "--listactivemonitors"])
    return result.count(b"\n") - 1


def is_external_display_connected():
    return get_num_displays() > 1


def get_current_brightness(here=None, sun=None):
    if is_external_display_connected():
        return DOCKED_BRIGHTNESS

    assert [sun, here].count(None) >= 1

    if here is None:
        here = ephem.city(CITY)

    if sun is None:
        sun = ephem.Sun(here)

    Θ = sun.alt
    print(f'{Θ}°')

    x = exp(2 * sin(Θ) - 2)
    return max(1.0, 100 * x)


def set_brightness(x):
    print(f'setting brightness to {x}')
    subprocess.check_call(["xbacklight", "-set", str(x)])


def normalize_offset(offset, b=None):
    if b is None:
        b = get_current_brightness()
    return between(1.0, b + offset, MAX_BRIGHTNESS) - b


def main():
    with running_once('auto_brightness'):
        offset = 0

        def handler(signum, frame):
            b = get_current_brightness()
            multiplier = {
                BRIGHTNESS_UP: 1 + CHANGE_PERCENTAGE,
                BRIGHTNESS_DOWN: 1 / (1 + CHANGE_PERCENTAGE)
            }[signum]

            nonlocal offset

            old_offset = offset
            offset = ((b + offset) * multiplier) - b

            if abs(offset - old_offset) < 1:
                offset = old_offset + (1 if signum == BRIGHTNESS_UP else -1)
                print("Correcting for sub-1 change")

            offset = normalize_offset(offset, b)
            set_brightness(b + offset)

        for signum in [BRIGHTNESS_UP, BRIGHTNESS_DOWN]:
            signal(signum, handler)

        signal(SIGALRM, SIG_IGN)

        t = datetime.now()
        loop_time = timedelta()
        while True:
            b = get_current_brightness()

            mult = exp(-ln(2) * loop_time / CHANGE_HALFTIME)
            offset *= mult
            offset = normalize_offset(offset, b)
            print(f"offset: {offset}")

            set_brightness(b + offset)

            with signal_interruptable():
                sleep(SLEEP_TIME)

            loop_time, t = datetime.now() - t, datetime.now()
            print(f"loop time: {loop_time}")


if __name__ == "__main__":
    print("Starting")
    main()
    print("Done")
