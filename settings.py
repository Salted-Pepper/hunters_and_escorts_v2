import constants as cs
from zones import *

# ---- World Settings ----
CHINA_ESCALATION_LEVELS = [1, 2, 3, 4, 5]
COALITION_ESCALATION_LEVELS = [1, 2, 3, 4, 5]

CHINA_SELECTED_LEVEL = 1
COALITION_SELECTED_LEVEL = 2

# ---- Simulation Settings ----
MULTITHREAD = False
ITERATION_LIMIT = 500
WEATHER_RESAMPLING_TIME_SPLIT = 1

simulation_period = 24 * 7
time_delta = 0.25
simulation_end_time = 0

SAFETY_ENDURANCE = 0.1

# ---- Teams ----
TEAM_COALITION = 1
TEAM_CHINA = 2

MARKET = "Market"
TAIWAN = "Taiwan"
USA = "USA"
JAPAN = "Japan"

# ---- Visualisation Settings ----
MERCHANT_COLOR = "black"
TAIWAN_ESCORT_COLOR = "forestgreen"
JAPAN_ESCORT_COLOR = "white"
US_ESCORT_COLOR = "navy"
UAV_COLOR = "indianred"
CHINESE_NAVY_COLOR = "red"
RECEPTOR_COLOR = "green"

PLOTTING_MODE = True
RECEPTOR_PLOT_PARAMETER = "Sea States"

# ---- Merchant Settings ----

