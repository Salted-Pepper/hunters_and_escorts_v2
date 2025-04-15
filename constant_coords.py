from copy import copy

from points import Point
from polygons import Polygon
import constants as cs
from itertools import pairwise

TAIWAN_POINTS = [Point(120.71, 21.93), Point(120.86, 21.90),
                 Point(120.89, 22.29), Point(121.17, 22.75),
                 Point(121.65, 24.00), Point(121.87, 24.54),
                 Point(121.83, 24.84), Point(122.00, 25.01),
                 Point(121.55, 25.30), Point(121.05, 25.024),
                 Point(120.73, 24.60), Point(120.18, 23.80),
                 Point(120.04, 23.10), Point(120.32, 22.54)]

ORCHID_ISLAND_POINTS = [Point(121.50, 22.08), Point(121.57, 22.09),
                        Point(121.57, 22.04), Point(121.60, 22.02),
                        Point(121.69, 22.00), Point(121.54, 22.03),
                        Point(121.50, 22.06)]

GREEN_ISLAND_POINTS = [Point(121.47, 22.68), Point(121.51, 22.68),
                       Point(121.51, 22.63), Point(121.47, 22.65)]

PENGHU_COUNTRY_POINTS = [Point(119.60, 23.68), Point(119.68, 23.60),
                         Point(119.69, 23.56), Point(119.61, 23.51),
                         Point(119.47, 23.56), Point(119.52, 23.65)]

WANGAN_POINTS = [Point(119.49, 23.36), Point(119.49, 23.39),
                 Point(119.51, 23.39), Point(119.51, 23.37),
                 Point(119.52, 23.37), Point(119.52, 23.37),
                 Point(119.51, 23.35)]

QIMEI_POINTS = [Point(119.45, 23.22), Point(119.43, 23.19),
                Point(119.41, 23.21)]

YONAGUNI_POINTS = [Point(122.93, 24.45), Point(122.96, 24.47),
                   Point(123.01, 24.47), Point(123.04, 24.46),
                   Point(123.01, 24.44), Point(122.95, 24.44)]

TAKETOMI_POINTS = [Point(123.66, 24.31), Point(123.77, 24.44),
                   Point(123.939, 24.364), Point(123.877, 24.257)]

ISHIGAKE_POINTS = [Point(124.071, 24.429), Point(124.157, 24.454),
                   Point(124.215, 24.456), Point(124.311, 24.609),
                   Point(124.341, 24.602), Point(124.283, 24.490),
                   Point(124.244, 24.348), Point(124.141, 24.327),
                   Point(124.113, 24.367), Point(124.142, 24.400),
                   Point(124.086, 24.418)]

MIYAKOJIMA_POINTS = [Point(125.136, 24.824), Point(125.164, 24.865),
                     Point(125.240, 24.940), Point(125.463, 24.725),
                     Point(125.241, 24.716)]

OKINAWA_POINTS = [Point(127.656, 26.082), Point(127.659, 26.218),
                  Point(127.759, 26.302), Point(127.714, 26.430),
                  Point(127.988, 26.577), Point(127.749, 26.723),
                  Point(128.099, 26.679), Point(128.254, 26.868),
                  Point(128.328, 26.783), Point(127.950, 26.444),
                  Point(128.006, 26.394), Point(127.832, 26.163)]

OKINOERABUJIMA_POINTS = [Point(128.712, 27.437), Point(128.567, 27.331),
                         Point(128.520, 27.375), Point(128.535, 27.405),
                         Point(128.562, 27.397)]

TOKUNOSHIMA_POINTS = [Point(128.969, 27.894), Point(128.968, 27.816),
                      Point(129.037, 27.770), Point(128.986, 27.671),
                      Point(128.881, 27.724)]

