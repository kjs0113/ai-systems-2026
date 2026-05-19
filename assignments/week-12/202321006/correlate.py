import numpy as np
from scipy.stats import spearmanr, pearsonr

def calculate_correlation(human_scores, judge_scores):
    """
    Calculates Spearman and Pearson correlation.
    """
    n = len(human_scores)
    if n < 2:
        return None
        
    rho, rho_p = spearmanr(human_scores, judge_scores)
    r, r_p = pearsonr(human_scores, judge_scores)
    
    return {
        "spearman_rho": round(rho, 4),
        "spearman_p": round(rho_p, 4),
        "pearson_r": round(r, 4),
        "pearson_p": round(r_p, 4),
        "n": n
    }

if __name__ == "__main__":
    # Example Data (10 samples)
    human = [9, 8, 4, 3, 7, 5, 10, 2, 6, 8]
    judge = [8.5, 7.8, 5.0, 3.5, 6.5, 5.5, 9.5, 3.0, 6.2, 8.2]
    
    stats = calculate_correlation(human, judge)
    print(stats)
