#! /usr/bin/env python3

# This code follows the NexStar Communication Protocol as described in
# http://www.celestron.com/c3/images/files/downloads/1154108406_nexstarcommprot.pdf

import serial, warnings, datetime, pytz, time
from enum import Enum

class NexstarUsageError(Exception):
    pass

class NexstarProtocolError(Exception):
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
    # All Nexstar commands star with a single ASCII character.
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

class NexstarCoordinateMode(Enum):
    RA_DEC  = 1 # Right Ascension / Declination
    AZM_ALT = 2 # Azimuth/Altitude

class NexstarTrackingMode(Enum):
    OFF      = 0
    ALT_AZ   = 1
    EQ_NORTH = 2
    EQ_SOUTH = 3

class NexstarSlewRateType(Enum):
    FIXED    = 1
    VARIABLE = 2

class NexstarDeviceId(Enum):
    AZM_RA_MOTOR  = 16
    ALT_DEC_MOTOR = 17
    GPS_DEVICE    = 176
    RTC_DEVICE    = 178 # real-time clock on the CGE mount

class NexstarHandController:

    def __init__(self, device):

        if isinstance(device, str):
            # For now, assume it's a serial device name.
            # Later, we will add support for TCP ports.
            device = serial.Serial(
                    port             = device,
                    baudrate         = 9600,
                    bytesize         = serial.EIGHTBITS,
                    parity           = serial.PARITY_NONE,
                    stopbits         = serial.STOPBITS_ONE,
                    timeout          = 0.050,
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

    def _write_ascii(self, request):
        assert isinstance(request, str)
        request = request.encode("ascii")
        return self._write_binary(request)

    def _read_binary(self, expected_response_length, check_and_remove_trailing_hash = True):

        if not (isinstance(expected_response_length, int) and expected_response_length > 0):
            raise NexstarUsageError("_read_binary() failed: incorrect value for parameter 'expected_response_length': {}".format(repr(expected_response_length)))

        if not isinstance(check_and_remove_trailing_hash, bool):
            raise NexstarUsageError("_read_binary() failed: incorrect value for parameter 'check_and_remove_trailing_hash': {}".format(repr(check_and_remove_trailing_hash)))

        response = self._device.read(expected_response_length)

        if len(response) != expected_response_length:
            raise NexstarProtocolError("read_binary() failed: actual response length ({}) not equal to expected response length ({})".format(len(response), expected_response_length))

        if check_and_remove_trailing_hash:
            if not (response[-1] == ord('#')): # 'hash' character
                raise NexstarProtocolError("read_binary() failed: response does not end with hash character (ASCII 35)")

            # remove the trailing hash character.
            response = response[:-1]

        return response

    def _read_ascii(self, expected_response_length, check_and_remove_trailing_hash = True):
        response = self._read_binary(expected_response_length, check_and_remove_trailing_hash)
        response = response.decode("ascii")
        return response

    def getVersion(self):
        request = "V"
        self._write_ascii(request)
        response = self._read_binary(expected_response_length = 2 + 1, check_and_remove_trailing_hash = True)
        response = (response[0], response[1])
        return response

    #def getDeviceVersion(self, deviceNr):
    #    if self._device is None:
    #        raise NexstarUsageError("device not open")
    #    assert isinstance(deviceNr, int) and (0 <= deviceNr <= 255)
    #    request = [ord("P"), 1, deviceNr, 254, 0, 0, 0, 2]
    #    request = bytes(request)
    #    self._device.write(request)
    #    response = self._device.read(3)
    #    print("==>", request, response)
    #    if not (len(response) == 3 and response[-1] == ord("#")):
    #        raise NexstarProtocolError("unexpected response")
    #    response = (response[0], response[1])
    #    return response

    def echo(self, c):
        if not isinstance(c, int) and (0 <= c <= 255):
            raise NexstarUsageError("echo() failed: incorrect 'c' parameter")
        request = [ord("K"), c]
        request = bytes(request)
        self._write_binary(request)
        response = self._read_binary(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)
        response = response[0]
        if not(response == c):
            raise NexstarProtocolError("echo() failed: unexpected response ({})".format(response))
        return None

    def getAlignmentComplete(self):
        request = "J"
        self._write_ascii(request)
        response = self._read_binary(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)
        response = response[0]
        if not response in [0, 1]:
            raise NexstarProtocolError("getAlignmentComplete() failed: unexpected response ({})".format(response))
        response = (response == 1)
        return response

    def cancelGoto(self):
        request = "M"
        self._write_ascii(request)
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)
        return None

    def getGotoInProgress(self):
        request = "L"
        self._write_ascii(request)
        response = self._read_ascii(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)
        response = response[0]
        # Response should be ASCII '0' or '1'
        if not response in ['0', '1']:
            raise NexstarProtocolError("getGotoInProgress() failed: unexpected response ({})".format(repr(response)))
        response = (response == '1') # convert to boolean
        return response

    def getModel(self):
        request = "m"
        self._write_ascii(request)
        response = self._read_binary(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)
        response = response[0]
        return response

    def getPosition(self, coordinateMode = NexstarCoordinateMode.AZM_ALT, highPrecisionFlag = True):

        if coordinateMode == NexstarCoordinateMode.RA_DEC:
            request = "e"
        elif coordinateMode == NexstarCoordinateMode.AZM_ALT:
            request = "z"
        else:
            request = None

        if highPrecisionFlag:
            request = request.lower()
            expected_response_length = 8 + 1 + 8 + 1
            denominator = 0x100000000
        else:
            request = request.upper()
            expected_response_length = 4 + 1 + 4 + 1
            denominator = 0x10000

        self._write_ascii(request)

        response = self._read_ascii(expected_response_length = expected_response_length, check_and_remove_trailing_hash = True)
        response = response.split(",")
        if not (len(response) == 2):
            raise NexstarProtocolError("getPosition() failed: unexpected response ({})".format(response))

        response = (360.0 * int(response[0], 16) / float(denominator), 360.0 * int(response[1], 16) / float(denominator))
        return response

    def gotoPosition(self, firstCoordinate, secondCoordinate, coordinateMode = NexstarCoordinateMode.AZM_ALT, highPrecisionFlag = True):

        # Initiate a "GoTo" command.

        if coordinateMode == NexstarCoordinateMode.RA_DEC:
            request = "r"
        elif coordinateMode == NexstarCoordinateMode.AZM_ALT:
            request = "b"
        else:
            request = None

        if highPrecisionFlag:
            request = request.lower()
            firstCoordinate  = round(firstCoordinate  / 360.0 * 0x100000000)
            secondCoordinate = round(secondCoordinate / 360.0 * 0x100000000)
            request = "{}{:08x},{:08x}".format(request, firstCoordinate, secondCoordinate)
        else:
            request = request.upper()
            firstCoordinate  = round(firstCoordinate  / 360.0 * 0x10000)
            secondCoordinate = round(secondCoordinate / 360.0 * 0x10000)
            request = "{}{:04x},{:04x}".format(request, firstCoordinate, secondCoordinate)

        self._write_ascii(request)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def sync(self, firstCoordinate, secondCoordinate, highPrecisionFlag = True):

        # sync always works in RA/DEC coordinates

        request = "S"

        if highPrecisionFlag:
            request = request.lower()
            firstCoordinate  = round(firstCoordinate  / 360.0 * 0x100000000)
            secondCoordinate = round(secondCoordinate / 360.0 * 0x100000000)
            request = "{}{:08x},{:08x}".format(request, firstCoordinate, secondCoordinate)
        else:
            request = request.upper()
            firstCoordinate  = round(firstCoordinate  / 360.0 * 0x10000)
            secondCoordinate = round(secondCoordinate / 360.0 * 0x10000)
            request = "{}{:04x},{:04x}".format(request, firstCoordinate, secondCoordinate)

        self._write_ascii(request)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def getTrackingMode(self):

        request = "t"
        self._write_ascii(request)

        response = self._read_binary(expected_response_length = 1 + 1, check_and_remove_trailing_hash = True)

        tracking_mode = response[0]

        return tracking_mode

    def setTrackingMode(self, tracking_mode):

        # Synthesize "T" request

        request = [ord("T"), tracking_mode]
        request = bytes(request)

        self._write_binary(request)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def slew(self, device, rateMode, rate):
        assert device in [NexstarDeviceId.AZM_RA_MOTOR, NexstarDeviceId.ALT_DEC_MOTOR]
        if rateMode == NexstarSlewRateType.FIXED:
            if rate >= 0:
                sign = 36
            else:
                sign = 37
                rate = -rate
            request = [ord("P"), 2, device.value, sign, rate, 0, 0, 0]
        elif rateMode == NexstarSlewRateType.VARIABLE:
            # rate is assumed to be in in degrees / second
            rate = round(rate * 3600.0 * 4)
            if rate >= 0:
                sign = 6
            else:
                sign = 7
                rate = -rate
            request = [ord("P"), 3, device.value, sign, rate // 256, rate % 256, 0, 0]

        request = bytes(request)

        self._write_binary(request)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def getLocation(self):

        request = "w"
        self._write_ascii(request)

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
                ord("W"),
                latitude_degrees, latitude_minutes, latitude_seconds, latitude_sign,
                longitude_degrees, longitude_minutes, longitude_seconds, longitude_sign
            ]

        request = bytes(request)

        self._write_binary(request)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

    def getTime(self):

        request = "h"
        self._write_ascii(request)

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

        tzinfo = datetime.timezone(zone) # simple timezone with offset relative to UTC
        timestamp = datetime.datetime(year, month, day, hour, minute, second, 0, tzinfo)

        return (timestamp, dst)

    def setTime(self, timestamp, dst):

        # Synthesize "H" request.

        hour   = timestamp.hour
        minute = timestamp.minute
        second = timestamp.second
        month  = timestamp.month
        day    = timestamp.day
        year   = timestamp.year - 2000

        zone = round(timestamp.utcoffset() / datetime.timedelta(hours = 1))
        if zone < 0:
            zone += 256

        request = [ord("H"), hour, minute, second, month, day, year, zone, dst]
        request = bytes(request)
        self._write_binary(request)

        # Response is a single hash ('#') character. Drop it.
        response = self._read_binary(expected_response_length = 0 + 1, check_and_remove_trailing_hash = True)

        return None

