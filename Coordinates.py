#! /usr/bin/env python3

import math

def to_dms(x):

    sign = (x > 0) - (x < 0) # Python lacks a sign() function.

    x *= sign # make sure that x is non-negative

    d = math.floor(x)
    x = (x - d) * 60.0
    m = math.floor(x)
    x = (x - m) * 60.0
    s = x

    d *= sign # correct sign of the result

    return (d, m, s)

def show_coordinates(label, lat, lon):

    (lat_d, lat_m, lat_s) = to_dms(lat)
    (lon_d, lon_m, lon_s) = to_dms(lon)

    print("[{}] latitude: {:.9f} (dms: {:+4d}°{:02d}′{:06.3f}″) longitude: {:.9f} (dms: {:+4d}°{:02d}′{:06.3f}″)".format(
            label,
            lat, lat_d, lat_m, lat_s,
            lon, lon_d, lon_m, lon_s
        ))

if __name__ == "__main__":
    show_coordinates("WS13", 52.010285, 4.350061)
    show_coordinates("BW47", 52.011310, 4.361599)
