"""Print each button of a remote as the config writes it.

    python3 plugins/Controls/learn.py

Press each button you want, then copy what it printed under remote:,
each with an action.  Ctrl+C stops it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import remote  # noqa: E402

DRIVER = 'gpio_ir_recv'


def main():
    found = remote.receiver(DRIVER)
    if found is None:
        sys.exit('No IR receiver.  Add dtoverlay=gpio-ir,gpio_pin=18 to'
                 ' config.txt and reboot - see the README.')
    rc, path = found
    print('Listening on %s.  Press the buttons on your remote, and'
          ' Ctrl+C stops.' % path)
    print('If nothing prints, turn on every protocol and try again:')
    print('    sudo ir-keytable -s %s -p all\n' % rc)
    try:
        for key in remote.presses(path):
            print(key, flush=True)
    except KeyboardInterrupt:
        print()
    except PermissionError:
        sys.exit('%s cannot be read.  It belongs to the video group:'
                 ' sudo usermod -aG video $USER, then log in again.' % path)


if __name__ == '__main__':
    main()
