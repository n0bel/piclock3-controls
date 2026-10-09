"""Push buttons on the gpio pins and an infrared remote, as actions.

Each button is one of the things a key does on the clock, called on the
clock directly rather than sent as a key press, so it works whichever
window has the focus.
"""
import logging
import threading

from PyQt5.QtCore import pyqtSignal

from PiClock3.Service import Service

from . import remote

logger = logging.getLogger(__name__)

# a button's key in the config, and what gpiozero calls the same pin
PREFIXES = {'gpio-': 'GPIO', 'pin-': 'BOARD'}


class Controls(Service):

    # the buttons and the remote call back on threads of their own, and the
    # clock is only safe to touch from Qt's.  A signal crosses between them.
    pressed = pyqtSignal(str)

    def __init__(self, piclock, name, config):
        super().__init__(piclock, name, config)
        # gpiozero releases a pin when its Button is collected
        self.buttons = []
        self.pressed.connect(self.act)

    def start(self):
        if self.config['buttons']:
            self.startButtons()
        if self.config['remote'] and self.config['remote-device']:
            self.startRemote()

    def startRemote(self):
        found = remote.receiver(self.config['remote-device'])
        if found is None:
            logger.error('%s: no IR receiver whose driver is %s, so the'
                         ' remote does nothing.  See the README',
                         self.name, self.config['remote-device'])
            return
        # what learn.py prints is lower case, and a hand-typed 0X45 is
        # the same button
        actions = {str(k).lower(): v
                   for k, v in self.config['remote'].items()}
        thread = threading.Thread(target=self.listen,
                                  args=(found[1], actions), daemon=True)
        thread.start()
        logger.info('%s: listening on %s for %s', self.name, found[1],
                    ', '.join(sorted(actions)))

    def listen(self, path, actions):
        """on a thread of its own, since a read waits for a press"""
        try:
            for key in remote.presses(path):
                if key in actions:
                    self.pressed.emit(actions[key])
                else:
                    logger.info('%s: %s is not under remote:',
                                self.name, key)
        except OSError as e:
            logger.error('%s: %s: %s', self.name, path, e)

    def startButtons(self):
        try:
            from gpiozero import Button
            from gpiozero.exc import PinInvalidPin
        except ImportError:
            logger.error('%s: gpiozero is not installed, so the buttons do'
                         ' nothing.  sudo apt install python3-gpiozero',
                         self.name)
            return
        for key, action in self.config['buttons'].items():
            pin = gpiozeroPin(str(key))
            if pin is None:
                logger.error('%s: %s is not a pin.  Write gpio-25 for'
                             ' GPIO25, or pin-22 for header pin 22',
                             self.name, key)
                continue
            try:
                button = Button(pin, pull_up=True,
                                bounce_time=self.config['bounce'] or None)
            except PinInvalidPin:
                logger.error('%s: %s is ground, power or not there, so no'
                             ' button can be wired to it', self.name, key)
                continue
            except Exception as e:
                # one something else already holds, mostly
                logger.error('%s: %s: %s', self.name, key, e)
                continue
            button.when_pressed = self.emitter(action)
            self.buttons.append(button)
            logger.info('%s: %s does %s', self.name, key, action)

    def emitter(self, action):
        # a function per button, so each sends its own action
        return lambda: self.pressed.emit(action)

    def act(self, action):
        """do one action by its name in schema.yaml"""
        clock = self.piclock
        if action == 'next-page':
            clock.nextPage(1)
        elif action == 'previous-page':
            clock.nextPage(-1)
        elif action == 'quit':
            clock.close()
        else:
            show = clock.showing()
            if show is None:
                return
            if action == 'slideshow-back':
                show.step(-1)
            elif action == 'slideshow-forward':
                show.step(1)
            elif action == 'slideshow-hold':
                show.hold()
        logger.info('%s: %s', self.name, action)


def gpiozeroPin(key):
    """gpio-25 as GPIO25 and pin-22 as BOARD22, or None"""
    for prefix, name in PREFIXES.items():
        if key.startswith(prefix) and key[len(prefix):].isdigit():
            return name + key[len(prefix):]
    return None
