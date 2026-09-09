def calculate_trust_score(
    is_known_device,
    login_count,
    anomaly_score
):
    """
    Computes a trust score between 0 and 100 based on device trust,
    login frequency, and context anomalies.
    Penalizes trust severely if anomaly score is elevated.
    """
    trust_score = 0

    # Device Trust (Max 40)
    if is_known_device:
        trust_score += 40
    else:
        trust_score += 10

    # User Activity Trust (Max 30)
    if login_count >= 3:
        trust_score += 30
    else:
        trust_score += 10

    # Anomaly Trust (Max 30)
    if anomaly_score <= 20:
        trust_score += 30
    elif anomaly_score <= 50:
        trust_score += 15
    else:
        trust_score += 5

    # Zero Trust Principle: Severe anomaly overrides all other factors
    if anomaly_score >= 80:
        # Cap trust score to very low level (maximum 15)
        trust_score = min(15, trust_score)
    elif anomaly_score >= 50:
        # Reduce trust score by half
        trust_score = int(trust_score * 0.5)

    return max(0, min(100, trust_score))