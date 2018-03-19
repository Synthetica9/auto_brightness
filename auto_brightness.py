#! /usr/bin/env nix-shell
#! nix-shell -i python -p "with python3Packages; [ephem python]" xorg.xbacklight

from tools import *

import subprocess
from signal import signal, SIGUSR1, SIGUSR2, SIGALRM, SIG_IGN

from math import sin, ceil, sqrt, exp, log as ln

from datetime import timedelta, datetime

import ephem

# CONFIGURABLES
LOCATION = ephem.city('Amsterdam')
CHANGE_HALFTIME = timedelta(minutes=60)
SLEEP_TIME = timedelta(seconds=5)
CHANGE_PERCENTAGE = 10/100

BRIGHTNESS_UP = SIGUSR1
BRIGHTNESS_DOWN = SIGUSR2

MAX_OVERDRIVE_PRESSES = 1
MAX_BRIGHTNESS = 100 * (1 + CHANGE_PERCENTAGE) ** MAX_OVERDRIVE_PRESSES

DOCKED_BRIGHTNESS = 100  # Set to None to disable this feature
# END OF CONFIGURABLES


class Decaying(object):
    def __init__(self, value, half_life, start_t=None):
        self._value = value
        self.half_life = half_life
        if start_t is None:
            start_t = datetime.utcnow()
        self.start_t = start_t

    @property
    def value(self):
        Δt = datetime.utcnow() - self.start_t
        return self._value * exp(-ln(2) * (Δt / self.half_life))  # -ln(2) == ln(1/2)

    @value.setter
    def value(self, value):
        self.start_t = datetime.utcnow()
        self._value = value

    def __repr__(self):
        return f'{self.__class__.__name__}({self.value}, {self.half_life})'


class Brightness(object):
    def __init__(self, location=None, sun=None):
        if location is None:
            location = LOCATION
        self.location = location
        if sun is None:
            sun = ephem.Sun(location)
        self.sun = sun
        self.offset = Decaying(0.0, CHANGE_HALFTIME)

        self.tick()

    # See: http://www.lutron.com/TechnicalDocumentLibrary/Measured_vs_Perceived.pdf
    @property
    def perceived(self):
        return self._base + self.offset.value

    # Because otherwise we get a dependency loop with normalize_offset
    def _setPerceived(self, val, normalize=True):
        self.offset.value = val - self._base
        if normalize:
            self.normalize_offset()

    @perceived.setter
    def perceived(self, val):
        self._setPerceived(val)

    @property
    def absolute(self):
        return self.perceived ** 2

    @absolute.setter
    def absolute(self, val):
        self.perceived = sqrt(val)

    def tick(self):
        if DOCKED_BRIGHTNESS is not None and is_external_display_connected():
            self._base = 1.0

        self.location.date = ephem.now()
        self.sun.compute(self.location)  # Update attributes
        θ = self.sun.alt
        self._base = pos_sin(θ)

        self.normalize_offset()
        print(self._base, self.offset)

    def normalize_offset(self):
        self._setPerceived(between(0, self.perceived, 1), normalize=False)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.perceived})'


def get_num_displays():
    result = subprocess.check_output(["xrandr", "--listactivemonitors"])
    return result.count(b"\n") - 1


def is_external_display_connected():
    return get_num_displays() > 1


def set_brightness(x):
    power = linearScale(x.absolute, 1, MAX_BRIGHTNESS)
    print(f'setting brightness to {power}')
    subprocess.check_call(["xbacklight", "-set", str(power)])


def main():
    with running_once('auto_brightness'):
        offset = 0

        b = Brightness()

        def handler(signum, frame):
            if signum == BRIGHTNESS_UP:
                b.perceived += CHANGE_PERCENTAGE
            elif signum == BRIGHTNESS_DOWN:
                b.perceived -= CHANGE_PERCENTAGE

            set_brightness(b)

        for signum in [BRIGHTNESS_UP, BRIGHTNESS_DOWN]:
            signal(signum, handler)

        signal(SIGALRM, SIG_IGN)

        while True:
            b.tick()
            set_brightness(b)

            with signal_interruptable():
                sleep(SLEEP_TIME)


if __name__ == "__main__":
    main()
