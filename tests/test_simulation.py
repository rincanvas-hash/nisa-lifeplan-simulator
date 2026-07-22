import pytest

from app import APP_NAME, APP_SUBTITLE, parse_yen_input, simulate_assets, yen


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


def test_final_age_must_be_retirement_age_or_later():
    with pytest.raises(ValueError, match="シミュレーション終了年齢は退職予定年齢以上"):
        simulate_assets(55, 1_000_000, 10_000, 3, 65, 200_000, 150_000, 64)


def test_yen_format():
    assert yen(1234567) == "1,234,567円"


def test_parse_yen_input_accepts_commas_and_symbols():
    assert parse_yen_input(" 1,234,567 円") == 1_234_567
    assert parse_yen_input("¥50,000") == 50_000


def test_parse_yen_input_treats_blank_as_zero():
    assert parse_yen_input("") == 0
    assert parse_yen_input(" 　") == 0


def test_parse_yen_input_rejects_invalid_characters():
    with pytest.raises(ValueError, match="金額は数字、カンマ、空白、円記号だけ"):
        parse_yen_input("10万円")


def test_branding_uses_future_design_name():
    assert APP_NAME == "50代からの未来設計シミュレーター"
    assert APP_SUBTITLE == "老後資金の見通しを、数字でやさしく確認"
