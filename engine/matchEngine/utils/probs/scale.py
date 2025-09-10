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
 
def balanced_score(attacker_norm, defender_norm, scale):
    scale_factor = scale_factor_lookup[scale+1]


    # Normalise to [-1, 1]
    
   
    att_pow = attacker_norm 
    def_pow = defender_norm 
    # Generate samples skewed toward 1 to approximate a normal distribution
    att_rand = random.random() ** 0.5
    def_rand = random.random() ** 0.5
    atk = (att_pow* att_rand) /scale_factor
    dfd = (def_pow * def_rand)/scale_factor
    


    # Generate raw score
    score =  atk - dfd
    
    # Analytic scale factor — maximum possible absolute value
   

    # Lookup scale factor based on exponent calibration
    
    return max(-1.0, min(1.0, score))
