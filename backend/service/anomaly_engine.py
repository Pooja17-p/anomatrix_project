from datetime import datetime

def detect_anomaly(
    login_count,
    is_known_device,
    current_hour=None,
    impossible_travel=False,
    ai_score=0
):
    """
    Evaluates context, historical frequency, location travel impossibility,
    and machine learning behavioral scores to yield a combined 0-100 anomaly metric.
    """
    heuristic_anomaly = 0

    # Unknown device heuristic
    if not is_known_device:
        heuristic_anomaly += 40

    # Excessive logins heuristic
    if login_count > 5:
        heuristic_anomaly += 30

    # Unusual login time heuristic (1 AM - 5 AM)
    if current_hour is None:
        current_hour = datetime.now().hour

    if 1 <= current_hour <= 5:
        heuristic_anomaly += 20

    # Blend heuristics and AI models if AI score is provided
    # If the user has history and AI model is active, weigh the AI prediction heavily (70% AI, 30% Heuristics)
    if ai_score > 0:
        combined_score = int(0.3 * heuristic_anomaly + 0.7 * ai_score)
    else:
        combined_score = heuristic_anomaly

    # Critical override: Impossible travel is a severe security event
    if impossible_travel:
        combined_score = max(95, combined_score)

    return min(100, combined_score)