def main():

    # Perform tests

    port = "/dev/ttyS3"

    controller = NexstarHandController(port)

    # tests

    tz = pytz.timezone('Europe/Amsterdam')

    version = controller.getVersion()
    print("version ............ : {}.{}".format(version[0], version[1]))

    model = controller.getModel()
    print("model .............. : {}".format(model))

    tracking_mode = controller.getTrackingMode()
    print("tracking mode ...... : ", tracking_mode)

    pos = controller.getPosition()
    print(pos)

    if True:
        controller.slew(NexstarDeviceId.AZM_RA_MOTOR, NexstarSlewRateType.VARIABLE, -0.1)
        controller.slew(NexstarDeviceId.ALT_DEC_MOTOR, NexstarSlewRateType.VARIABLE, +0.1)
        time.sleep(60)
        controller.slew(NexstarDeviceId.AZM_RA_MOTOR, NexstarSlewRateType.FIXED, 0)

    if False:

        controller.gotoPosition(180, 0)

        gotoInProgress = True
        while gotoInProgress:

            pos = controller.getPosition()
            print(pos)

            gotoInProgress = controller.getGotoInProgress()

    if False:

        controller.setLocation(52.5, 4.5)

        loc = controller.getLocation()
        print(loc)

    if False:
        timestamp = datetime.datetime.now(tz)
        controller.setTime(timestamp, 0)

        (timestamp, dst) = controller.getTime()
        #timestamp = timestamp.astimezone(tz)
        print(">>", timestamp.strftime("%Y-%m-%d %H:%M:%S.%f %Z"), dst)

    controller.close()

if __name__ == "__main__":
    main()