AMAMI_OSHIMA_POINTS = [Point(129.136, 28.249), Point(129.344, 28.368),
                       Point(129.686, 28.528), Point(129.719, 28.439),
                       Point(129.442, 28.241), Point(129.476, 28.215),
                       Point(129.367, 28.112)]

YAKUSHIMA_POINTS = [Point(130.375, 30.382), Point(130.509, 30.450),
                    Point(130.671, 30.377), Point(130.563, 30.229)]

TANEGASHIMA_POINTS = [Point(130.857, 30.362), Point(130.945, 30.662),
                      Point(131.059, 30.832), Point(131.053, 30.603)]

KOREA_POINTS = [Point(126.1105936433172, 34.382635296628266),
                Point(126.72869474423958, 34.283897291817006),
                Point(128.44754879324768, 34.8147862758336),
                Point(128.6397890487289, 34.666106922426835),
                Point(128.77548805259792, 35.055818803797955),
                Point(129.0129613093688, 35.06507513295652),
                Point(129.60099032613473, 36.049414003089616),
                Point(129.39744182033112, 36.12252266586377),
                Point(129.35220881904146, 37.22897033265078),
                Point(128.3570827906683, 38.60276796020003),  # Right side border
                Point(127.4184981196537, 39.22746826972953),
                Point(129.7479976860726, 40.85492641510266),
                Point(129.6349151828484, 41.51024592280302),
                Point(130.65265771186637, 42.30134275308864),
                Point(129.97416269252105, 60.0),  # N Korea
                Point(124.12779727582893, 39.81192015777447),
                Point(125.2925470590384, 39.50722297163861),
                Point(124.68190154162761, 38.10617579665901),
                Point(125.37170481129533, 37.740443461568674),
                Point(126.1180493325752, 37.731500450396815),
                Point(126.16328222811846, 37.740443375169086),  # Left side border
                Point(126.67215349262747, 36.97643996172249),
                Point(126.1293574771512, 36.777433290343886),
                Point(126.49122148746869, 35.627722046101404)
                ]

JEJUDO_POINTS = [Point(126.90759969506134, 33.522375907040484),
                 Point(126.85218991209356, 33.299521222070986),
                 Point(126.85218991209356, 33.299521222070986),
                 Point(126.17216075748912, 33.32898761892358),
                 Point(126.31246328374174, 33.4641845509088),
                 Point(126.81228862632128, 33.568364256062075)
                 ]

JAPAN_POINTS = [Point(130.6680, 30.9984),
                Point(131.4137, 31.3838),
                Point(132.0042, 32.7988),
                Point(133.0451, 32.7204),
                Point(134.1949, 33.2677),
                Point(135.7796, 33.4818),
                Point(136.9061, 34.2686),
                Point(138.8793, 34.6274),
                Point(139.9630, 34.9241),
                Point(140.8487, 35.6975),
                Point(142.0579, 39.5627),
                Point(141.4647, 41.4338),
                Point(143.2774, 41.9261),
                Point(145.8152, 43.3725),
                Point(145.2201, 43.6191),
                Point(145.3586, 44.3470),

                Point(143, 60.000),
                # Point(144.2777, 44.1120),
                # Point(141.9266, 45.5306),
                # Point(141.0040, 45.4560),

                Point(141.6954, 44.3112),
                Point(140.3330, 43.3142),
                Point(139.4117, 42.1322),
                Point(140.0953, 41.4157),
                Point(139.8551, 40.5510),
                Point(139.6519, 38.7299),
                Point(138.5063, 38.3107),
                Point(136.7695, 37.4650),
                Point(135.9724, 35.9734),
                Point(132.7096, 35.4625),
                Point(130.8763, 34.3220),
                Point(130.8924, 33.9353),
                Point(129.3773, 33.2891),
                Point(129.7838, 32.5757),
                Point(130.2457, 31.2584),
                ]

