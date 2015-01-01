#! /usr/bin/env python3

import math

def to_dms(x):

    if x >= 0:
        sign = 1
    else:
        sign = -1
        x = -x

    d = math.floor(x)
    x = (x - d) * 60.0
    m = math.floor(x)
    x = (x - m) * 60.0
    s = x

    if sign < 0:
        d = -d

    return (d, m, s)

def present(label, latitude, longitude):

    (latitude_d , latitude_m , latitude_s ) = to_dms(latitude)
    (longitude_d, longitude_m, longitude_s) = to_dms(longitude)

    print("[{}] latitude: {:.9f} (dms: {:+4d}°{:02d}′{:06.3f}″) longitude: {:.9f} (dms: {:+4d}°{:02d}′{:06.3f}″)".format(
            label,
        latitude, latitude_d , latitude_m , latitude_s,
        longitude, longitude_d, longitude_m, longitude_s
    ))

present("WS13", 52.010285, 4.350061)
present("BW47", 52.011308, 4.361591)
