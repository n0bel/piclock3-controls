try:
    from PiClock3 import __version__
except ImportError:
    # a PiClock3 from before it had a version
    __version__ = '0'

# the oldest PiClock3 this plugin runs on: the first with a version, and
# services: came before it.  A SystemExit with a sentence is shown as that
# sentence, where any other error is a traceback.
if __version__ < '2026.10.09':
    raise SystemExit('Controls needs PiClock3 2026.10.09 or later - '
                     'git pull in the PiClock3 folder')

from .Controls import *  # noqa: E402,F401,F403