CHINA_POINTS = [Point(108.6931, 18.5089),
                Point(109.5998, 18.2412),
                Point(110.4158, 18.8429),
                Point(111.0505, 19.9736),
                Point(110.5165, 20.4275),
                Point(110.7785, 21.3874),
                Point(116.5915, 22.9918),
                Point(118.5702, 24.5542),
                Point(119.8267, 25.4489),
                Point(119.7370, 26.1600),
                Point(121.6577, 28.2670),
                Point(122.4296, 29.9607),
                Point(121.2089, 30.3022),
                Point(121.1551, 30.5962),
                Point(122.0526, 30.8277),
                Point(121.8193, 32.0225),
                Point(120.8679, 32.6292),
                Point(120.3118, 34.2553),
                Point(119.3245, 34.8909),
                Point(120.2579, 36.0313),
                Point(122.4771, 36.9018),
                Point(122.6585, 37.4461),
                Point(120.9187, 37.8686),
                Point(120.3104, 37.6830),
                Point(119.4992, 37.1319),
                Point(118.8908, 37.3783),
                Point(119.1327, 37.8684),
                Point(117.6811, 38.6395),
                Point(118.1720, 39.2042),
                Point(118.6417, 39.0883),
                Point(121.1820, 40.8549),
                Point(122.1853, 40.4663),
                Point(121.3314, 39.7643),
                Point(124.2560, 39.8955),
                Point(129.9952, 45.0),
                Point(117.9813, 45.0),
                Point(108.6931, 45.0)]

PHILIPPINES_POINTS = [Point(120.035, 10.000),
                      Point(119.709, 16.256),
                      Point(119.973, 16.470),
                      Point(120.190, 16.0514),
                      Point(120.397, 16.175),
                      Point(120.569, 18.483),
                      Point(120.863, 18.677),
                      Point(121.936, 18.270),
                      Point(122.174, 18.597),
                      Point(122.455, 17.125),
                      Point(121.499, 10.000)]

MEDIAN_ZONE = [Point(110.000, 40.000), Point(120.647, 40.000),
               Point(122.000, 27.000), Point(118.000, 23.000),
               Point(110.000, 19.949)]

A_ALL_ZONES = [Point(cs.MIN_LAT, cs.MIN_LONG),
               Point(cs.MIN_LAT, cs.MAX_LONG),
               Point(cs.MAX_LAT, cs.MAX_LONG),
               Point(cs.MAX_LAT, cs.MIN_LONG)]

B_TAIWAN_CONT = [Point(121.492, 25.690),
                 Point(122.466, 25.005),
                 Point(121.316, 21.800),
                 Point(120.610, 21.466),
                 Point(119.532, 22.978),
                 Point(119.663, 23.907),
                 Point(120.539, 25.120)]

C_TAIWAN_TERRITORIAL = [Point(121.564, 25.491),
                        Point(122.263, 24.978),
                        Point(121.140, 21.897),
                        Point(120.617, 21.686),
                        Point(119.814, 22.966),
                        Point(119.885, 23.764),
                        Point(120.715, 25.019)]

D_JAPAN_CONT = [Point(140.000, 45.000),
                Point(140.635, 45.000),
                Point(148.000, 45.000),
                Point(140.221, 31.421),
                Point(137.458, 33.581),
                Point(132.149, 31.120),
                Point(128.223, 25.7423),
                Point(126.331, 26.284),
                Point(128.874, 29.977),
                Point(128.083, 32.592),
                Point(129.153, 34.812),
                Point(132.970, 36.676),
                Point(137.879, 38.473),
                Point(138.837, 42.099),]

E_JAPAN_TERRITORIAL = [Point(143, 60.000), Point(145.27, 44.99),
                       Point(145.8152, 43.3725), Point(144.878, 41.632),
                       Point(139.942, 31.876), Point(138.191, 34.225),
                       Point(133.229, 32.386), Point(131.388, 30.395),
                       Point(128.040, 25.920), Point(126.500, 26.315),
                       Point(128.673, 27.954), Point(129.665, 30.897),
                       Point(128.401, 32.574), Point(129.220, 34.776),
                       Point(133.136, 36.475), Point(138.135, 38.341),
                       Point(139.163, 42.120), Point(141.74, 45.0)]

