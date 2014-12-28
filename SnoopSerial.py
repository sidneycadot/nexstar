#! /usr/bin/env python3

import sys, serial

def main():

    port = None

    for arg in sys.argv:
        if arg.startswith("--port="):
            port = arg[7:]

    if port is None:
        print("specify serial port using --port=<device> argument.")
        return

    snoop = serial.Serial(
            port             = port,
            baudrate         = 19200,
            bytesize         = serial.EIGHTBITS,
            parity           = serial.PARITY_NONE,
            stopbits         = serial.STOPBITS_ONE,
            timeout          = 0.01,
            xonxoff          = None,
            rtscts           = False,
            writeTimeout     = None,
            dsrdtr           = False,
            interCharTimeout = None
        )

    buf = []
    while True:
        x = snoop.read(1)
        if len(x) == 0:
            if len(buf) > 0:
                print(" ".join(["{:02x}".format(x) for x in buf]))
                buf = []
        else:
            buf.append(x[0])

if __name__ == "__main__":
    main()
