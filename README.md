# auto_brightness

Automatically manages your brightness for you, based on the location of the sun.

Requires only minimal configuration and tweaking©.

Set your location at the top of `auto_brightness.py` (`LOCATION = ephem.city('Amsterdam')`, replace with your city. If that doesn't work, try a larger city.). Let it run at login, and use `brightness_up` and `brightness_down` to update your brightness.

## Requirements:

- Python 3.6
- ephem