F_FILIPINO_CONT = [Point(119.623, 15.000), Point(119.376, 16.507),
                   Point(121.346, 20.987), Point(122.350, 20.841),
                   Point(122.920, 17.135), Point(122.574, 15.000)]

G_FILIPINO_TERRITORIAL = [Point(119.845, 15.000), Point(119.586, 16.420),
                          Point(121.569, 20.907), Point(122.140, 20.837),
                          Point(122.730, 17.131), Point(122.368, 15.000)]

H_OUTSIDE_10_DASH = [Point(124.152, 45.000), Point(124.152, 39.734),
                     Point(122.91, 34.89), Point(125.95, 30.62),
                     Point(125.02, 28.25), Point(125.55, 26.01),
                     Point(122.87, 25.26), Point(122.61, 24.47),
                     Point(122.48, 22.27), Point(116.41, 17.32),
                     Point(116.28, 15.00), Point(150.000, 15.000),
                     Point(150.000, 45.000)]

I_INSIDE_10_DASH = [Point(120.393, 28.055), Point(122.87, 25.26),
                    Point(122.61, 24.47), Point(122.48, 22.27),
                    Point(120.437, 20.874), Point(116.561, 23.397)]

J_TAIWAN_FILIPINO = [Point(121.326, 21.643), Point(121.606, 21.069),
                     Point(120.966, 19.487), Point(120.422, 21.672)]

K_TAIWAN_JAPAN = [Point(122.328, 25.218), Point(122.910, 25.200),
                  Point(122.611, 24.464), Point(122.405, 23.334),
                  Point(121.870, 23.334), Point(122.231, 24.503)]

L_INSIDE_MEDIAN_LINE = [Point(110, 45), Point(120.647, 45), Point(123, 32), Point(122, 27),
                        Point(118, 23), Point(110, 19.949)]

N_HOLDING_ZONE = [Point(126.0800, 22.8486),
                  Point(127.7491, 21.9493),
                  Point(127.7491, 20.1507),
                  Point(126.0800, 19.2514),
                  Point(124.4109, 20.1507),
                  Point(124.4109, 21.9493)]

P_PRIMARY_HUNTING_ZONE = [
    Point(122.263, 24.978),
    Point(122.87, 25.26),
    Point(122.61, 24.47),
    Point(122.48, 22.27),
    Point(120.437, 20.874),
    Point(121.140, 21.897)
]

ALL_ZONES = [A_ALL_ZONES, B_TAIWAN_CONT, C_TAIWAN_TERRITORIAL, D_JAPAN_CONT, E_JAPAN_TERRITORIAL, F_FILIPINO_CONT,
             G_FILIPINO_TERRITORIAL, H_OUTSIDE_10_DASH, I_INSIDE_10_DASH, J_TAIWAN_FILIPINO, K_TAIWAN_JAPAN,
             L_INSIDE_MEDIAN_LINE, N_HOLDING_ZONE]

# Landmasses
TAIWAN_COLOR = "0x015417"
JAPAN_COLOR = "0xffffff"
CHINA_COLOR = "0x7a0412"
OTHER_COLOR = "0x757373"

TAIWAN_LAND = Polygon(name="taiwan", points=TAIWAN_POINTS, color=TAIWAN_COLOR)
ORCHID = Polygon(name="orchid_island", points=ORCHID_ISLAND_POINTS, color=TAIWAN_COLOR)
GREEN_ISLAND = Polygon(name="green_island", points=GREEN_ISLAND_POINTS, color=TAIWAN_COLOR)
PENGHU = Polygon(name="penghu", points=PENGHU_COUNTRY_POINTS, color=TAIWAN_COLOR)
WANGAN = Polygon(name="wangan", points=WANGAN_POINTS, color=TAIWAN_COLOR)
QIMEI = Polygon(name="qimei", points=QIMEI_POINTS, color=TAIWAN_COLOR)
TAIWAN_AND_ISLANDS = [TAIWAN_LAND, ORCHID, GREEN_ISLAND, PENGHU, WANGAN, QIMEI]

