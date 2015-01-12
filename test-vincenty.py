#! /usr/bin/env python3

import sys, math
from vincenty import vincenty_direct, vincenty_inverse

#const double THRESHOLD_ANGLE = 1e-6;
#const double THRESHOLD_DIST  = 1e-3;

def coord(degs, mins, secs):
    sign = (degs > 0) - (degs < 0)
    degs *= sign
    x = degs + mins / 60.0 + secs / 3600.0
    x *= sign
    return x

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

def dms_string(x):
    (d, m, s) = to_dms(x)
    return "{:+4d}°{:02d}′{:08.5f}″".format(d, m, s)

def test_paper():

    # Case (a) direct

    phi1      = coord(55.0, 45.0, 0.00000)
    alpha1    = coord(96.0, 36.0, 8.79960)
    s         = 14110526.170
    ellipsoid = "bessel"

    (phi2, L, alpha2) = vincenty_direct(phi1, 0.0, alpha1, s, ellipsoid)

    print("Case (a) direct:")
    print()
    print("    phi2 ......... : {}".format(dms_string(phi2)))
    print("    L ............ : {}".format(dms_string(L)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print()

    # Case (b) direct

    phi1      = coord(37.0, 19.0, 54.95367)
    alpha1    = coord(95.0, 27.0, 59.63089)
    s         = 4085966.703
    ellipsoid = "international"

    (phi2, L, alpha2) = vincenty_direct(phi1, 0.0, alpha1, s, ellipsoid)

    print("Case (b) direct:")
    print()
    print("    phi2 ......... : {}".format(dms_string(phi2)))
    print("    L ............ : {}".format(dms_string(L)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print()

    # Case (c) direct

    phi1      = coord(35.0, 16.0, 11.24862)
    alpha1    = coord(15.0, 44.0, 23.74850)
    s         = 8084823.839
    ellipsoid = "international"

    (phi2, L, alpha2) = vincenty_direct(phi1, 0.0, alpha1, s, ellipsoid)

    print("Case (c) direct:")
    print()
    print("    phi2 ......... : {}".format(dms_string(phi2)))
    print("    L ............ : {}".format(dms_string(L)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print()

    # Case (d) direct

    phi1      = coord( 1.0, 0.0, 0.00000)
    alpha1    = coord(89.0, 0.0, 0.00000)
    s         = 19960000.000
    ellipsoid = "international"

    (phi2, L, alpha2) = vincenty_direct(phi1, 0.0, alpha1, s, ellipsoid)

    print("Case (d) direct:")
    print()
    print("    phi2 ......... : {}".format(dms_string(phi2)))
    print("    L ............ : {}".format(dms_string(L)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print()

    # Case (e) direct

    phi1      = coord( 1.0,  0.0,  0.00000)
    alpha1    = coord( 4.0, 59.0, 59.99995)
    s         = 19780006.558
    ellipsoid = "international"

    (phi2, L, alpha2) = vincenty_direct(phi1, 0.0, alpha1, s, ellipsoid)

    print("Case (e) direct:")
    print()
    print("    phi2 ......... : {}".format(dms_string(phi2)))
    print("    L ............ : {}".format(dms_string(L)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print()

    # Case (a) inverse

    phi1      =  coord( 55.0, 45.0, 0.00000)
    phi2      = -coord( 33.0, 26.0, 0.00000)
    L         =  coord(108.0, 13.0, 0.00000)
    ellipsoid = "bessel"

    (s, alpha1, alpha2) = vincenty_inverse(phi1, 0.0, phi2, L, ellipsoid)

    print("Case (a) inverse:")
    print()
    print("    alpha1 ....... : {}".format(dms_string(alpha1)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print("    s ............ : {:10.3f} meters".format(s))
    print()

    # Case (b) inverse

    phi1      =  coord( 37.0, 19.0, 54.95367)
    phi2      =  coord( 26.0,  7.0, 42.83946)
    L         =  coord( 41.0, 28.0, 35.50729)
    ellipsoid = "international"

    (s, alpha1, alpha2) = vincenty_inverse(phi1, 0.0, phi2, L, ellipsoid)

    print("Case (b) inverse:")
    print()
    print("    alpha1 ....... : {}".format(dms_string(alpha1)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print("    s ............ : {:10.3f} meters".format(s))
    print()

    # Case (c) inverse

    phi1   =  coord( 35.0, 16.0, 11.24862)
    phi2   =  coord( 67.0, 22.0, 14.77638)
    L      =  coord(137.0, 47.0, 28.31435)
    ellipsoid = "international"

    (s, alpha1, alpha2) = vincenty_inverse(phi1, 0.0, phi2, L, ellipsoid)

    print("Case (c) inverse:")
    print()
    print("    alpha1 ....... : {}".format(dms_string(alpha1)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print("    s ............ : {:10.3f} meters".format(s))
    print()

    return # TODO: fix cases below

    # Case (d) inverse

    phi1      =  coord(  1.0,  0.0,  0.00000)
    phi2      = -coord(  0.0, 59.0, 53.83076)
    L         =  coord(179.0, 17.0, 48.02997)
    ellipsoid = "international"

    (s, alpha1, alpha2) = vincenty_inverse(phi1, 0.0, phi2, L, ellipsoid)

    print("Case (d) inverse:")
    print()
    print("    alpha1 ....... : {}".format(dms_string(alpha1)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print("    s ............ : {:10.3f} meters".format(s))
    print()

    # Case (e) inverse

    phi1   =  coord(  1.0,  0.0,  0.00000)
    phi2   =  coord(  1.0,  1.0, 15.18952)
    L      =  coord(179.0, 46.0, 17.84244)
    ellipsoid = "international"

    (s, alpha1, alpha2) = vincenty_inverse(phi1, 0.0, phi2, L, ellipsoid)

    print("Case (e) inverse:")
    print()
    print("    alpha1 ....... : {}".format(dms_string(alpha1)))
    print("    alpha2 ....... : {}".format(dms_string(alpha2)))
    print("    s ............ : {:10.3f} meters".format(s))
    print()

#void test1p(double lat1, double lon1)
#{
#    double s_arr[] = {
#        //1.0e-6,
#        // 1.0e-3,
#        1.0e+2,
#        1.0e+3,
#        1.0e+6,
#       19.8e+6
#    };

#    for(int si=0; si < (int)(sizeof(s_arr)/sizeof(double));++si)
#    {
#        for(double alpha1 = 0.0; alpha1 < 360.0; alpha1 += 15.0)
#        {
#            double s = s_arr[si];
#            double lat2, lon2, alpha2;

#            printf("TEST CASE (SINGLE-POINT SOURCE):\n\n");
#            printf("    lat1 ............. : "); print_dms(lat1);   printf("\n");
#            printf("    lon1 ............. : "); print_dms(lon1);   printf("\n");
#            printf("    alpha1 ........... : "); print_dms(alpha1); printf("\n\n");
#            printf("    s ................ : "); printf("%.9f [m]\n\n", s);

#            int vincenty_result = vincenty_direct(lat1, lon1, alpha1, s, &lat2, &lon2, &alpha2);
#            assert(vincenty_result == 0);

#            printf("    CALCULATED FORWARD DIRECT:\n\n");
#            printf("        lat2 ............. : "); print_dms(lat2);   printf("\n");
#            printf("        lon2 ............. : "); print_dms(lon2);   printf("\n");
#            printf("        alpha2 ........... : "); print_dms(alpha2); printf("\n\n");

#            double s_verify, alpha1_verify, alpha2_verify;

#            // verify FORWARD

#            if ((fabs(lat1)<1.0e-9) && (fabs(lat2)<1.0e-9))
#            {
#                printf("    NOTE: skipping co-equatorial inverses.\n\n");
#            }
#            else
#            {
#                vincenty_result = vincenty_inverse(lat1, lon1, lat2, lon2, &s_verify, &alpha1_verify, &alpha2_verify);
#                if (vincenty_result != 0)
#                {
#                    printf("    !!! UNABLE TO DO FORWARD INVERSE!\n\n");
#                }
#                else
#                {
#                    printf("    CALCULATED FORWARD INVERSE:\n\n");
#                    printf("        distance ......... : %.9f\n", s_verify);
#                    printf("        alpha1 ........... : "); print_dms(alpha1_verify); printf("\n");
#                    printf("        alpha2 ........... : "); print_dms(alpha2_verify); printf("\n\n");

#                    double err_s      = s_verify - s;
#                    double err_alpha1 = normalize_degrees_signed(alpha1_verify - alpha1);
#                   double err_alpha2 = normalize_degrees_signed(alpha2_verify - alpha2);

#                    if (fabs(err_s)>=THRESHOLD_DIST || fabs(err_alpha1)>=THRESHOLD_ANGLE || fabs(err_alpha2)>=THRESHOLD_ANGLE)
#                    {
#                       printf("    !!! SIGNIFICANT DEVIATION: err_s %g err_alpha1 %g err_alpha2 %g\n\n",
#                           err_s, err_alpha1, err_alpha2);
#                    }
#                }

#                // verify BACKWARD

#               vincenty_result = vincenty_inverse(lat2, lon2, lat1, lon1, &s_verify, &alpha1_verify, &alpha2_verify);
#               if (vincenty_result != 0)
#               {
#                   printf("    !!! UNABLE TO DO BACKWARD INVERSE!\n\n");
#               }
#               else
#               {
#                   alpha1_verify = normalize_degrees_unsigned(alpha1_verify+180.0);
#                   alpha2_verify = normalize_degrees_unsigned(alpha2_verify+180.0);

#                    printf("    CALCULATED BACKWARD INVERSE:\n\n");
#                    printf("        distance ......... : %.9f\n", s_verify);
#                    printf("        alpha1 ........... : "); print_dms(alpha1_verify); printf("\n");
#                    printf("        alpha2 ........... : "); print_dms(alpha2_verify); printf("\n");
#                    printf("\n");

#                    double err_s      = s_verify - s;
#                    double err_alpha1 = normalize_degrees_signed(alpha1_verify - alpha2);
#                    double err_alpha2 = normalize_degrees_signed(alpha2_verify - alpha1);

#                    if (fabs(err_s)>=THRESHOLD_DIST || fabs(err_alpha1)>=THRESHOLD_ANGLE || fabs(err_alpha2)>=THRESHOLD_ANGLE)
#                    {
#                        printf("    !!! SIGNIFICANT DEVIATION: err_s %g err_alpha1 %g err_alpha2 %g\n\n",
#                            err_s, err_alpha1, err_alpha2);
#                    }
#                }
#            } // not co-equatorial

#        } // alpha1 loop
#    } // distance loop
#}

#void test2p(double lat1, double lon1, double lat2, double lon2)
#{
    #printf("TEST CASE (POINT-TO-POINT):\n\n");
    #printf("    lat1 ............. : "); print_dms(lat1);   printf("\n");
    #printf("    lon1 ............. : "); print_dms(lon1);   printf("\n");
    #printf("    lat2 ............. : "); print_dms(lat2);   printf("\n");
    #printf("    lon2 ............. : "); print_dms(lon2);   printf("\n\n");

    #if ((lat1==lat2) && fmod(lon1-lon2, 360.0)==0.0)
    #{
        #printf("    !!! SKIPPING (cannot take INVERSE of IDENTICAL points)\n\n");
        #return; // skip identical points
    #}

    #if ((lat1==-lat2) && fmod(lon1 - lon2 + 180.0, 360.0)==0.0)
    #{
        #printf("    !!! SKIPPING (cannot take INVERSE of ANTIPODAL points)\n\n");
        #return; // skip antipodal points
    #}

    #if ((lat1 == 0.0) && (lat2 == 0.0))
    #{
        #printf("    !!! SKIPPING (cannot take INVERSE of EQUATORIAL points)\n\n");
        #return; // skip if points are both on the equator
    #}

    #double s, alpha1, alpha2;

    #int vincenty_result = vincenty_inverse(lat1, lon1, lat2, lon2, &s, &alpha1, &alpha2);

    #if (vincenty_result == 0)
    #{
        #printf("    !!! UNABLE TO DO INVERSE\n\n");
        #return;
    #}
    #else
    #{
        #printf("    CALCULATED INVERSE:\n\n");
        #printf("        distance ......... : %.9f\n", s);
        #printf("        alpha1 ........... : "); print_dms(alpha1); printf("\n");
        #printf("        alpha2 ........... : "); print_dms(alpha2); printf("\n\n");

        #double lat2_verify, lon2_verify, alpha2_verify;

        #vincenty_result = vincenty_direct(lat1, lon1, alpha1, s, &lat2_verify, &lon2_verify, &alpha2_verify);
        #if (vincenty_result != 0)
        #{
            #printf("    !!! UNABLE TO DO FORWARD DIRECT!\n\n");
        #}
        #else
        #{
            #printf("    CALCULATED FORWARD DIRECT:\n\n");
            #printf("        lat2 ............. : "); print_dms(lat2_verify);   printf("\n");
            #printf("        lon2 ............. : "); print_dms(lon2_verify);   printf("\n");
            #printf("        alpha2 ........... : "); print_dms(alpha2_verify); printf("\n\n");

            #double err_lat2   = normalize_degrees_signed(lat2_verify   - lat2  );
            #double err_lon2   = normalize_degrees_signed(lon2_verify   - lon2  );
            #double err_alpha2 = normalize_degrees_signed(alpha2_verify - alpha2);

            #if (fabs(err_lat2)>=THRESHOLD_ANGLE || fabs(err_lon2)>=THRESHOLD_ANGLE || fabs(err_alpha2)>=THRESHOLD_ANGLE)
            #{
                #printf("    !!! SIGNIFICANT DEVIATION: err_lat2 %g err_lon2 %g err_alpha2 %g\n", err_lat2, err_lon2, err_alpha2);
            #}
        #}

        #double lat1_verify, lon1_verify, alpha1_verify;

        #vincenty_result = vincenty_direct(lat2, lon2, alpha2 + 180.0, s, &lat1_verify, &lon1_verify, &alpha1_verify);

        #if (vincenty_result != 0)
        #{
            #printf("    !!! UNABLE TO DO BACKWARD DIRECT!\n\n");
        #}
        #else
        #{
            #alpha1_verify = normalize_degrees_unsigned(alpha1_verify + 180.0); // invert

            #printf("    CALCULATED BACKWARD DIRECT:\n\n");
            #printf("        lat1 ............. : "); print_dms(lat1_verify);   printf("\n");
            #printf("        lon1 ............. : "); print_dms(lon1_verify);   printf("\n");
            #printf("        alpha1 ........... : "); print_dms(alpha1_verify); printf("\n\n");


            #double err_lat1   = normalize_degrees_signed(lat1_verify   - lat1  );
            #double err_lon1   = normalize_degrees_signed(lon1_verify   - lon1  );
            #double err_alpha1 = normalize_degrees_signed(alpha1_verify - alpha1);

            #if (fabs(err_lat1)>=THRESHOLD_ANGLE || fabs(err_lon1)>=THRESHOLD_ANGLE || fabs(err_alpha1)>=THRESHOLD_ANGLE)
            #{
                #printf("    !!! SIGNIFICANT DEVIATION: err_lat1 %g err_lon1 %g err_alpha1 %g\n", err_lat1, err_lon1, err_alpha1);
            #}
        #}
    #} // we have a valid inverse

#}

#void test_grid1p(void)
#{
    #// start at -180+1/256; stop at 180-1/256;
    #// 119 steps of 781/256.0

    #for(double lat1 = -88.0; lat1 <=  88.0; lat1 += 8.0)
    #{
        #for(double lon1 = 0.0; lon1 < 360.0; lon1 += 8.0)
        #{
            #test1p(lat1, lon1);
        #}
    #}
#}

#void test_grid2p(void)
#{
    #for(double lat1 = -88.0; lat1 <=  88.0; lat1 +=  4.0)
    #{
        #for(double lon1 = 0.0; lon1 < 360.0; lon1 += 8.0)
        #{
            #for(double lat2 = -88.0; lat2 <= 88.0; lat2 +=  4.0)
            #{
                #for(double lon2 = 0.0; lon2 < 360.0; lon2 += 8.0)
                #{
                    #test2p(lat1, lon1, lat2, lon2);
                #}
            #}
        #}
    #}
#}

def main():

    if len(sys.argv) == 1:
        print(
            "\n"
            "Using test-vincenty:\n"
            "\n"
            "  Provide one or more of the following command line arguments:\n"
            "\n"
            "    '1' --> perform single-point-source test.\n"
            "    '2' --> perform point-to-point.\n"
            "    'p' --> perform tests given in Vincenty's paper.\n"
            "\n"
            "Example usage:\n"
            "\n"
            "$ ./test-vincenty p\n"
            "$ ./test-vincenty p 1 2\n"
            "\n"
        )
    else:
        for arg in sys.argv[1:]:
            if arg == "p":
                test_paper()
            elif arg == "1":
                test_grid1p()
            elif arg == "2":
                test_grid2p()
            else:
                print("unknown test '{}' requested (ignored).\n\n".format(arg));

if __name__ == "__main__":
    main()
