"""Remote presses from the kernel's IR receiver, as the config writes them.

The kernel decodes the remote itself.  Its lirc device, put in scancode
mode, hands over one record per press with the protocol it decoded, so
nothing beyond Python is needed to read one.
"""
import glob
import os
import struct

# from linux/lirc.h
LIRC_SET_REC_MODE = 0x40046912
LIRC_MODE_SCANCODE = 0x08
LIRC_SCANCODE_FLAG_REPEAT = 2

# struct lirc_scancode: timestamp, flags, rc_proto, keycode, scancode
RECORD = struct.Struct('=QHHIQ')

# enum rc_proto, by number, named the way ir-keytable names them
PROTOCOLS = [
    'unknown', 'other', 'rc5', 'rc5x_20', 'rc5_sz', 'jvc', 'sony12',
    'sony15', 'sony20', 'nec', 'necx', 'nec32', 'sanyo', 'mcir2_kbd',
    'mcir2_mse', 'rc6_0', 'rc6_6a_20', 'rc6_6a_24', 'rc6_6a_32', 'rc6_mce',
    'sharp', 'xmp', 'cec', 'imon', 'rcmm12', 'rcmm24', 'rcmm32', 'xbox_dvd',
]


def receiver(driver):
    """the receiver whose driver is this, as ('rc2', '/dev/lirc0'), or
    None"""
    for rc in sorted(glob.glob('/sys/class/rc/rc*')):
        try:
            with open(os.path.join(rc, 'uevent')) as fh:
                uevent = fh.read().split()
        except OSError:
            continue
        if 'DRV_NAME=%s' % driver not in uevent:
            continue
        for lirc in glob.glob(os.path.join(rc, 'lirc*')):
            return os.path.basename(rc), '/dev/' + os.path.basename(lirc)
    return None


def key(protocol, scancode):
    """a press as the config writes it, such as rc6_mce-0x800f0409"""
    name = (PROTOCOLS[protocol] if protocol < len(PROTOCOLS)
            else str(protocol))
    return '%s-%#x' % (name, scancode)


def presses(path):
    """each new press on the receiver, forever.

    A held button repeats, and acting on every repeat would turn the
    pages as fast as the remote sends.  Only the first of them counts.
    """
    # here rather than at the top, so the plugin still loads on Windows
    import fcntl
    with open(path, 'rb', buffering=0) as fh:
        fcntl.ioctl(fh, LIRC_SET_REC_MODE,
                    struct.pack('I', LIRC_MODE_SCANCODE))
        while True:
            data = fh.read(RECORD.size)
            if len(data) < RECORD.size:
                return
            _, flags, protocol, _, scancode = RECORD.unpack(data)
            if flags & LIRC_SCANCODE_FLAG_REPEAT:
                continue
            yield key(protocol, scancode)
