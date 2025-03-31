# ---- Reachable Software Components ----
world = None
interface = None
display = None

simulation_running = False
# ["Waiting to start", "Loading", "Ready"]

# ---- Geographical Constants ----
LATITUDE_CONVERSION_FACTOR = 110.574
LONGITUDE_CONVERSION_FACTOR = 111.320

MIN_LAT = 110
MAX_LAT = 140
MIN_LONG = 15
MAX_LONG = 42

GRID_WIDTH = 1
GRID_HEIGHT = GRID_WIDTH

# ---- Movement ----

SAFETY_ENDURANCE = 1.1

# ----  Receptors  ----
DEPRECIATION_PER_TIME_DELTA = 0.99
RECEPTOR_RADIUS_MULTIPLIER = 10

LAT_GRID_EXTRA = 6
LONG_GRID_EXTRA = 6

# ---- Fixed Properties Strings ----

# Detection Size
STEALTHY = "stealthy"
VSMALL = "vsmall"
SMALL = "small"
MEDIUM = "medium"
LARGE = "large"

rcs_dict = {STEALTHY: 0.25,
            VSMALL: 0.5,
            SMALL: 1,
            MEDIUM: 1.25,
            LARGE: 1.5}

# Detection Skill
DET_BASIC = "Basic"
DET_ADV = "Advanced"

# Attack Skill
ATT_BASIC = "Basic"
ATT_ADV = "Advanced"

# Merchant Reactions
COMPLY = "compliant"
EVADE = "evade"
RESIST = "resist"

# ---- Agent Detection Fixed Parameters ----
PHEROMONE_SPREAD = 1

PATROL_LOCATIONS = 10
K_CONSTANT_ADV = 39_633
K_CONSTANT_BASIC = 2_747

CHINESE_NAVY_MAX_DETECTION_RANGE = 463

# ---- Agent Types ----

# Hunter Types
HUNTER_CCG = "Ship CCG"
HUNTER_MSA = "Ship MSA"
HUNTER_PAFMM = "Ship PAFMM"
HUNTER_PLAN = "Ship PLAN"

HUNTER_SUBMARINE = "Submarine"
HUNTER_MINELAYER = "Minelayer"

HUNTER_UAV = "Air UAV"
HUNTER_AIRCRAFT = "Air Manned"

HUNTER_TYPES = [HUNTER_CCG, HUNTER_MSA, HUNTER_PAFMM, HUNTER_PLAN, HUNTER_MINELAYER, HUNTER_SUBMARINE,
                HUNTER_UAV, HUNTER_AIRCRAFT]

# Coalition Types
COALITION_TW_MERCHANT = "TW MER"
COALITION_US_MERCHANT = "US MER"
COALITION_JP_MERCHANT = "JP MER"
COALITION_MK_MERCHANT = "MK MER"

COALITION_TW_ESCORT = "TW ESC"
COALITION_US_ESCORT = "US ESC"
COALITION_JP_ESCORT = "JP ESC"

COALITION_TW_AIRCRAFT = "TW AIR"
COALITION_US_AIRCRAFT = "US AIR"
COALITION_JP_AIRCRAFT = "JP AIR"

COALITION_TW_SUB = "TW SUB"
COALITION_US_SUB = "US SUB"
COALITION_JP_SUB = "JP SUB"

COALITION_TYPES = [COALITION_TW_MERCHANT, COALITION_US_MERCHANT, COALITION_JP_MERCHANT, COALITION_MK_MERCHANT,
                   COALITION_TW_ESCORT, COALITION_TW_AIRCRAFT, COALITION_TW_SUB,
                   COALITION_US_ESCORT, COALITION_US_AIRCRAFT, COALITION_US_SUB,
                   COALITION_JP_ESCORT, COALITION_JP_AIRCRAFT, COALITION_JP_SUB]

# ---- Agent Data ----
CHINA_NAVY_DATA = None
CHINA_SUB_DATA = None
CHINA_AIR_DATA = None

COALITION_NAVY_DATA = None

# ---- Deterministic Detecting Behaviour ----
CHINA_NAVY_DETECTING_SHIP = {DET_ADV: {LARGE: 56,
                                       MEDIUM: 56,
                                       SMALL: 37,
                                       VSMALL: 20,
                                       STEALTHY: 11},
                             DET_BASIC: {LARGE: 37,
                                         MEDIUM: 37,
                                         SMALL: 28,
                                         VSMALL: 17,
                                         STEALTHY: 9}}

CHINA_NAVY_DETECTING_AIR = {DET_ADV: {LARGE: 463,
                                      MEDIUM: 320,
                                      SMALL: 239,
                                      VSMALL: 102,
                                      STEALTHY: 70},
                            DET_BASIC: {LARGE: 350,
                                        MEDIUM: 244,
                                        SMALL: 176,
                                        VSMALL: 70,
                                        STEALTHY: 20}}

