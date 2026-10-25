
def evaluate_baseline(
    monthly_cost,
    usage_days,
    importance_rating,
    alternative_rating,
    cancellation_fee_amount
):
    """Evaluate a subscription using a weighted-score baseline.

    The weights are design assumptions, not learned parameters.
    Cancellation fees are treated separately from subscription value.
    """

    values = {
        "Monthly cost": (monthly_cost, 0, 2000),
        "Usage days": (usage_days, 0, 30),
        "Importance": (importance_rating, 0, 10),
        "Alternatives": (alternative_rating, 0, 10),
        "Cancellation fee": (cancellation_fee_amount, 0, 1000),
    }

    for name, (value, minimum, maximum) in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be numeric.")

        if not minimum <= value <= maximum:
            raise ValueError(
                f"{name} must be between {minimum} and {maximum}."
            )

    if int(usage_days) != usage_days:
        raise ValueError("Usage days must be a whole number.")

    # Normalize inputs to a 0–100 scale.
    cost_score = (monthly_cost / 2000) * 100
    usage_score = (usage_days / 30) * 100
    importance_score = (importance_rating / 10) * 100
    alternatives_score = (alternative_rating / 10) * 100

    # Higher values mean greater retention suitability.
    score = (
        0.20 * (100 - cost_score)
        + 0.30 * usage_score
        + 0.30 * importance_score
        + 0.20 * (100 - alternatives_score)
    )

    # Cancellation fee does not increase subscription value.
    # It is considered separately when estimating cancellation savings.
    score = max(0.0, min(100.0, score))

    if score < 25:
        action = "Cancel"
    elif score < 45:
        action = "Downgrade"
    elif score < 65:
        action = "Review"
    else:
        action = "Keep"

    return {
        "score": round(score, 2),
        "action": action
    }


if __name__ == "__main__":
    result = evaluate_baseline(
        monthly_cost=649,
        usage_days=12,
        importance_rating=8,
        alternative_rating=7,
        cancellation_fee_amount=0
    )

    print("SUBSIGHT - Weighted Score Test")
    print("------------------------------")
    print(f"Retention score: {result['score']}")
    print(f"Recommendation: {result['action']}")
