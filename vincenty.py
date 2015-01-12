
from math import radians as degrees_to_radians, degrees as radians_to_degrees, sin, cos, tan, atan, atan2, sqrt, acos

def lookup_ellipsoid_parameters(ellipsoid):

    # parameters 'a' and 'f' of different ellipsoids
    ellipsoids = {
        "wgs84"         : (6378137.0, 1000000000.0 / 298257223563.0),
        "bessel"        : (6377397.155, 10000000.0 /   2991528128.0),
        "international" : (6378388.000,        1.0 /          297.0)
    }

    return ellipsoids[ellipsoid]

def normalize_degrees_signed(angle):
    while (angle < -180.0):
        angle += 360.0
    while (angle >= 180.0):
        angle -= 360.0
    return angle

def normalize_degrees_unsigned(angle):
    while (angle < 0.0):
        angle += 360.0
    while (angle >= 360.0):
        angle -= 360.0
    return angle

def square(x):
    return x * x

#def coord(degs, mins, secs)
#    return degs + mins / 60.0 + secs / 3600.0

#void print_dms(double dms)
#{
#    double value = dms;
#
#    bool negative = (value < 0.0);
#
#    if (negative)
#    {
#        value = -value;
#    }
#
#    double deg = floor(value);
#    value -= deg;
#    value *= 60.0;
#    double min = floor(value);
#    value -= min;
#    value *= 60.0;
#    double sec = value;
#
#    printf("%c %3.0f deg %02.0f min %20.17f sec [%+22.17f deg]", (negative ? '-' : '+'), deg, min, sec, dms)
#}

def vincenty_direct(latitude_departure_deg, longitude_departure_deg, azimuth_departure_deg, distance_meters, ellipsoid = "wgs84", ITERATION_LIMIT = 20, TOLERANCE = 1e-12):

    # lookup ellipsoid parameters

    (a, f) = lookup_ellipsoid_parameters(ellipsoid)

    # massage the input parameters

    phi1   = degrees_to_radians(latitude_departure_deg)
    alpha1 = degrees_to_radians(azimuth_departure_deg)
    s      = distance_meters

    # ellipsoid parameters

    b = (1 - f) * a

    # prepare iterations

    tan_U1 = (1 - f) * tan(phi1)
    U1 = atan(tan_U1)

    sigma1            = atan2(tan_U1, cos(alpha1))
    sin_alpha         = cos(U1) * sin(alpha1)
    cos_alpha_squared = 1.0 - square(sin_alpha)

    u_squared = cos_alpha_squared * (square(a) - square(b)) / square(b)

    A = 1.0 + u_squared/16384.0 * (4096.0 + u_squared * (-768.0 + u_squared * (320.0 - 175.0 * u_squared)))
    B =       u_squared/ 1024.0 * ( 256.0 + u_squared * (-128.0 + u_squared * ( 74.0 -  47.0 * u_squared)))

    # iterate until sigma is stable

    sigma = s/(b*A) # initial guess

    for iteration in range(ITERATION_LIMIT):

        cos_two_sigma_m = cos(2.0 * sigma1 + sigma)
        delta_sigma = B * sin(sigma) * (cos_two_sigma_m + 1.0/4.0 * B * ( cos(sigma) * (-1.0 + 2.0 * square(cos_two_sigma_m))
          - 1.0/6.0 * B * cos_two_sigma_m * (-3.0 + 4.0 * square(sin(sigma))) * (-3.0 + 4.0 * square(cos_two_sigma_m))))

        old_sigma = sigma
        sigma = s/(b*A) + delta_sigma

        if (abs(sigma - old_sigma) < TOLERANCE):
            break

    else:
        raise Exception("vincenty_direct failed to converge")

    # done iterating; calculate where we are

    phi2 = atan2(
               sin(U1) * cos(sigma) + cos(U1) * sin(sigma) * cos(alpha1),
               (1.0-f)*sqrt(square(sin_alpha)+square(sin(U1)*sin(sigma)-cos(U1)*cos(sigma)*cos(alpha1)))
           )

    lambda_ = atan2(sin(sigma)*sin(alpha1), cos(U1)*cos(sigma) - sin(U1)*sin(sigma)*cos(alpha1))

    C = f / 16.0 * cos_alpha_squared * (4.0 + f * (4.0 - 3.0 * cos_alpha_squared))

    L = lambda_ - (1.0 - C) * f * sin_alpha * (sigma + C * sin(sigma) * (cos_two_sigma_m + C * cos(sigma) * (-1.0 + 2.0 * square(cos_two_sigma_m))))

    alpha2 = atan2(sin_alpha, -sin(U1) * sin(sigma) + cos(U1) * cos(sigma) * cos(alpha1))

    # massage output

    latitude_arrival_deg  = radians_to_degrees(phi2)
    longitude_arrival_deg = normalize_degrees_unsigned(longitude_departure_deg + radians_to_degrees(L))
    azimuth_arrival_deg   = normalize_degrees_unsigned(radians_to_degrees(alpha2))

    return (latitude_arrival_deg, longitude_arrival_deg, azimuth_arrival_deg)