CHINA_NAVY_DETECTING_SUB_AWS = {DET_ADV: {LARGE: 185,
                                          MEDIUM: 74,
                                          SMALL: 37,
                                          VSMALL: 18.5,
                                          STEALTHY: 9.25},
                                DET_BASIC: {LARGE: 64.82,
                                            MEDIUM: 25.928,
                                            SMALL: 12.964,
                                            VSMALL: 6.482,
                                            STEALTHY: 3.241}}

CHINA_NAVY_DETECTING_SUB_NO_AWS = {DET_ADV: {LARGE: 0,
                                             MEDIUM: 0,
                                             SMALL: 0,
                                             VSMALL: 0,
                                             STEALTHY: 0},
                                   DET_BASIC: {LARGE: 39.818,
                                               MEDIUM: 15.9272,
                                               SMALL: 7.9636,
                                               VSMALL: 3.9818,
                                               STEALTHY: 1.9909}}

# ---- Weather Data ----
WEATHER_UPDATE_TIME = 7

weather_markov_dict = {0: {0: 0.86797, 1: 0.13202, 2: 1e-05, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0,
                           8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       1: {0: 0.01759, 1: 0.91031, 2: 0.072, 3: 0.0001, 4: 0.0, 5: 0, 6: 0, 7: 0,
                           8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       2: {0: 0.00028, 1: 0.07991, 2: 0.84874, 3: 0.07046, 4: 0.0006, 5: 1e-05, 6: 0.0, 7: 0,
                           8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       3: {0: 0.00012, 1: 0.00891, 2: 0.20346, 3: 0.67584, 4: 0.10752, 5: 0.00405, 6: 9e-05, 7: 0.0,
                           8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       4: {0: 6e-05, 1: 0.00465, 2: 0.0558, 3: 0.27422, 4: 0.49631, 5: 0.1529, 6: 0.01496, 7: 0.00106,
                           8: 4e-05, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0},
                       5: {0: 1e-05, 1: 0.00211, 2: 0.02767, 3: 0.12292, 4: 0.30308, 5: 0.37542, 6: 0.13974, 7: 0.02456,
                           8: 0.00385, 9: 0.00054, 10: 9e-05, 11: 0, 12: 0, 13: 0, 14: 0},
                       6: {0: 0, 1: 0.00064, 2: 0.018, 3: 0.07771, 4: 0.15775, 5: 0.28886, 6: 0.28494, 7: 0.13138,
                           8: 0.03085, 9: 0.00733, 10: 0.00195, 11: 0.00061, 12: 0, 13: 0, 14: 0},
                       7: {0: 0, 1: 0.00027, 2: 0.01244, 3: 0.05629, 4: 0.10846, 5: 0.18872, 6: 0.25432, 7: 0.20376,
                           8: 0.11955, 9: 0.04385, 10: 0.00886, 11: 0.00304, 12: 0.00045, 13: 0, 14: 0},
                       8: {0: 0, 1: 0, 2: 0.00566, 3: 0.05019, 4: 0.08571, 5: 0.11737, 6: 0.19562, 7: 0.19614,
                           8: 0.14466, 9: 0.1323, 10: 0.06178, 11: 0.00927, 12: 0.00103, 13: 0.00026, 14: 0},
                       9: {0: 0, 1: 0, 2: 0.00112, 3: 0.03652, 4: 0.05506, 5: 0.08708, 6: 0.14944, 7: 0.19663,
                           8: 0.1309, 9: 0.12978, 10: 0.14888, 11: 0.0573, 12: 0.00618, 13: 0.00056, 14: 0.00056},
                       10: {0: 0, 1: 0, 2: 0, 3: 0.01331, 4: 0.04197, 5: 0.04606, 6: 0.07062, 7: 0.14944,
                            8: 0.19345, 9: 0.13204, 10: 0.14637, 11: 0.15967, 12: 0.03992, 13: 0.00716, 14: 0},
                       11: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0.01843, 5: 0.03456, 6: 0.06452, 7: 0.07834,
                            8: 0.12903, 9: 0.19124, 10: 0.27419, 11: 0.15207, 12: 0.0553, 13: 0, 14: 0.0023},
                       12: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0.01111, 6: 0.04444, 7: 0.05556,
                            8: 0.08889, 9: 0.21111, 10: 0.34444, 11: 0.17778, 12: 0.06667, 13: 0, 14: 0},
                       13: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0.1,
                            8: 0.1, 9: 0.2, 10: 0.3, 11: 0.2, 12: 0, 13: 0.1, 14: 0},
                       14: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0,
                            8: 0, 9: 0, 10: 0, 11: 0.5, 12: 0.5, 13: 0, 14: 0}}

sea_state_values = {0: 1,
                    1: 0.89,
                    2: 0.77,
                    3: 0.68,
                    4: 0.62,
                    5: 0.53,
                    6: 0.47}
