import pytest

from fuzzy_engine import evaluate_subscription, score_to_action
from baseline import evaluate_baseline
from savings import calculate_savings


def test_fuzzy_returns_valid_score_and_action():
    result = evaluate_subscription(649, 12, 8, 7, 0)

    assert 0 <= result["score"] <= 100
    assert result["action"] in {"Keep", "Review", "Downgrade", "Cancel"}
    assert result["explanation"]


def test_baseline_returns_valid_score_and_action():
    result = evaluate_baseline(649, 12, 8, 7, 0)

    assert 0 <= result["score"] <= 100
    assert result["action"] in {"Keep", "Review", "Downgrade", "Cancel"}


@pytest.mark.parametrize(
    "score, expected",
    [
        (0, "Cancel"),
        (24.99, "Cancel"),
        (25, "Downgrade"),
        (44.99, "Downgrade"),
        (45, "Review"),
        (64.99, "Review"),
        (65, "Keep"),
        (100, "Keep"),
    ],
)
def test_score_thresholds(score, expected):
    assert score_to_action(score) == expected


@pytest.mark.parametrize(
    "inputs",
    [
        (-1, 10, 5, 5, 0),
        (2001, 10, 5, 5, 0),
        (100, 31, 5, 5, 0),
        (100, 10, 11, 5, 0),
        (100, 10, 5, -1, 0),
        (100, 10, 5, 5, 1001),
    ],
)
def test_fuzzy_rejects_out_of_range_inputs(inputs):
    with pytest.raises(ValueError):
        evaluate_subscription(*inputs)


def test_cancel_savings_subtracts_one_time_fee():
    result = calculate_savings(
        monthly_cost=649,
        action="Cancel",
        cancellation_fee=100,
        action_confirmed=True,
    )

    assert result["gross_monthly_savings"] == 649
    assert result["gross_yearly_savings"] == 7788
    assert result["first_year_net_savings"] == 7688


def test_unconfirmed_action_does_not_claim_savings():
    result = calculate_savings(
        monthly_cost=649,
        action="Cancel",
        cancellation_fee=100,
        action_confirmed=False,
    )

    assert result["gross_monthly_savings"] == 0
    assert result["gross_yearly_savings"] == 0
    assert result["first_year_net_savings"] == 0


def test_downgrade_requires_cheaper_plan_price():
    with pytest.raises(ValueError):
        calculate_savings(
            monthly_cost=649,
            action="Downgrade",
            action_confirmed=True,
        )


def test_downgrade_savings():
    result = calculate_savings(
        monthly_cost=649,
        action="Downgrade",
        cheaper_plan_monthly=299,
        action_confirmed=True,
    )

    assert result["gross_monthly_savings"] == 350
    assert result["gross_yearly_savings"] == 4200
    assert result["first_year_net_savings"] == 4200