# TODO: Check the Country x Model permutations
MERCHANT_INFO = {
    "T1": {"Type": "Tanker", "Class": "VLCC", "DWT": 320, "Cargo Size": 304, "Cargo Value": 160,
           "Speed (km/h)": 29.6, "Visibility": cs.LARGE, "arrivals": 2},
    "T2": {"Type": "Tanker", "Class": "Suezmax", "DWT": 157, "Cargo Size": 147, "Cargo Value": 80,
           "Speed (km/h)": 28.6, "Visibility": cs.MEDIUM, "arrivals": 2},
    "T3": {"Type": "Tanker", "Class": "Aframax", "DWT": 117, "Cargo Size": 87, "Cargo Value": 40,
           "Speed (km/h)": 27.8, "Visibility": cs.MEDIUM, "arrivals": 2},
    "T4": {"Type": "Tanker", "Class": "Panamax", "DWT": 75, "Cargo Size": 75, "Cargo Value": 35,
           "Speed (km/h)": 27.8, "Visibility": cs.MEDIUM, "arrivals": 2},
    "T5": {"Type": "Tanker", "Class": "MR", "DWT": 50, "Cargo Size": 45, "Cargo Value": 25,
           "Speed (km/h)": 27.8, "Visibility": cs.MEDIUM, "arrivals": 2},
    "T6": {"Type": "Tanker", "Class": "Handy", "DWT": 37, "Cargo Size": 33, "Cargo Value": 20,
           "Speed (km/h)": 27.8, "Visibility": cs.MEDIUM, "arrivals": 2},
    "T7": {"Type": "Tanker", "Class": "Small", "DWT": 25, "Cargo Size": 22, "Cargo Value": 10,
           "Speed (km/h)": 27.8, "Visibility": cs.SMALL, "arrivals": 2},

    "B1": {"Type": "Bulk Carriers", "Class": "Capesize", "DWT": 180, "Cargo Size": 180, "Cargo Value": 23.4,
           "Speed (km/h)": 26.9, "Visibility": cs.LARGE, "arrivals": 2},
    "B2": {"Type": "Bulk Carriers", "Class": "Panamax", "DWT": 82, "Cargo Size": 82, "Cargo Value": 10.6,
           "Speed (km/h)": 25.9, "Visibility": cs.MEDIUM, "arrivals": 2},
    "B3": {"Type": "Bulk Carriers", "Class": "Handymax", "DWT": 52, "Cargo Size": 52, "Cargo Value": 6.8,
           "Speed (km/h)": 25.0, "Visibility": cs.MEDIUM, "arrivals": 2},
    "B4": {"Type": "Bulk Carriers", "Class": "Handysize", "DWT": 38, "Cargo Size": 38, "Cargo Value": 5.0,
           "Speed (km/h)": 24.0, "Visibility": cs.MEDIUM, "arrivals": 2},

    "C1": {"Type": "Container Ships", "Class": "≥ 12k+ TEU", "DWT": 150, "Cargo Size": 186, "Cargo Value": 560,
           "Speed (km/h)": 44.4, "Visibility": cs.LARGE, "arrivals": 2},
    "C2": {"Type": "Container Ships", "Class": "8-12k TEU", "DWT": 120, "Cargo Size": 150, "Cargo Value": 450,
           "Speed (km/h)": 41.7, "Visibility": cs.LARGE, "arrivals": 2},
    "C3": {"Type": "Container Ships", "Class": "5-8k TEU", "DWT": 90, "Cargo Size": 120, "Cargo Value": 360,
           "Speed (km/h)": 38.9, "Visibility": cs.MEDIUM, "arrivals": 2},
    "C4": {"Type": "Container Ships", "Class": "3-5k TEU", "DWT": 65, "Cargo Size": 80, "Cargo Value": 240,
           "Speed (km/h)": 37.0, "Visibility": cs.MEDIUM, "arrivals": 2},
    "C5": {"Type": "Container Ships", "Class": "2-3k TEU", "DWT": 45, "Cargo Size": 55, "Cargo Value": 165,
           "Speed (km/h)": 33.3, "Visibility": cs.SMALL, "arrivals": 2},
    "C6": {"Type": "Container Ships", "Class": "< 900 TEU", "DWT": 12, "Cargo Size": 15, "Cargo Value": 45,
           "Speed (km/h)": 27.8, "Visibility": cs.SMALL, "arrivals": 2},

    "LNG": {"Type": "LNG", "Class": "LNG", "DWT": 87, "Cargo Size": 174, "Cargo Value": 48.1,
            "Speed (km/h)": 38.9, "Visibility": cs.LARGE, "arrivals": 2},

    "GC1": {"Type": "General Cargo", "Class": "General Cargo", "DWT": 50, "Cargo Size": 45, "Cargo Value": 16.5,
            "Speed (km/h)": 30.6, "Visibility": cs.MEDIUM, "arrivals": 2},
    "GC2": {"Type": "General Cargo", "Class": "General Cargo", "DWT": 25, "Cargo Size": 22, "Cargo Value": 8.2,
            "Speed (km/h)": 28.7, "Visibility": cs.SMALL, "arrivals": 2},
    "GC3": {"Type": "General Cargo", "Class": "General Cargo", "DWT": 10, "Cargo Size": 8, "Cargo Value": 3.0,
            "Speed (km/h)": 26.0, "Visibility": cs.SMALL, "arrivals": 2},

    "RoRo": {"Type": "Ro-Ro", "Class": "RoRo", "DWT": 15, "Cargo Size": 12, "Cargo Value": 5.0,
             "Speed (km/h)": 30.0, "Visibility": cs.SMALL, "arrivals": 2},

    "Reefer": {"Type": "Reefer", "Class": "Reefer", "DWT": 7.5, "Cargo Size": 6.75, "Cargo Value": 25,
               "Speed (km/h)": 40.7, "Visibility": cs.MEDIUM, "arrivals": 2},

    "LPG1": {"Type": "LPG", "Class": "VLGC", "DWT": 55, "Cargo Size": 82, "Cargo Value": 18,
             "Speed (km/h)": 32.0, "Visibility": cs.LARGE, "arrivals": 2},
    "LPG2": {"Type": "LPG", "Class": "Medium", "DWT": 22, "Cargo Size": 30, "Cargo Value": 8,
             "Speed (km/h)": 30.0, "Visibility": cs.MEDIUM, "arrivals": 2},
    "LPG3": {"Type": "LPG", "Class": "Coaster", "DWT": 3.5, "Cargo Size": 5, "Cargo Value": 1,
             "Speed (km/h)": 28.0, "Visibility": cs.SMALL, "arrivals": 2},

    "Chem1": {"Type": "Chemical", "Class": "Oceangoing", "DWT": 50, "Cargo Size": 45, "Cargo Value": 22,
              "Speed (km/h)": 30.0, "Visibility": cs.MEDIUM, "arrivals": 2},
    "Chem2": {"Type": "Chemical", "Class": "Medium", "DWT": 22, "Cargo Size": 20, "Cargo Value": 10,
              "Speed (km/h)": 30.0, "Visibility": cs.LARGE, "arrivals": 2},
    "Chem3": {"Type": "Chemical", "Class": "Coastal", "DWT": 4.3, "Cargo Size": 4, "Cargo Value": 2,
              "Speed (km/h)": 30.0, "Visibility": cs.SMALL, "arrivals": 2}
}

