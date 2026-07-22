"""50代からの未来設計シミュレーター."""
from __future__ import annotations

from dataclasses import dataclass


APP_NAME = "50代からの未来設計シミュレーター"
APP_SUBTITLE = "老後資金の見通しを、数字でやさしく確認"


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


def parse_yen_input(value: str) -> int:
    """Convert a Japanese yen text input into an integer amount.

    Commas, regular spaces, full-width spaces, and the yen symbol are accepted.
    Empty input is treated as zero. Other characters raise a Japanese error.
    """
    cleaned = (
        str(value)
        .replace(",", "")
        .replace("円", "")
        .replace("¥", "")
        .replace(" ", "")
        .replace("　", "")
    )

    if cleaned == "":
        return 0
    if not cleaned.isdigit():
        raise ValueError("金額は数字、カンマ、空白、円記号だけで入力してください。")
    return int(cleaned)


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


def set_default_inputs() -> None:
    import streamlit as st

    defaults = {
        "current_age": 55,
        "current_assets_text": yen(10_000_000),
        "monthly_contribution_text": yen(50_000),
        "annual_return_percent": 3.0,
        "retirement_age": 65,
        "monthly_living_expenses_text": yen(280_000),
        "monthly_pension_income_text": yen(180_000),
        "final_age": 95,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def apply_design() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        html, body, .stApp { max-width: 100%; overflow-x: clip; }
        .stApp { background: linear-gradient(180deg, #f5fbff 0%, #ffffff 45%); }
        h1, h2, h3 { color: #164e63; max-width: 100%; white-space: normal; overflow-wrap: anywhere; word-break: normal; }
        p, label, div, span { font-size: 1.05rem; line-height: 1.7; max-width: 100%; white-space: normal; overflow-wrap: anywhere; }
        .app-title {
            color: #164e63;
            font-size: clamp(1.8rem, 5.8vw, 2.4rem);
            font-weight: 800;
            line-height: 1.25;
            letter-spacing: 0.01em;
            max-width: 100%;
            white-space: normal;
            overflow-wrap: anywhere;
            word-break: normal;
        }
        .app-subtitle {
            color: #0f766e;
            font-size: clamp(1rem, 3.6vw, 1.15rem);
            font-weight: 650;
            line-height: 1.6;
            margin-top: 0.25rem;
            max-width: 100%;
            white-space: normal;
            overflow-wrap: anywhere;
            word-break: normal;
        }
        .page-title {
            color: #164e63;
            font-size: clamp(1.5rem, 4.8vw, 1.8rem);
            font-weight: 750;
            line-height: 1.35;
            margin: 1.4rem 0 1rem;
            max-width: 100%;
            white-space: normal;
            overflow-wrap: anywhere;
            word-break: normal;
        }
        [data-testid="stMetricValue"] { color: #0f766e; font-size: clamp(1.35rem, 4.8vw, 1.75rem); }
        .block-container { max-width: 980px; padding-top: 2rem; padding-bottom: 3rem; overflow-x: clip; }
        .notice { padding: 1rem; border-radius: 0.9rem; background: #ecfeff; border: 1px solid #a5f3fc; margin: 0.75rem 0; }
        .warning { padding: 1rem; border-radius: 0.9rem; background: #fff7ed; border: 1px solid #fed7aa; margin: 0.75rem 0; }
        .step-card { padding: 1.1rem; border-radius: 1rem; background: #ffffff; border: 1px solid #dbeafe; box-shadow: 0 1px 6px rgba(15, 76, 117, 0.08); }
        @media (max-width: 640px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .app-title { line-height: 1.3; }
            .page-title { line-height: 1.35; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(page_title: str) -> None:
    import streamlit as st

    st.markdown(f'<div class="app-title">{APP_NAME}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="app-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-title">{page_title}</div>', unsafe_allow_html=True)


def intro_page() -> None:
    import streamlit as st

    apply_design()
    page_header("1. はじめに")
    st.markdown(
        '<div class="step-card">これからの資産がどのように変化しそうか、かんたんな条件で確認できる教育目的のシミュレーターです。</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="notice">このシミュレーターは教育目的の概算です。金融助言ではなく、結果を保証するものではありません。</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="notice">入力内容は保存されません。安心して目安の確認にご利用ください。</div>',
        unsafe_allow_html=True,
    )
    if st.button("シミュレーションを始める", type="primary", use_container_width=True):
        st.switch_page(INPUT_PAGE)


def input_page() -> None:
    import streamlit as st

    set_default_inputs()
    apply_design()
    page_header("2. 条件を入力")
    st.caption("条件を入力して、次のページで結果を確認します。")

    with st.form("input_form"):
        age_col1, age_col2 = st.columns(2)
        with age_col1:
            current_age = st.number_input("現在の年齢", 50, 80, st.session_state.current_age, help="今日時点のおおよその年齢を入力してください。")
            retirement_age = st.number_input("退職予定年齢", current_age, 90, max(st.session_state.retirement_age, current_age), help="積立をやめ、老後生活費を取り崩し始める年齢です。")
        with age_col2:
            annual_return_percent = st.number_input("想定する年利（%）", -10.0, 20.0, st.session_state.annual_return_percent, step=0.5, help="資産運用で期待する1年あたりの増減率です。高すぎる設定に注意してください。")
            final_age = st.number_input("シミュレーション終了年齢", retirement_age, 110, max(st.session_state.final_age, retirement_age), help="退職予定年齢以降で、何歳まで資産推移を確認するかを選びます。")

        st.markdown("### 金額")
        money_col1, money_col2 = st.columns(2)
        with money_col1:
            current_assets_text = st.text_input("現在の金融資産（円）", st.session_state.current_assets_text, help="例：10,000,000円。預貯金や投資信託など、老後資金として考える資産の合計です。")
            monthly_contribution_text = st.text_input("退職前の毎月の積立額（円）", st.session_state.monthly_contribution_text, help="例：50,000円。退職するまで毎月追加できそうな金額です。")
        with money_col2:
            monthly_living_expenses_text = st.text_input("退職後の毎月の生活費（円）", st.session_state.monthly_living_expenses_text, help="例：280,000円。住居費、食費、医療費、趣味などを含めた毎月の支出見込みです。")
            monthly_pension_income_text = st.text_input("退職後の毎月の年金収入（円）", st.session_state.monthly_pension_income_text, help="例：180,000円。公的年金など、退職後に毎月受け取る見込み額です。")

        submitted = st.form_submit_button("結果を見る", type="primary", use_container_width=True)

    if submitted:
        try:
            current_assets = parse_yen_input(current_assets_text)
            monthly_contribution = parse_yen_input(monthly_contribution_text)
            monthly_living_expenses = parse_yen_input(monthly_living_expenses_text)
            monthly_pension_income = parse_yen_input(monthly_pension_income_text)
            simulate_assets(current_age, current_assets, monthly_contribution, annual_return_percent, retirement_age, monthly_living_expenses, monthly_pension_income, final_age)
        except ValueError as error:
            st.error(str(error))
            st.stop()

        st.session_state.current_age = current_age
        st.session_state.current_assets_text = yen(current_assets)
        st.session_state.monthly_contribution_text = yen(monthly_contribution)
        st.session_state.annual_return_percent = annual_return_percent
        st.session_state.retirement_age = retirement_age
        st.session_state.monthly_living_expenses_text = yen(monthly_living_expenses)
        st.session_state.monthly_pension_income_text = yen(monthly_pension_income)
        st.session_state.final_age = final_age
        st.switch_page(RESULT_PAGE)

    if annual_return_percent >= 7:
        st.markdown('<div class="warning">想定利回りが高めです。将来の運用成果は変動するため、現実的な範囲で複数のケースを確認しましょう。</div>', unsafe_allow_html=True)


def result_page() -> None:
    import pandas as pd
    import streamlit as st

    set_default_inputs()
    apply_design()
    page_header("3. 結果")
    st.caption("入力条件にもとづく概算結果です。")

    try:
        current_assets = parse_yen_input(st.session_state.current_assets_text)
        monthly_contribution = parse_yen_input(st.session_state.monthly_contribution_text)
        monthly_living_expenses = parse_yen_input(st.session_state.monthly_living_expenses_text)
        monthly_pension_income = parse_yen_input(st.session_state.monthly_pension_income_text)
        result = simulate_assets(st.session_state.current_age, current_assets, monthly_contribution, st.session_state.annual_return_percent, st.session_state.retirement_age, monthly_living_expenses, monthly_pension_income, st.session_state.final_age)
    except ValueError as error:
        st.error(str(error))
        if st.button("条件を変更する", use_container_width=True):
            st.switch_page(INPUT_PAGE)
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

    st.subheader("計算の前提と注意事項")
    st.info("税金、社会保険料、物価上昇、退職金、夫婦での計算などは含めていません。このシミュレーターは教育目的の概算であり、金融助言ではありません。結果は保証されません。")
    if st.session_state.annual_return_percent >= 7:
        st.markdown('<div class="warning">想定利回りが高めです。将来の運用成果は変動するため、現実的な範囲で複数のケースを確認しましょう。</div>', unsafe_allow_html=True)

    if st.button("条件を変更する", use_container_width=True):
        st.switch_page(INPUT_PAGE)


def main() -> None:
    import streamlit as st

    if INTRO_PAGE is None or INPUT_PAGE is None or RESULT_PAGE is None:
        configure_pages()

    st.set_page_config(
        page_title=APP_NAME,
        page_icon="🌿",
        layout="wide",
    )
    set_default_inputs()
    page = st.navigation([INTRO_PAGE, INPUT_PAGE, RESULT_PAGE])
    page.run()


INTRO_PAGE = None
INPUT_PAGE = None
RESULT_PAGE = None


def configure_pages() -> None:
    import streamlit as st

    global INTRO_PAGE, INPUT_PAGE, RESULT_PAGE
    INTRO_PAGE = st.Page(intro_page, title="はじめに", icon="🌿")
    INPUT_PAGE = st.Page(input_page, title="条件を入力", icon="📝")
    RESULT_PAGE = st.Page(result_page, title="結果", icon="📈")


if __name__ == "__main__":
    main()
