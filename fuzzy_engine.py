
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# --------------------------------------------------
# 1. Define input and output universes
# --------------------------------------------------

cost = ctrl.Antecedent(np.arange(0, 2001, 1), "cost")
usage = ctrl.Antecedent(np.arange(0, 31, 1), "usage")
importance = ctrl.Antecedent(np.arange(0, 10.1, 0.1), "importance")
alternatives = ctrl.Antecedent(
    np.arange(0, 10.1, 0.1), "alternatives"
)
cancellation_fee = ctrl.Antecedent(
    np.arange(0, 1001, 1), "cancellation_fee"
)

retention = ctrl.Consequent(
    np.arange(0, 101, 1), "retention"
)


# --------------------------------------------------
# 2. Define membership functions
# --------------------------------------------------

# Subscription cost (rupees per month)
cost["low"] = fuzz.trapmf(cost.universe, [0, 0, 250, 700])
cost["medium"] = fuzz.trimf(cost.universe, [400, 1000, 1500])
cost["high"] = fuzz.trapmf(
    cost.universe, [1200, 1600, 2000, 2000]
)

# Usage days per month
usage["rare"] = fuzz.trapmf(usage.universe, [0, 0, 3, 10])
usage["occasional"] = fuzz.trimf(usage.universe, [5, 15, 24])
usage["frequent"] = fuzz.trapmf(
    usage.universe, [18, 25, 30, 30]
)

# Importance rating
importance["low"] = fuzz.trapmf(
    importance.universe, [0, 0, 2, 4]
)
importance["medium"] = fuzz.trimf(
    importance.universe, [2, 5, 8]
)
importance["high"] = fuzz.trapmf(
    importance.universe, [6, 8, 10, 10]
)

# Availability of cheaper alternatives
alternatives["poor"] = fuzz.trapmf(
    alternatives.universe, [0, 0, 2, 4]
)
alternatives["moderate"] = fuzz.trimf(
    alternatives.universe, [2, 5, 8]
)
alternatives["good"] = fuzz.trapmf(
    alternatives.universe, [6, 8, 10, 10]
)

# One-time cancellation fee
cancellation_fee["low"] = fuzz.trapmf(
    cancellation_fee.universe, [0, 0, 100, 300]
)
cancellation_fee["medium"] = fuzz.trimf(
    cancellation_fee.universe, [150, 500, 800]
)
cancellation_fee["high"] = fuzz.trapmf(
    cancellation_fee.universe, [600, 800, 1000, 1000]
)

# Retention suitability (0 to 100)
retention["very_low"] = fuzz.trapmf(
    retention.universe, [0, 0, 10, 25]
)
retention["low"] = fuzz.trimf(
    retention.universe, [15, 32, 48]
)
retention["medium"] = fuzz.trimf(
    retention.universe, [38, 55, 72]
)
retention["high"] = fuzz.trapmf(
    retention.universe, [62, 78, 100, 100]
)


# --------------------------------------------------
# 3. Define the fuzzy rule base
# --------------------------------------------------

rules = [
    # Base rules: usage and importance
    ctrl.Rule(
        usage["rare"] & importance["low"],
        retention["very_low"]
    ),
    ctrl.Rule(
        usage["rare"] & importance["medium"],
        retention["low"]
    ),
    ctrl.Rule(
        usage["rare"] & importance["high"],
        retention["medium"]
    ),
    ctrl.Rule(
        usage["occasional"] & importance["low"],
        retention["low"]
    ),
    ctrl.Rule(
        usage["occasional"] & importance["medium"],
        retention["medium"]
    ),
    ctrl.Rule(
        usage["occasional"] & importance["high"],
        retention["high"]
    ),
    ctrl.Rule(
        usage["frequent"] & importance["low"],
        retention["medium"]
    ),
    ctrl.Rule(
        usage["frequent"] & importance["medium"],
        retention["high"]
    ),
    ctrl.Rule(
        usage["frequent"] & importance["high"],
        retention["high"]
    ),

    # Cost and alternative adjustments
    ctrl.Rule(
        cost["low"] & usage["frequent"],
        retention["high"]
    ),
    ctrl.Rule(
        cost["high"] & usage["rare"] & importance["low"],
        retention["very_low"]
    ),
    ctrl.Rule(
        cost["high"] & alternatives["good"] & usage["rare"],
        retention["very_low"]
    ),
    ctrl.Rule(
        cost["high"] & alternatives["good"],
        retention["low"]
    ),
    ctrl.Rule(
        cost["high"] & usage["frequent"] & importance["high"],
        retention["high"]
    ),
    ctrl.Rule(
        importance["high"] & alternatives["poor"],
        retention["high"]
    ),

    # Cancellation fee: soften an immediate cancellation decision
    # only when usage and importance are both low.
    ctrl.Rule(
        cancellation_fee["high"]
        & usage["rare"]
        & importance["low"],
        retention["low"]
    ),
]


