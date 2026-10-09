# piclock3-controls

Push buttons and an infrared remote for a
[PiClock3](https://github.com/n0bel/PiClock3), for a clock on a wall with
no keyboard in front of it.  Each button does one of the things a key does
on the clock: turn the page, turn it back, quit, or step or hold the
slideshow.

Which pin or which remote button does what is written in the clock's
config, and nothing has to be compiled.  It's
[issue #43](https://github.com/n0bel/PiClock3/issues/43) of PiClock3.

Both work, on a Pi 4 with Raspberry Pi OS Bookworm.  The buttons were
tested with a wire to ground in place of a button.

## What a button can do

| action | the key it matches |
|---|---|
| `next-page` | Space |
| `previous-page` | none |
| `quit` | F4 |
| `slideshow-back` | F6 |
| `slideshow-forward` | F7 |
| `slideshow-hold` | F8 |

The slideshow ones act on the slideshow of the page being looked at, the
way the keys do.  An action is a call on the clock rather than a key
press, so it works whichever window has the focus.

## Wiring

**Buttons.**  These are the pins PiClock v1 used.  Each button connects
its gpio pin to ground when pressed.  No resistor: the pin's own pull-up
holds it high the rest of the time.

    gpio     header pin   in the example
    GPIO23   16           next-page
    GPIO24   18           previous-page
    GPIO25   22           slideshow-hold
    ground   20           shared by all three

A header pin that isn't a gpio, such as `pin-25`, which is ground, is
refused, and the log says which one.

**An infrared receiver,** a TSOP4838 or one like it.  Facing its dome, its
legs are output, ground and power, left to right:

    TSOP4838         Pi header
    right, power     pin 1, 3.3V
    middle, ground   pin 9, ground
    left, output     pin 12, GPIO18

GPIO18 is where the kernel's receiver listens unless told otherwise.  Any
gpio works, named in the `dtoverlay=` line below.

## Installing

Needs a PiClock3 that knows `services:`, from October 2026 on.  Then, on
the Pi:

```
cd ~/PiClock3
git clone https://github.com/n0bel/piclock3-controls plugins/Controls
sudo apt install python3-gpiozero ir-keytable
```

gpiozero comes with Raspberry Pi OS, so apt usually has nothing to do for
it.  The remote also needs the kernel's receiver turned on, with a line in
`/boot/firmware/config.txt` (`/boot/config.txt` on Bullseye), and a
reboot:

```
dtoverlay=gpio-ir,gpio_pin=18
```

The kernel decodes the remote itself, so lirc isn't needed.

**Finding your remote's buttons.**  Run `learn.py` and press each button
you want.  It prints each one the way `remote:` writes it:

```
cd ~/PiClock3
python3 plugins/Controls/learn.py
```

    rc6_mce-0x800f0422
    rc6_mce-0x800f040e

Ctrl+C stops it.  A running clock does the same for any button its config
doesn't name, in its log: `controls: rc6_mce-0x800f0421 is not under
remote:`.

If nothing prints, the kernel isn't decoding that remote's protocol.  At
boot it decodes only rc-6, the protocol of a Windows Media Center remote.
This turns on the rest, until the next reboot, and `learn.py` prints the
command for your receiver:

```
sudo ir-keytable -s rc2 -p all
```

Once `learn.py` has shown your remote's protocol, the start of each line,
turn on just that one.  With every protocol on, some read stray noise as a
button, and the log fills with buttons nobody pressed:

```
sudo ir-keytable -s rc2 -p nec
```

`ir-keytable -s rc2` lists the names `-p` takes, which differ a little
from what `learn.py` prints: `rc6_mce` is `rc-6`, and `rc5` is `rc-5`.

Planned: keeping the protocol on across a reboot.

## Naming it in a config

It's a service: it draws nothing, so it goes under `services:` and takes no
region.

```yaml
services:
  controls:
    plugin: plugins.Controls
    buttons:
      gpio-23: next-page
      gpio-24: previous-page
      gpio-25: slideshow-hold
    remote:
      rc6_mce-0x800f0422: next-page
      rc6_mce-0x800f040e: previous-page
```

| setting | |
|---|---|
| `buttons` | a pin, as `gpio-25` for GPIO25 or `pin-22` for header pin 22, which is the same one, and what each does |
| `remote` | a button as `learn.py` prints it, and what it does |
| `remote-device` | the driver of the IR receiver.  `gpio_ir_recv` is the one the overlay above makes |
| `bounce` | seconds a button is ignored after a press, 0.05 |

`examples/controls.yaml` is a clock of two pages with these in it.

## Without this plugin

The kernel can turn a button into a key press with no plugin at all, which
is what v1's `gpio-keys` program did.  One line per button in
`config.txt`, and a reboot:

```
dtoverlay=gpio-key,gpio=23,keycode=57,label="next page"
dtoverlay=gpio-key,gpio=24,keycode=64,label="slideshow back"
dtoverlay=gpio-key,gpio=25,keycode=66,label="slideshow hold"
```

The keycodes are Linux's: 57 is Space, 62 F4, 64 F6, 65 F7 and 66 F8.  A
key press reaches the clock the way a keyboard's does.  No key turns a page
back, and what each button does lives in `config.txt` rather than the
clock's config, where `--check` can't see it.

## License

MIT, the same as PiClock3.