def vincenty_inverse(latitude_departure_deg, longitude_departure_deg, latitude_arrival_deg, longitude_arrival_deg, ellipsoid = "wgs84", ITERATION_LIMIT = 20, TOLERANCE = 1e-12):

    # lookup ellipsoid parameters

    (a, f) = lookup_ellipsoid_parameters(ellipsoid)

    # massage the input parameters

    phi1 = degrees_to_radians(latitude_departure_deg)
    phi2 = degrees_to_radians(latitude_arrival_deg)

    L = degrees_to_radians(longitude_arrival_deg - longitude_departure_deg)

    # ellipsoid parameters

    b = (1.0-f) * a

    # prepare iterations

    tan_U1 = (1.0-f) * tan(phi1)
    U1 = atan(tan_U1)

    tan_U2 = (1.0-f) * tan(phi2)
    U2 = atan(tan_U2)

    # iterate until lambda is stable

    lambda_ = L # initial guess

    for iteration in range(ITERATION_LIMIT):
        sin_sigma_squared = square(cos(U2) * sin(lambda_)) + square(cos(U1)*sin(U2) - sin(U1)*cos(U2)*cos(lambda_))

        sin_sigma = sqrt(sin_sigma_squared)
        cos_sigma = sin(U1) * sin(U2) + cos(U1) * cos(U2) * cos(lambda_)

        sigma = acos(cos_sigma)

        sin_alpha = cos(U1) * cos(U2) * sin(lambda_) / sin_sigma

        cos_alpha_squared = 1.0 - square(sin_alpha)

        cos_two_sigma_m = cos_sigma - 2.0 * sin(U1) * sin(U2) / cos_alpha_squared

        C = f / 16.0 * cos_alpha_squared * (4.0 + f * (4.0 - 3.0 * cos_alpha_squared))

        old_lambda = lambda_

        lambda_ = L + (1.0 - C) * f * sin_alpha * (sigma + C * sin_sigma * (cos_two_sigma_m + C * cos_sigma * (-1.0 + 2.0 * square(cos_two_sigma_m))))

        if (abs(lambda_ - old_lambda) < TOLERANCE):
            break
    else:
        raise Exception("vincenty_indirect failed to converge")

    u_squared = cos_alpha_squared * (square(a) - square(b)) / square(b)

    A = 1.0 + u_squared/16384.0 * (4096.0 + u_squared * (-768.0 + u_squared * (320.0 - 175.0 * u_squared)))
    B =       u_squared/ 1024.0 * ( 256.0 + u_squared * (-128.0 + u_squared * ( 74.0 -  47.0 * u_squared)))

    delta_sigma = B * sin_sigma * (cos_two_sigma_m + 1.0/4.0 * B * ( cos_sigma * (-1.0 + 2.0 * square(cos_two_sigma_m))
             - 1.0/6.0 * B * cos_two_sigma_m * (-3.0 + 4.0 * sin_sigma_squared)       * (-3.0 + 4.0 * square(cos_two_sigma_m))))

    s = b * A * (sigma - delta_sigma)

    alpha1 = atan2(cos(U2) * sin(lambda_),   cos(U1) * sin(U2) - sin(U1) * cos(U2) * cos(lambda_))
    alpha2 = atan2(cos(U1) * sin(lambda_), - sin(U1) * cos(U2) + cos(U1) * sin(U2) * cos(lambda_))

    # massage output

    distance_meters = s
    azimuth_departure_deg = normalize_degrees_unsigned(radians_to_degrees(alpha1))
    azimuth_arrival_deg = normalize_degrees_unsigned(radians_to_degrees(alpha2))

    return(distance_meters, azimuth_departure_deg, azimuth_arrival_deg)

if __name__ == "__main__":
    forward = vincenty_direct(52.0, 4.0, 17.0, 100000.0)
    print(forward)

    inverse = vincenty_inverse(52.0, 4.0, forward[0], forward[1])
    print(inverse)
