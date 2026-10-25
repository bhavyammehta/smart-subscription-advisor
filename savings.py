
def calculate_savings(
    monthly_cost,
    action,
    cancellation_fee=0,
    cheaper_plan_monthly=None,
    action_confirmed=False,
):
    """Calculate estimated savings for a proposed subscription action.

    Savings are zero unless the user confirms the proposed action.
    Cancellation fees are treated as one-time costs.
    """

    if action not in {"Keep", "Review", "Downgrade", "Cancel"}:
        raise ValueError("Invalid recommendation action.")

    values = {
        "Monthly cost": monthly_cost,
        "Cancellation fee": cancellation_fee,
    }

    if cheaper_plan_monthly is not None:
        values["Cheaper plan monthly cost"] = cheaper_plan_monthly

    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be numeric.")
        if value < 0:
            raise ValueError(f"{name} cannot be negative.")

    if action == "Downgrade" and cheaper_plan_monthly is None:
        raise ValueError(
            "Enter the cheaper plan price to calculate downgrade savings."
        )

    if (
        action == "Downgrade"
        and cheaper_plan_monthly > monthly_cost
    ):
        raise ValueError(
            "The cheaper plan price must not exceed the current price."
        )

    if not action_confirmed or action in {"Keep", "Review"}:
        gross_monthly = 0.0
        gross_yearly = 0.0
        fee_adjusted_first_year = 0.0

    elif action == "Cancel":
        gross_monthly = float(monthly_cost)
        gross_yearly = gross_monthly * 12
        fee_adjusted_first_year = gross_yearly - cancellation_fee

    else:  # Confirmed downgrade
        gross_monthly = (
            float(monthly_cost) - float(cheaper_plan_monthly)
        )
        gross_yearly = gross_monthly * 12
        fee_adjusted_first_year = gross_yearly

    return {
        "gross_monthly_savings": round(gross_monthly, 2),
        "gross_yearly_savings": round(gross_yearly, 2),
        "first_year_net_savings": round(
            fee_adjusted_first_year, 2
        ),
        "action_confirmed": action_confirmed,
    }


if __name__ == "__main__":
    result = calculate_savings(
        monthly_cost=649,
        action="Cancel",
        cancellation_fee=100,
        action_confirmed=True,
    )

    print("SUBSIGHT - Savings Test")
    print("-----------------------")
    print(f"Gross monthly savings: ₹{result['gross_monthly_savings']:.2f}")
    print(f"Gross yearly savings: ₹{result['gross_yearly_savings']:.2f}")
    print(f"First-year net savings: ₹{result['first_year_net_savings']:.2f}")

