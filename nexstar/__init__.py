#! /usr/bin/env python3

# This code follows the NexStar Communication Protocol as described in NexStarCommunicationProtocolV1.2.pdf
# This code is forked from https://github.com/sidneycadot/nexstar

import sys, serial, datetime, pytz, time
from enum import Enum

class NexstarUsageError(Exception):
    pass

class NexstarProtocolError(Exception):
    pass

class NexstarPassthroughError(Exception):
    pass

class NexstarModel(Enum):
    gps_series  =  1
    i_series    =  3
    i_series_se =  4
    cge         =  5
    advanced_gt =  6
    slt         =  7
    cpc         =  9
    gt          = 10
    se45        = 11
    se68        = 12
    lcm         = 15

class NexstarCommand(Enum):
    # All Nexstar commands start with a single ASCII character.
    GET_POSITION_RA_DEC           = 'E' # 1.2+
    GET_POSITION_RA_DEC_PRECISE   = 'e' # 1.6+
    GET_POSITION_AZM_ALT          = 'Z' # 1.2+
    GET_POSITION_AZM_ALT_PRECISE  = 'z' # 2.2+
    GOTO_POSITION_RA_DEC          = 'R' # 1.2+
    GOTO_POSITION_RA_DEC_PRECISE  = 'r' # 1.6+
    GOTO_POSITION_AZM_ALT         = 'B' # 1.2+
    GOTO_POSITION_AZM_ALT_PRECISE = 'b' # 2.2+
    SYNC                          = 'S' # 4.10+
    SYNC_PRECISE                  = 's' # 4.10+
    GET_TRACKING_MODE             = 't' # 2.3+
    SET_TRACKING_MODE             = 'T' # 1.6+
    GET_LOCATION                  = 'w' # 2.3+
    SET_LOCATION                  = 'W' # 2.3+
    GET_TIME                      = 'h' # 2.3+
    SET_TIME                      = 'H' # 2.3+
    GET_VERSION                   = 'V' # 1.2+
    GET_MODEL                     = 'm' # 2.2+
    ECHO                          = 'K' # 1.2+
    GET_ALIGNMENT_COMPLETE        = 'J' # 1.2+
    GET_GOTO_IN_PROGRESS          = 'L' # 1.2+
    CANCEL_GOTO                   = 'M' # 1.2+
    PASSTHROUGH                   = 'P' # 1.6+ this includes slewing commands, 'get device version' commands, GPS commands, and RTC commands

class NexstarPassthroughCommand(Enum):
    MOTOR_SLEW_POSITIVE_VARIABLE_RATE =   6
    MOTOR_SLEW_NEGATIVE_VARIABLE_RATE =   7
    MOTOR_SLEW_POSITIVE_FIXED_RATE    =  36
    MOTOR_SLEW_NEGATIVE_FIXED_RATE    =  37
    GET_DEVICE_VERSION                = 254

class NexstarCoordinateMode(Enum):
    RA_DEC  = 1 # Right Ascension / Declination
    AZM_ALT = 2 # Azimuth/Altitude

class NexstarTrackingMode(Enum):
    OFF      = 0
    ALT_AZ   = 1
    EQ_NORTH = 2
    EQ_SOUTH = 3

class NexstarDeviceId(Enum):
    AZM_RA_MOTOR  = 16
    ALT_DEC_MOTOR = 17
    GPS_DEVICE    = 176
    RTC_DEVICE    = 178 # real-time clock on the CGE mount