merchant_country_distribution = {country: 1 / 4 for country in [MARKET, TAIWAN, JAPAN, USA]}

merchant_rules = {1: {MARKET: cs.COMPLY,
                      TAIWAN: cs.EVADE,
                      USA: cs.COMPLY,
                      JAPAN: cs.COMPLY},
                  2: {MARKET: cs.COMPLY,
                      TAIWAN: cs.RESIST,
                      USA: cs.COMPLY,
                      JAPAN: cs.COMPLY},
                  3: {MARKET: cs.COMPLY,
                      TAIWAN: cs.RESIST,
                      USA: cs.EVADE,
                      JAPAN: cs.COMPLY},
                  4: {MARKET: cs.COMPLY,
                      TAIWAN: cs.RESIST,
                      USA: cs.RESIST,
                      JAPAN: cs.COMPLY},
                  5: {MARKET: cs.COMPLY,
                      TAIWAN: cs.RESIST,
                      USA: cs.RESIST,
                      JAPAN: cs.RESIST}}


def get_merchant_rule(country: str) -> str:
    return merchant_rules[COALITION_SELECTED_LEVEL][country]


# ---- Engagement/Target Rules ----

min_r_o_e = {
    1: {
        cs.COALITION_TW_ESCORT: {ZONE_A.name: 4, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 4, ZONE_E.name: 4,
                                 ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_TW_AIRCRAFT: {ZONE_A.name: 4, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 4, ZONE_E.name: 4,
                                   ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_TW_SUB: {ZONE_A.name: 4, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 4, ZONE_E.name: 4,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 4, ZONE_L.name: 4},

        cs.COALITION_US_ESCORT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 4, ZONE_E.name: 4,
                                 ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_US_AIRCRAFT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 4, ZONE_E.name: 4,
                                   ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_US_SUB: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 4, ZONE_E.name: 4,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},

        cs.COALITION_JP_ESCORT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                                 ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_JP_AIRCRAFT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                                   ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_JP_SUB: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4}
    },

    2: {
        cs.COALITION_TW_ESCORT: {ZONE_A.name: 4, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 4, ZONE_E.name: 4,
                                 ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 1, ZONE_L.name: 4},
        cs.COALITION_TW_AIRCRAFT: {ZONE_A.name: 4, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 4, ZONE_E.name: 4,
                                   ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 1, ZONE_L.name: 4},
        cs.COALITION_TW_SUB: {ZONE_A.name: 4, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 4, ZONE_E.name: 4,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 1, ZONE_L.name: 4},

        cs.COALITION_US_ESCORT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 4, ZONE_E.name: 4,
                                 ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_US_AIRCRAFT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 4, ZONE_E.name: 4,
                                   ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_US_SUB: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 4, ZONE_E.name: 4,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},

        cs.COALITION_JP_ESCORT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                                 ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_JP_AIRCRAFT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                                   ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_JP_SUB: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4}
    },

    3: {
        cs.COALITION_TW_ESCORT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 2,
                                 ZONE_F.name: 1, ZONE_G.name: 2, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 4},
        cs.COALITION_TW_AIRCRAFT: {ZONE_A.name: 2, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 2, ZONE_E.name: 2,
                                   ZONE_F.name: 2, ZONE_G.name: 2, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},
        cs.COALITION_TW_SUB: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},

        cs.COALITION_US_ESCORT: {ZONE_A.name: 2, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 2, ZONE_E.name: 2,
                                 ZONE_F.name: 2, ZONE_G.name: 2, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},
        cs.COALITION_US_AIRCRAFT: {ZONE_A.name: 2, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 2, ZONE_E.name: 2,
                                   ZONE_F.name: 2, ZONE_G.name: 2, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},
        cs.COALITION_US_SUB: {ZONE_A.name: 2, ZONE_B.name: 2, ZONE_C.name: 1, ZONE_D.name: 2, ZONE_E.name: 2,
                              ZONE_F.name: 2, ZONE_G.name: 2, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},

        cs.COALITION_JP_ESCORT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                                 ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_JP_AIRCRAFT: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                                   ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4},
        cs.COALITION_JP_SUB: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4}
    },

    4: {
        cs.COALITION_TW_ESCORT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                                 ZONE_F.name: 1, ZONE_G.name: 1, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 4},
        cs.COALITION_TW_AIRCRAFT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 2, ZONE_E.name: 1,
                                   ZONE_F.name: 2, ZONE_G.name: 1, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},
        cs.COALITION_TW_SUB: {ZONE_A.name: 2, ZONE_B.name: 2, ZONE_C.name: 2, ZONE_D.name: 1, ZONE_E.name: 1,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},

        cs.COALITION_US_ESCORT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 2, ZONE_E.name: 1,
                                 ZONE_F.name: 2, ZONE_G.name: 1, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},
        cs.COALITION_US_AIRCRAFT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 2, ZONE_E.name: 1,
                                   ZONE_F.name: 2, ZONE_G.name: 1, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},
        cs.COALITION_US_SUB: {ZONE_A.name: 2, ZONE_B.name: 2, ZONE_C.name: 2, ZONE_D.name: 1, ZONE_E.name: 1,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},

        cs.COALITION_JP_ESCORT: {ZONE_A.name: 2, ZONE_B.name: 2, ZONE_C.name: 2, ZONE_D.name: 1, ZONE_E.name: 1,
                                 ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},
        cs.COALITION_JP_AIRCRAFT: {ZONE_A.name: 2, ZONE_B.name: 2, ZONE_C.name: 2, ZONE_D.name: 1, ZONE_E.name: 1,
                                   ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 2, ZONE_I.name: 2, ZONE_L.name: 4},
        cs.COALITION_JP_SUB: {ZONE_A.name: 4, ZONE_B.name: 4, ZONE_C.name: 4, ZONE_D.name: 2, ZONE_E.name: 1,
                              ZONE_F.name: 4, ZONE_G.name: 4, ZONE_H.name: 4, ZONE_I.name: 4, ZONE_L.name: 4}
    },

    5: {
        cs.COALITION_TW_ESCORT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                                 ZONE_F.name: 1, ZONE_G.name: 1, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 1},
        cs.COALITION_TW_AIRCRAFT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                                   ZONE_F.name: 1, ZONE_G.name: 1, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 1},
        cs.COALITION_TW_SUB: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                              ZONE_F.name: 1, ZONE_G.name: 1, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 1},

        cs.COALITION_US_ESCORT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                                 ZONE_F.name: 1, ZONE_G.name: 1, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 1},
        cs.COALITION_US_AIRCRAFT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                                   ZONE_F.name: 1, ZONE_G.name: 1, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 1},
        cs.COALITION_US_SUB: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                              ZONE_F.name: 1, ZONE_G.name: 1, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 1},

        cs.COALITION_JP_ESCORT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                                 ZONE_F.name: 4, ZONE_G.name: 2, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 1},
        cs.COALITION_JP_AIRCRAFT: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                                   ZONE_F.name: 4, ZONE_G.name: 2, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 1},
        cs.COALITION_JP_SUB: {ZONE_A.name: 1, ZONE_B.name: 1, ZONE_C.name: 1, ZONE_D.name: 1, ZONE_E.name: 1,
                              ZONE_F.name: 4, ZONE_G.name: 2, ZONE_H.name: 1, ZONE_I.name: 1, ZONE_L.name: 1}
    }
}

coalition_r_o_e_rules = min_r_o_e[COALITION_SELECTED_LEVEL]
hunter_target_rules = {hunter_agent: {coalition_agent: True for coalition_agent in cs.COALITION_TYPES}
                       for hunter_agent in cs.HUNTER_TYPES}

# ---- Zone Assignment Rules ----
zone_assignment_hunter = {agent_type: {zone: 1 / len(ZONES) for zone in ZONES
                                       if zone.name not in ['C', 'E']}
                          for agent_type in cs.HUNTER_TYPES}
zone_assignment_coalition = {agent_type: {zone: 1 / len(ZONES) for zone in ZONES}
                             for agent_type in cs.COALITION_TYPES
                             if agent_type not in [cs.COALITION_TW_MERCHANT,
                                                   cs.COALITION_JP_MERCHANT,
                                                   cs.COALITION_US_MERCHANT]}
