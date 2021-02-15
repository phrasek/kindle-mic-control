import math
import signal
import struct
import time

import pyaudio
from ahk import AHK
from ahk.directives import NoTrayIcon

Threshold = 15  # threshold for noise to trigger page turn

SHORT_NORMALIZE = 1.0 / 32768.0
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
swidth = 2

debounce = 0.25
left_threshold = 2.5  # a second trigger within the period left_threshold - debounce will turn the page left

kindle_path = r"path\\to\\kindle.exe"
ahk_path = r"path\\to\\autohotkey.exe"


class Listener:
    @staticmethod
    def rms(frame):
        count = len(frame) / swidth
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(self, handler):
        self.debug = False
        self.p = pyaudio.PyAudio()
        self.handler = handler
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            output=True,
            frames_per_buffer=chunk,
        )

    def listen(self):
        lasttime = time.time() - 3

        print("Listening...")
        while True:
            input = self.stream.read(chunk)
            rms_val = self.rms(input)

            if rms_val > Threshold and (lasttime - time.time()) < -left_threshold:
                self.handler("right")
                lasttime = time.time()
            elif rms_val > Threshold and (lasttime - time.time()) < -debounce:
                self.handler("left")
                self.handler("left")
                lasttime = time.time()
            elif rms_val > Threshold:
                pass


def handler(key):
    ahk = AHK(directives=[NoTrayIcon], executable_path=ahk_path)
    win = ahk.find_window(process=kindle_path)
    try:
        win.activate()
        win.to_top()
        ahk.key_press(key)
    except AttributeError:
        pass


def keyboardInterruptHandler(signal, frame):
    exit()


def main():
    signal.signal(signal.SIGINT, keyboardInterruptHandler)
    listener = Listener(handler=handler)
    listener.listen()


if __name__ == "__main__":
    main()