YONAGUNI = Polygon(name="yonaguni", points=YONAGUNI_POINTS, color=JAPAN_COLOR)
TAKETOMI = Polygon(name="taketomi", points=TAKETOMI_POINTS, color=JAPAN_COLOR)
ISHIGAKE = Polygon(name="ishigaki", points=ISHIGAKE_POINTS, color=JAPAN_COLOR)
MIYAKOJIMA = Polygon(name="miyakojima", points=MIYAKOJIMA_POINTS, color=JAPAN_COLOR)
OKINAWA = Polygon(name="okinawa", points=OKINAWA_POINTS, color=JAPAN_COLOR)
OKINOERABUJIMA = Polygon(name="okinoerabujima", points=OKINOERABUJIMA_POINTS, color=JAPAN_COLOR)
TOKUNOSHIMA = Polygon(name="tokunoshima", points=TOKUNOSHIMA_POINTS, color=JAPAN_COLOR)
AMAMI = Polygon(name="amami_oshima", points=AMAMI_OSHIMA_POINTS, color=JAPAN_COLOR)
YAKUSHIMA = Polygon(name="yakushima", points=YAKUSHIMA_POINTS, color=JAPAN_COLOR)
TANEGASHIMA = Polygon(name="tanegashima", points=TANEGASHIMA_POINTS, color=JAPAN_COLOR)
JAPAN_LAND = Polygon(name="japan", points=JAPAN_POINTS, color=JAPAN_COLOR)

JAPAN_AND_ISLANDS = [YONAGUNI, TAKETOMI, ISHIGAKE, MIYAKOJIMA, OKINAWA, OKINOERABUJIMA, TOKUNOSHIMA,
                     AMAMI, YAKUSHIMA, TANEGASHIMA, JAPAN_LAND]

KOREA = Polygon(name="korea", points=KOREA_POINTS, color=OTHER_COLOR)
JEJUDO = Polygon(name="jejudo", points=JEJUDO_POINTS, color=OTHER_COLOR)
PHILIPPINES = Polygon(name="philippines", points=PHILIPPINES_POINTS, color=OTHER_COLOR)
OTHER_LAND = [KOREA, JEJUDO, PHILIPPINES]

CHINA = Polygon(name="china", points=CHINA_POINTS, color=CHINA_COLOR)

LAND_MASSES = TAIWAN_AND_ISLANDS + JAPAN_AND_ISLANDS + OTHER_LAND
ALL_MASSES = LAND_MASSES + [CHINA]


def set_points_to_bounds(polygon, margin=2) -> Polygon:
    for point in polygon.points:
        fix_point_to_edge(point, margin)

    new_points = copy(polygon.points)
    for i, j in pairwise(polygon.points):
        if i == j:
            new_points.remove(i)
    polygon.points = new_points
    polygon.calculate_bounds()
    return polygon


def fix_point_to_edge(point: Point, margin) -> None:
    if point.x < cs.MIN_LAT + margin:
        point.x = cs.MIN_LAT + margin
    elif point.x > cs.MAX_LAT - margin:
        point.x = cs.MAX_LAT - margin

    if point.y < cs.MIN_LONG + margin:
        point.y = cs.MIN_LONG + margin
    elif point.y > cs.MAX_LONG - margin:
        point.y = cs.MAX_LONG - margin

# TODO: Check if this is needed (probably better to simplify manually
# for landmass in ALL_MASSES:
#     set_points_to_bounds(landmass, margin=2)