# --------------------------------------------------
# 4. Create the Mamdani inference system
# --------------------------------------------------

fuzzy_system = ctrl.ControlSystem(rules)


# --------------------------------------------------
# 5. Validate input values
# --------------------------------------------------

def validate_inputs(
    monthly_cost,
    usage_days,
    importance_rating,
    alternative_rating,
    cancellation_fee_amount
):
    values = {
        "Monthly cost": (monthly_cost, 0, 2000),
        "Usage days": (usage_days, 0, 30),
        "Importance": (importance_rating, 0, 10),
        "Alternatives": (alternative_rating, 0, 10),
        "Cancellation fee": (cancellation_fee_amount, 0, 1000),
    }

    for name, (value, minimum, maximum) in values.items():
        if isinstance(value, (bool, np.bool_)):
            raise ValueError(f"{name} must be a number.")

        if not isinstance(value, (int, float, np.integer, np.floating)):
            raise ValueError(f"{name} must be numeric.")

        if not np.isfinite(value):
            raise ValueError(f"{name} must be finite.")

        if not minimum <= value <= maximum:
            raise ValueError(
                f"{name} must be between {minimum} and {maximum}."
            )

    if not float(usage_days).is_integer():
        raise ValueError("Usage days must be a whole number.")


# --------------------------------------------------
# 6. Convert the score into an action
# --------------------------------------------------

def score_to_action(score):
    if 0 <= score < 25:
        return "Cancel"
    elif score < 45:
        return "Downgrade"
    elif score < 65:
        return "Review"
    else:
        return "Keep"


# --------------------------------------------------
# 7. Generate an explanation from the inputs
# --------------------------------------------------

def explain_decision(
    monthly_cost,
    usage_days,
    importance_rating,
    alternative_rating,
    cancellation_fee_amount,
    action
):
    reasons = []

    if monthly_cost >= 1200:
        reasons.append("the monthly cost is high")
    elif monthly_cost <= 250:
        reasons.append("the monthly cost is low")

    if usage_days <= 3:
        reasons.append("usage is rare")
    elif usage_days >= 25:
        reasons.append("usage is frequent")

    if importance_rating <= 3:
        reasons.append("importance is low")
    elif importance_rating >= 8:
        reasons.append("importance is high")

    if alternative_rating >= 8:
        reasons.append("good cheaper alternatives may be available")
    elif alternative_rating <= 2:
        reasons.append("few suitable cheaper alternatives are available")

    if cancellation_fee_amount >= 600:
        reasons.append("the cancellation fee is high")

    if not reasons:
        reasons.append("the inputs contain a mixture of cost and value factors")

    reason_text = "; ".join(reasons)

    messages = {
        "Cancel": "Consider cancelling because " + reason_text + ".",
        "Downgrade": "Consider a cheaper plan because " + reason_text + ".",
        "Review": "Review the subscription and compare available plans because " + reason_text + ".",
        "Keep": "Keeping the subscription may be suitable because " + reason_text + ".",
    }

    return messages[action]


# --------------------------------------------------
# 8. Run the fuzzy inference system
# --------------------------------------------------

def evaluate_subscription(
    monthly_cost,
    usage_days,
    importance_rating,
    alternative_rating,
    cancellation_fee_amount
):
    validate_inputs(
        monthly_cost,
        usage_days,
        importance_rating,
        alternative_rating,
        cancellation_fee_amount
    )

    simulation = ctrl.ControlSystemSimulation(fuzzy_system)

    simulation.input["cost"] = monthly_cost
    simulation.input["usage"] = usage_days
    simulation.input["importance"] = importance_rating
    simulation.input["alternatives"] = alternative_rating
    simulation.input["cancellation_fee"] = cancellation_fee_amount

    try:
        simulation.compute()
        score = float(simulation.output["retention"])
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        raise RuntimeError(
            "The fuzzy system could not calculate a score for these inputs."
        ) from exc

    if not np.isfinite(score):
        raise RuntimeError("The fuzzy system returned an invalid score.")

    action = score_to_action(score)

    explanation = explain_decision(
        monthly_cost,
        usage_days,
        importance_rating,
        alternative_rating,
        cancellation_fee_amount,
        action
    )

    return {
        "score": round(score, 2),
        "action": action,
        "explanation": explanation
    }


# --------------------------------------------------
# 9. Run a sample test when executed directly
# --------------------------------------------------

if __name__ == "__main__":
    result = evaluate_subscription(
        monthly_cost=649,
        usage_days=12,
        importance_rating=8,
        alternative_rating=7,
        cancellation_fee_amount=0
    )

    print("SUBSIGHT - Fuzzy Logic Test")
    print("---------------------------")
    print(f"Retention score: {result['score']}")
    print(f"Recommendation: {result['action']}")
    print(f"Explanation: {result['explanation']}")