class NexstarHandController:

    def __init__(self, device):

        if isinstance(device, str):
            # For now, if we're passed a string, assume it's a serial device name.
            # We may add support for TCP ports later.
            device = serial.Serial(
                    port             = device,
                    baudrate         = 9600,
                    bytesize         = serial.EIGHTBITS,
                    parity           = serial.PARITY_NONE,
                    stopbits         = serial.STOPBITS_ONE,
                    timeout          = 3.500,
                    xonxoff          = None,
                    rtscts           = False,
                    writeTimeout     = None,
                    dsrdtr           = False,
                    interCharTimeout = None
                )

        self._device = device

    @property
    def device(self):
        return self._device

    def close(self):
        return self._device.close()

    def _write_binary(self, request):
        return self._device.write(request)

    @staticmethod
    def _to_bytes(arg):

        if isinstance(arg, NexstarCommand) or isinstance(arg, NexstarTrackingMode) or isinstance(arg, NexstarDeviceId) or isinstance (arg, NexstarPassthroughCommand):
           arg = arg.value

        if isinstance(arg, int):
            arg = bytes([arg])

        if isinstance(arg, str):
            arg = bytes(arg, "ascii")

        if not isinstance(arg, bytes):
            arg = b''.join(NexstarHandController._to_bytes(e) for e in arg)

        return arg

    def _write(self, *args):
        msg = NexstarHandController._to_bytes(args)
        # print("message to be written:", msg)
        return self._write_binary(msg)

    def _read_binary(self, expected_response_length, check_and_remove_trailing_hash = True):

        if not (isinstance(expected_response_length, int) and expected_response_length > 0):
            raise NexstarUsageError("_read_binary() failed: incorrect value for parameter 'expected_response_length': {}".format(repr(expected_response_length)))

        if not isinstance(check_and_remove_trailing_hash, bool):
            raise NexstarUsageError("_read_binary() failed: incorrect value for parameter 'check_and_remove_trailing_hash': {}".format(repr(check_and_remove_trailing_hash)))

        response = self._device.read(expected_response_length)

        if len(response) != expected_response_length:
            raise NexstarProtocolError("read_binary() failed: actual response length ({}) not equal to expected response length ({})".format(len(response), expected_response_length))

        if check_and_remove_trailing_hash:
            if not response.endswith(b'#'):
                raise NexstarProtocolError("read_binary() failed: response does not end with hash character (ASCII 35)")
            # remove the trailing hash character.
            response = response[:-1]

        return response

    def _read_ascii(self, expected_response_length, check_and_remove_trailing_hash = True):
        response = self._read_binary(expected_response_length, check_and_remove_trailing_hash)
        response = response.decode("ascii")
        return response

    # Public API starts here

    def getPosition(self, coordinateMode = NexstarCoordinateMode.AZM_ALT, highPrecisionFlag = True):

        if highPrecisionFlag:
            command = NexstarCommand.GET_POSITION_AZM_ALT_PRECISE if (coordinateMode == NexstarCoordinateMode.AZM_ALT) else NexstarCommand.GET_POSITION_RA_DEC_PRECISE
            expected_response_length = 8 + 1 + 8 + 1
            denominator = 0x100000000
        else:
            command = NexstarCommand.GET_POSITION_AZM_ALT if (coordinateMode == NexstarCoordinateMode.AZM_ALT) else NexstarCommand.GET_POSITION_RA_DEC
            expected_response_length = 4 + 1 + 4 + 1
            denominator = 0x10000

        self._write(command)

        response = self._read_ascii(expected_response_length = expected_response_length, check_and_remove_trailing_hash = True)
        response = response.split(",")
        if not (len(response) == 2):
            raise NexstarProtocolError("getPosition() failed: unexpected response ({})".format(response))

        response = (360.0 * int(response[0], 16) / float(denominator), 360.0 * int(response[1], 16) / float(denominator))
        return response

    def gotoPosition(self, firstCoordinate, secondCoordinate, coordinateMode = NexstarCoordinateMode.AZM_ALT, highPrecisionFlag = True):

        # Initiate a "GoTo" command.

        if highPrecisionFlag:
            command = NexstarCommand.GOTO_POSITION_AZM_ALT_PRECISE if (coordinateMode == NexstarCoordinateMode.AZM_ALT) else NexstarCommand.GOTO_POSITION_RA_DEC_PRECISE
            firstCoordinate  = round(float(firstCoordinate)  / 360.0 * 0x100000000)
            secondCoordinate = round(float(secondCoordinate) / 360.0 * 0x100000000)
            coordinates = "{:08x},{:08x}".format(firstCoordinate, secondCoordinate)
        else:
            command = NexstarCommand.GOTO_POSITION_AZM_ALT if (coordinateMode == NexstarCoordinateMode.AZM_ALT) else NexstarCommand.GOTO_POSITION_RA_DEC
            firstCoordinate  = round(float(firstCoordinate)  / 360.0 * 0x10000)
            secondCoordinate = round(float(secondCoordinate) / 360.0 * 0x10000)
            coordinates = "{:04x},{:04x}".format(firstCoordinate, secondCoordinate)

        self._write(command, coordinates)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def sync(self, firstCoordinate, secondCoordinate, highPrecisionFlag = True):

        # sync always works in RA/DEC coordinates

        if highPrecisionFlag:
            command = NexstarCommand.SYNC_PRECISE
            firstCoordinate  = round(float(firstCoordinate)  / 360.0 * 0x100000000)
            secondCoordinate = round(float(secondCoordinate) / 360.0 * 0x100000000)
            coordinates = "{}{:08x},{:08x}".format(firstCoordinate, secondCoordinate)
        else:
            command = NexstarCommand.SYNC
            firstCoordinate  = round(float(firstCoordinate)  / 360.0 * 0x10000)
            secondCoordinate = round(float(secondCoordinate) / 360.0 * 0x10000)
            coordinates = "{}{:04x},{:04x}".format(firstCoordinate, secondCoordinate)

        self._write(command, coordinates)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def getTrackingMode(self):

        command = NexstarCommand.GET_TRACKING_MODE
        self._write(command)

        response = self._read_binary(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)

        tracking_mode = response[0]

        return tracking_mode

    def setTrackingMode(self, tracking_mode):

        if not isinstance(tracking_mode, NexstarTrackingMode):
            raise NexstarUsageError("_read_binary() failed: incorrect value for parameter 'tracking_mode': {}".format(repr(tracking_mode)))

        command = NexstarCommand.GET_TRACKING_MODE

        self._write(command, tracking_mode)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def getLocation(self):

        command = NexstarCommand.GET_LOCATION
        self._write(command)

        response = self._read_binary(expected_response_length = 8 + 1, check_and_remove_trailing_hash = True)

        latitude_degrees = response[0]
        latitude_minutes = response[1]
        latitude_seconds = response[2]
        latitude_sign    = response[3] # 0 == north, 1 == south

        longitude_degrees = response[4]
        longitude_minutes = response[5]
        longitude_seconds = response[6]
        longitude_sign    = response[7] # 0 == east, 1 == west

        latitude_seconds = latitude_degrees * 3600 + latitude_minutes * 60 + latitude_seconds
        if latitude_sign != 0:
            latitude_seconds = -latitude_seconds

        longitude_seconds = longitude_degrees * 3600 + longitude_minutes * 60 + longitude_seconds
        if longitude_sign != 0:
            longitude_seconds = -longitude_seconds

        latitude = latitude_seconds / 3600.0
        longitude = longitude_seconds / 3600.0

        return (latitude, longitude)

    def setLocation(self, latitude, longitude):

        # Fix latitude

        latitude_seconds = round(latitude * 3600)
        if latitude_seconds >= 0:
            latitude_sign = 0
        else:
            latitude_sign = 1
            latitude_seconds = -latitude_seconds

        # Fix longitude

        longitude_seconds = round(longitude * 3600)
        if longitude_seconds >= 0:
            longitude_sign = 0
        else:
            longitude_sign = 1
            longitude_seconds = -longitude_seconds

        # Reduce to Degrees/Minutes/Seconds

        latitude_degrees = latitude_seconds // 3600 ; latitude_seconds %= 3600
        latitude_minutes = latitude_seconds // 60   ; latitude_seconds %= 60

        longitude_degrees = longitude_seconds // 3600 ; longitude_seconds %= 3600
        longitude_minutes = longitude_seconds // 60   ; longitude_seconds %= 60

        # Synthesize "W" request

        request = [
                NexstarCommand.SET_LOCATION,
                latitude_degrees, latitude_minutes, latitude_seconds, latitude_sign,
                longitude_degrees, longitude_minutes, longitude_seconds, longitude_sign
            ]

        self._write(request)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def getTime(self):

        request = NexstarCommand.GET_TIME
        self._write(request)

        response = self._read_binary(expected_response_length = 8 + 1, check_and_remove_trailing_hash = True)

        hour   = response[0] # 24 hour clock
        minute = response[1]
        second = response[2]
        month  = response[3] # jan == 1, dec == 12
        day    = response[4] # 1 .. 31
        year   = response[5] # year minus 2000
        zone   = response[6] # 2-complement of timezone (hour offset from UTC)
        dst    = response[7] # 1 to enable DST, 0 for standard time.

        year += 2000

        if zone >= 128: # take care of negative zone offsets
            zone -= 256

        zone = datetime.timedelta(hours = zone)

        dst = (dst != 0)

        print(year, month, day, hour, minute, second)

        tzinfo = datetime.timezone(zone) # simple timezone with offset relative to UTC
        timestamp = datetime.datetime(year, month, day, hour, minute, second, 0, tzinfo)

        return (timestamp, dst)

    def setTime(self, timestamp, dst):

        hour   = timestamp.hour
        minute = timestamp.minute
        second = timestamp.second
        month  = timestamp.month
        day    = timestamp.day
        year   = timestamp.year - 2000

        zone = round(timestamp.utcoffset() / datetime.timedelta(hours = 1))
        if zone < 0:
            zone += 256

        request = [NexStarCommand.SET_TIME, hour, minute, second, month, day, year, zone, dst]
        self._write(request)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def getVersion(self):
        request = NexstarCommand.GET_VERSION
        self._write(request)
        response = self._read_binary(expected_response_length = 2 + 1, check_and_remove_trailing_hash = True)
        response = (response[0], response[1])
        return response

    def getModel(self):
        request = NexstarCommand.GET_MODEL
        self._write(request)
        response = self._read_binary(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)
        response = response[0]
        return response

    def echo(self, c):
        if not isinstance(c, int) and (0 <= c <= 255):
            raise NexstarUsageError("echo() failed: incorrect 'c' parameter")
        request = [NexstarCommand.ECHO, c]
        self._write(request)
        response = self._read_binary(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)
        response = response[0]
        if not(response == c):
            raise NexstarProtocolError("echo() failed: unexpected response ({})".format(repr(response)))
        return None

    #def recover(self):
    #    request = [NexstarCommand.ECHO, 'S']
    #    self._write(request)
    #    response = self._read_binary(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)
    #    print("==>", request, response)

    def getAlignmentComplete(self):
        request = [NexstarCommand.GET_ALIGNMENT_COMPLETE]
        self._write(request)
        response = self._read_binary(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)
        response = response[0]
        if not response in [0, 1]:
            raise NexstarProtocolError("getAlignmentComplete() failed: unexpected response ({})".format(repr(response)))
        response = (response == 1) # convert to bool
        return response

    def getGotoInProgress(self):
        request = [NexstarCommand.GET_GOTO_IN_PROGRESS]
        self._write(request)
        response = self._read_ascii(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)
        response = response[0]
        # Response should be ASCII '0' or '1'
        if not response in ['0', '1']:
            raise NexstarProtocolError("getGotoInProgress() failed: unexpected response ({})".format(repr(response)))
        response = (response == '1') # convert to bool
        return response

    def cancelGoto(self):
        request = [NexstarCommand.CANCEL_GOTO]
        self._write(request)
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)
        return None

    # The commands below are low-level 'pass-through' commands that are handled by the specified
    # sub-devices connected to the hand controller via the 6-pin RJ-12 port.

    def passthrough(self, deviceId, command, expected_response_bytes):

        if not isinstance(deviceId, NexstarDeviceId):
            raise NexstarUsageError("getDeviceVersion() failed: incorrect value for parameter 'deviceId': {}".format(repr(deviceId)))

        if not (isinstance(expected_response_bytes, int) and expected_response_bytes >= 0):
            raise NexstarUsageError("passthrough() failed: incorrect value for parameter 'expected_response_bytes': {}".format(repr(expected_response_bytes)))

        command_bytes = NexstarHandController._to_bytes(command)

        if not (1 <= len(command_bytes) <= 4):
            raise NexstarUsageError("expected between 1 and 4 command bytes for passthrough command (received {})".format(len(command)))

        padding = bytes(4 - len(command_bytes))

        request = [NexstarCommand.PASSTHROUGH, len(command_bytes), deviceId, command_bytes, padding, expected_response_bytes]

        self._write(request)

        # Receive response.
        try:
            response = self._read_binary(expected_response_length = expected_response_bytes + 1, check_and_remove_trailing_hash = True)
        except NexstarProtocolError as exception:
            # read away extra hash
            extra_hash = self._device.read(1)
            if extra_hash != b"#":
                raise NexstarProtocolError("extra hash not found") from exception

            raise NexstarPassthroughError("No valid response from device {}".format(deviceId.name))

        return response

    def slew_fixed(self, deviceId, rate):
        if deviceId not in [NexstarDeviceId.AZM_RA_MOTOR, NexstarDeviceId.ALT_DEC_MOTOR]:
            raise NexstarUsageError("slew command only supported for motors.")
        if not (isinstance(rate, int) and -9 <= rate <= +9):
            raise NexstarUsageError("slew_fixed() failed: incorrect value for parameter 'rate': {}".format(repr(rate)))

        if rate >= 0:
            command = NexstarPassthroughCommand.MOTOR_SLEW_POSITIVE_FIXED_RATE
        else:
            command = NexstarPassthroughCommand.MOTOR_SLEW_NEGATIVE_FIXED_RATE
            rate = -rate

        self.passthrough(deviceId, [command, rate], expected_response_bytes = 0)

    def slew_variable(self, deviceId, rate):
        if deviceId not in [NexstarDeviceId.AZM_RA_MOTOR, NexstarDeviceId.ALT_DEC_MOTOR]:
            raise NexstarUsageError("slew command only supported for motors.")

        # rate is assumed to be in in degrees / second
        rate = round(rate * 3600.0 * 4)

        if rate >= 0:
            command = NexstarPassthroughCommand.MOTOR_SLEW_POSITIVE_VARIABLE_RATE
        else:
            command = NexstarPassthroughCommand.MOTOR_SLEW_NEGATIVE_VARIABLE_RATE
            rate = -rate

        if not (0 <= rate <= 65535):
            raise NexstarUsageError("variable rate out of range.")

        self.passthrough(deviceId, [command, rate // 256, rate % 256], expected_response_bytes = 0)

    def getDeviceVersion(self, deviceId):

        (versionMajor, versionMinor) = self.passthrough(deviceId, command = NexstarPassthroughCommand.GET_DEVICE_VERSION, expected_response_bytes = 2)

        return (versionMajor, versionMinor)

def status_report(controller):

    tz = pytz.timezone('Europe/Amsterdam')

    (ra, dec) = controller.getPosition(coordinateMode = NexstarCoordinateMode.RA_DEC)
    print("position RA/DEC ................... : ra = {}, dec = {}".format(ra, dec))

    (azimuth, altitude) = controller.getPosition(coordinateMode = NexstarCoordinateMode.AZM_ALT)
    print("position AZM/ALT .................. : azimuth = {}, altitude = {}".format(azimuth, altitude))

    tracking_mode = controller.getTrackingMode()
    print("tracking mode ..................... : {}".format(tracking_mode))

    (latitude, longitude) = controller.getLocation()
    print("location .......................... : latitude = {}, longitude = {}".format(latitude, longitude))

    (time, dst) = controller.getTime()
    time = time.astimezone(tz)
    print("time .............................. : time = {}, dst = {}".format(time.strftime("%Y-%m-%d %H:%M:%S %Z"), dst))

    (versionMajor, versionMinor) = controller.getVersion()
    print("version ........................... : {}.{}".format(versionMajor, versionMinor))

    model = controller.getModel()
    print("model ............................. : {}".format(model))

    alignmentComplete = controller.getAlignmentComplete()
    print("alignment complete ................ : {}".format(alignmentComplete))

    gotoInProgress = controller.getGotoInProgress()
    print("goto in progress .................. : {}".format(gotoInProgress))

    if True:
        for deviceId in NexstarDeviceId:
            try:
                (versionMajor, versionMinor) = controller.getDeviceVersion(deviceId)
                status = "version = {}.{}".format(versionMajor, versionMinor)
            except NexstarPassthroughError as exception:
                status = "error: {}".format(exception)

            print("device {} {} : {}".format(deviceId.name, "." * (27 - len(str(deviceId.name))), status))

    model = controller.getModel()
    print("model ............................. : {}".format(model))


def main():

    # Perform tests

    port = None

    for arg in sys.argv:
        if arg.startswith("--port="):
            port = arg[7:]

    if port is None:
        print("specify serial port using --port=<device> argument.")
        return

    controller = NexstarHandController(port)

    # tests

    #if True:
    #    controller.recover()

    status_report(controller)

    if True:

        controller.slew_fixed(NexstarDeviceId.AZM_RA_MOTOR, 9)
        #controller.slew(NexstarDeviceId.ALT_DEC_MOTOR, +0.001)
        time.sleep(10)
        controller.slew_fixed(NexstarDeviceId.AZM_RA_MOTOR, 0)
        pass

    if False:

        while True:

            pos = controller.getPosition()
            print(pos)

    if False:
        controller.gotoPosition(0.0, 0.0)
        gotoInProgress = True
        while gotoInProgress:
            pos = controller.getPosition()
            print(pos)
            gotoInProgress = getGotoInProgress()

    if False:

        while True:
            for deviceId in [NexstarDeviceId.AZM_RA_MOTOR, NexstarDeviceId.ALT_DEC_MOTOR]:
                try:
                    (versionMajor, versionMinor) = controller.getDeviceVersion(deviceId)
                    status = "version = {}.{}".format(versionMajor, versionMinor)
                except NexstarPassthroughError as exception:
                    status = "error: {}".format(exception)

                print("device {} {} : {}".format(deviceId.name, "." * (27 - len(str(deviceId.name))), status))

                time.sleep(1)
    if False:

        controller.setLocation(52.01, 4.355)
        loc = controller.getLocation()

    if False:

        timestamp = datetime.datetime.now(tz)
        controller.setTime(timestamp, 0)

        #(timestamp, dst) = controller.getTime()
        #timestamp = timestamp.astimezone(tz)
        #print(">>", timestamp.strftime("%Y-%m-%d %H:%M:%S.%f %Z"), dst)

    controller.close()

if __name__ == "__main__":
    main()

# Below are some low-level HC <-> MC commands:
#
# Standard boot sequence:

# 3b 03 0d 11 05 da    3b 05 11 0d 05 0f 87 42
# 3b 03 0d 10 05 db    3b 05 10 0d 05 0f 87 43
# 3b 03 0d 10 fe e2    3b 05 10 0d fe 06 0d cd
# 3b 03 0d 10 fc e4    3b 04 10 0d fc 00 e3
# 3b 03 0d 11 fc e3    3b 04 11 0d fc 01 e1

# Slew left (hand controller)
#
# 3b 04 0d 10 25 09 b1 3b 04 10 0d 25 01 b9
# 3b 04 0d 10 24 00 bb 3b 04 10 0d 24 01 ba
#
# Slew right (hand controller)
#
# 3b 04 0d 10 24 09 b2 3b 04 10 0d 24 01 ba
# 3b 04 0d 10 24 00 bb 3b 04 10 0d 24 01 ba
#
# Slew up (hand controller)
#
# 3b 04 0d 11 24 09 b1 3b 04 11 0d 24 01 b9
# 3b 04 0d 11 24 00 ba 3b 04 11 0d 24 01 b9
#
# Slew down (hand controller)
#
# 3b 04 0d 11 25 09 b0 3b 04 11 0d 25 01 b8
# 3b 04 0d 11 24 00 ba 3b 04 11 0d 24 01 b9
