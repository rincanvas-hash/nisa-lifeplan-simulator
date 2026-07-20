"""50代からの老後資金かんたんシミュレーター."""
from __future__ import annotations

from dataclasses import dataclass



@dataclass(frozen=True)
class SimulationResult:
    annual_rows: list[dict[str, int | float]]
    assets_at_retirement: float
    monthly_shortfall: float
    depletion_age: int | None
    final_assets: float


def yen(value: float) -> str:
    """Format a number as Japanese yen."""
    return f"{round(value):,}円"


def simulate_assets(
    current_age: int,
    current_assets: float,
    monthly_contribution: float,
    annual_return_percent: float,
    retirement_age: int,
    monthly_living_expenses: float,
    monthly_pension_income: float,
    final_age: int,
) -> SimulationResult:
    """Calculate projected asset balances by age for the MVP simulator.

    The model applies the selected annual return once per age and then applies
    either annual contributions before retirement or annual withdrawals after
    retirement. Balances are floored at zero for display and downstream results.
    """
    if current_age > final_age:
        raise ValueError("現在の年齢はシミュレーション終了年齢以下にしてください。")
    if retirement_age < current_age:
        raise ValueError("退職予定年齢は現在の年齢以上にしてください。")
    if final_age < retirement_age:
        raise ValueError("シミュレーション終了年齢は退職予定年齢以上にしてください。")
    if annual_return_percent < -100:
        raise ValueError("想定利回りは-100%以上にしてください。")

    assets = max(float(current_assets), 0.0)
    annual_return_rate = annual_return_percent / 100
    annual_contribution = max(float(monthly_contribution), 0.0) * 12
    monthly_shortfall = max(float(monthly_living_expenses) - float(monthly_pension_income), 0.0)
    annual_shortfall = monthly_shortfall * 12

    annual_rows: list[dict[str, int | float]] = []
    assets_at_retirement: float | None = assets if current_age >= retirement_age else None
    depletion_age: int | None = None

    for age in range(current_age, final_age + 1):
        if assets > 0:
            assets *= 1 + annual_return_rate

        if age < retirement_age:
            assets += annual_contribution
        else:
            if assets_at_retirement is None:
                assets_at_retirement = assets
            assets -= annual_shortfall

        if assets <= 0:
            assets = 0.0
            if age >= retirement_age and depletion_age is None:
                depletion_age = age

        annual_rows.append({"年齢": age, "資産残高": round(assets)})

    return SimulationResult(
        annual_rows=annual_rows,
        assets_at_retirement=max(assets_at_retirement or 0.0, 0.0),
        monthly_shortfall=monthly_shortfall,
        depletion_age=depletion_age,
        final_assets=annual_rows[-1]["資産残高"] if annual_rows else 0.0,
    )


def main() -> None:
    import pandas as pd
    import streamlit as st

    st.set_page_config(
        page_title="50代からの老後資金かんたんシミュレーター",
        page_icon="🌿",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(180deg, #f5fbff 0%, #ffffff 45%); }
        h1, h2, h3 { color: #164e63; }
        p, label, div, span { font-size: 1.04rem; }
        [data-testid="stMetricValue"] { color: #0f766e; font-size: 1.8rem; }
        .notice { padding: 1rem; border-radius: 0.9rem; background: #ecfeff; border: 1px solid #a5f3fc; }
        .warning { padding: 1rem; border-radius: 0.9rem; background: #fff7ed; border: 1px solid #fed7aa; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("50代からの老後資金かんたんシミュレーター")
    st.markdown(
        '<div class="notice">現在の資産や毎月の積立額、年金見込み額を入力すると、将来の資産残高の目安を確認できます。入力内容は保存されません。</div>',
        unsafe_allow_html=True,
    )
    st.caption("このシミュレーターは教育目的の概算です。金融助言ではなく、結果を保証するものではありません。")

    with st.sidebar:
        st.header("入力してください")
        current_age = st.number_input("現在の年齢", 50, 80, 55, help="今日時点のおおよその年齢を入力してください。")
        current_assets = st.number_input("現在の金融資産（円）", 0, 500_000_000, 10_000_000, step=500_000, help="預貯金や投資信託など、老後資金として考える資産の合計です。")
        monthly_contribution = st.number_input("退職前の毎月の積立額（円）", 0, 1_000_000, 50_000, step=10_000, help="退職するまで毎月追加できそうな金額です。")
        annual_return_percent = st.number_input("想定する年利（%）", -10.0, 20.0, 3.0, step=0.5, help="資産運用で期待する1年あたりの増減率です。高すぎる設定に注意してください。")
        retirement_age = st.number_input("退職予定年齢", current_age, 90, 65, help="積立をやめ、老後生活費を取り崩し始める年齢です。")
        monthly_living_expenses = st.number_input("退職後の毎月の生活費（円）", 0, 2_000_000, 280_000, step=10_000, help="住居費、食費、医療費、趣味などを含めた毎月の支出見込みです。")
        monthly_pension_income = st.number_input("退職後の毎月の年金収入（円）", 0, 2_000_000, 180_000, step=10_000, help="公的年金など、退職後に毎月受け取る見込み額です。")
        final_age = st.number_input("シミュレーション終了年齢", retirement_age, 110, max(95, retirement_age), help="退職予定年齢以降で、何歳まで資産推移を確認するかを選びます。")

    if annual_return_percent >= 7:
        st.markdown('<div class="warning">想定利回りが高めです。将来の運用成果は変動するため、現実的な範囲で複数のケースを確認しましょう。</div>', unsafe_allow_html=True)

    try:
        result = simulate_assets(current_age, current_assets, monthly_contribution, annual_return_percent, retirement_age, monthly_living_expenses, monthly_pension_income, final_age)
    except ValueError as error:
        st.error(str(error))
        st.stop()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("退職時の推定資産", yen(result.assets_at_retirement))
    col2.metric("退職後の毎月不足額", yen(result.monthly_shortfall))
    col3.metric("資産がなくなる推定年齢", f"{result.depletion_age}歳" if result.depletion_age else "期間内は残る")
    col4.metric("終了年齢での推定資産", yen(result.final_assets))

    df = pd.DataFrame(result.annual_rows)
    st.subheader("年齢ごとの資産残高")
    st.line_chart(df.set_index("年齢"), height=360)

    st.subheader("かんたん年間結果表")
    display_df = df.copy()
    display_df["資産残高"] = display_df["資産残高"].map(yen)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.info("注意：税金、社会保険料、物価上昇、退職金、夫婦での計算などは含めていません。実際の計画は専門家にも相談してください。")


if __name__ == "__main__":
    main()
