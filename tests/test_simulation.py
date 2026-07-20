import pytest

from app import simulate_assets, yen


def test_simulation_before_and_after_retirement():
    result = simulate_assets(
        current_age=60,
        current_assets=10_000_000,
        monthly_contribution=50_000,
        annual_return_percent=0,
        retirement_age=65,
        monthly_living_expenses=250_000,
        monthly_pension_income=150_000,
        final_age=66,
    )

    assert result.assets_at_retirement == 13_000_000
    assert result.monthly_shortfall == 100_000
    assert result.final_assets == 10_600_000
    assert result.depletion_age is None
    assert len(result.annual_rows) == 7


def test_assets_never_display_negative_and_depletion_age_is_recorded():
    result = simulate_assets(65, 500_000, 0, 0, 65, 300_000, 0, 70)

    assert result.depletion_age == 65
    assert all(row["資産残高"] >= 0 for row in result.annual_rows)
    assert result.final_assets == 0


def test_invalid_age_order_raises_error():
    with pytest.raises(ValueError):
        simulate_assets(80, 1_000_000, 0, 0, 65, 100_000, 100_000, 90)


def test_yen_format():
    assert yen(1234567) == "1,234,567円"
