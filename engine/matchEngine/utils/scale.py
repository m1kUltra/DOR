import random

# Precomputed scale factors for attr=10 calibration
scale_factor_lookup = {
    1: 0.5488542990849676,
    2: 0.30173249934070745,
    3: 0.16605886887805832,
    4: 0.09145528830218691,
    5: 0.05024328976771668,
    6: 0.027642391647769795,
    7: 0.015221558815374655,
    8: 0.008368187285112252,
    9: 0.004603547701779899,
    10: 0.0025275815188501157,
    11: 0.0013931973574938213,
    12: 0.0007660485615191882
}

def balanced_score(attr_value, exponent):
    norm_val = ((attr_value - 1) / 19) ** 0.8
    scaled_val = norm_val ** exponent
    raw_score = scaled_val * random.random() - scaled_val * random.random()
    return raw_score / scale_factor_lookup[exponent]  

score = balanced_score(2, 4)  # attr=15, exponent=4
print(score) 