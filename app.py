"""50代からの未来設計シミュレーター."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


APP_DIR = Path(__file__).parent


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


def man_yen_to_yen(value: float) -> int:
    """Convert an amount expressed in ten-thousand yen to yen."""
    return round(value * 10_000)


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
    """Calculate projected asset balances by age."""
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


DEFAULTS = {
    "page": 1,
    "current_age": 55,
    "current_assets_man": 1000,
    "monthly_contribution_man": 5,
    "annual_return_percent": 3.0,
    "retirement_age": 65,
    "monthly_living_expenses_man": 28,
    "monthly_pension_income_man": 18,
    "final_age": 95,
}


def main() -> None:
    import pandas as pd
    import streamlit as st

    st.set_page_config(page_title="50代からの未来設計シミュレーター", page_icon="🌿", layout="wide")
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(155deg, #f1fbf6 0%, #fffdf7 55%, #eef8ff 100%); }
        .block-container { max-width: 1120px; padding-top: 2rem; }
        h1, h2, h3 { color: #174c42; }
        .step { color:#39796c; font-weight:700; letter-spacing:.08em; }
        .bubble { position:relative; padding:1.1rem 1.25rem; border-radius:1.2rem;
          background:white; border:2px solid #b9e0d3; box-shadow:0 5px 16px #174c421c; }
        .bubble:before { content:""; position:absolute; left:-14px; top:36px; border-width:10px 14px 10px 0;
          border-style:solid; border-color:transparent #b9e0d3 transparent transparent; }
        .guide img { max-height:245px; object-fit:contain; }
        [data-testid="stMetric"] { background:#fff; border:1px solid #d9ebe5; padding:1rem; border-radius:1rem; box-shadow:0 4px 12px #174c4212; }
        [data-testid="stMetricValue"] { color:#087f68; }
        .stButton > button { border:0; border-radius:999px; font-weight:700; padding:.7rem 1.5rem;
          background:linear-gradient(#35ad88,#148067); color:white; box-shadow:0 6px 0 #0d5d4c,0 10px 18px #174c4233; }
        .stButton > button:active { transform:translateY(4px); box-shadow:0 2px 0 #0d5d4c; }
        .yen-note { color:#526b65; font-size:.9rem; margin-top:-.65rem; margin-bottom:.5rem; }
        @media(max-width: 700px) {
          .block-container { padding:1rem .9rem 2rem; } h1 { font-size:1.75rem!important; }
          .guide img { max-height:165px; } .bubble:before { display:none; }
          [data-testid="stHorizontalBlock"] { gap:.5rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("50代からの未来設計シミュレーター")
    st.progress(st.session_state.page / 3, text=f"STEP {st.session_state.page} / 3")

    if st.session_state.page == 1:
        render_intro(st)
    elif st.session_state.page == 2:
        render_input(st)
    else:
        render_result(st, pd)


def guide(st, image_name: str, message: str) -> None:
    """Render the responsive guide character and speech bubble."""
    image_col, message_col = st.columns([1, 2.3], vertical_alignment="center")
    with image_col:
        st.markdown('<div class="guide">', unsafe_allow_html=True)
        st.image(str(APP_DIR / image_name), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with message_col:
        st.markdown(f'<div class="bubble">{message}</div>', unsafe_allow_html=True)


def go_to(st, page: int) -> None:
    st.session_state.page = page


def render_intro(st) -> None:
    st.markdown('<div class="step">STEP 1　はじめに</div>', unsafe_allow_html=True)
    guide(st, "guide_intro.png", "こんにちは！ これからの暮らしと資産を、3つのステップで一緒に見通してみましょう。")
    st.subheader("未来のお金を、わかりやすく見える化")
    st.write("今の資産や積立、退職後の生活費などを入力すると、年齢ごとの資産推移を概算します。入力内容はこのブラウザの操作中だけ保持されます。")
    st.caption("教育目的の概算であり、金融助言や将来の成果を保証するものではありません。")
    st.button("入力をはじめる →", type="primary", use_container_width=True, on_click=go_to, args=(st, 2))


def money_input(st, label: str, key: str, maximum: int, help_text: str) -> None:
    st.number_input(label, min_value=0, max_value=maximum, step=1, key=key, help=help_text)
    st.markdown(f'<div class="yen-note">円換算：{yen(man_yen_to_yen(st.session_state[key]))}</div>', unsafe_allow_html=True)


def render_input(st) -> None:
    st.markdown('<div class="step">STEP 2　条件を入力</div>', unsafe_allow_html=True)
    guide(st, "guide_input.png", "金額はすべて「万円」単位です。＋／－ボタンでも気軽に調整できますよ。")
    left, right = st.columns(2)
    with left:
        st.number_input("現在の年齢", 50, 80, key="current_age")
        money_input(st, "現在の金融資産（万円）", "current_assets_man", 50_000, "預貯金や投資信託などの合計")
        money_input(st, "退職前の毎月の積立額（万円）", "monthly_contribution_man", 100, "退職まで毎月積み立てる金額")
        st.number_input("想定する年利（%）", -10.0, 20.0, step=0.5, key="annual_return_percent")
    with right:
        st.number_input("退職予定年齢", min_value=st.session_state.current_age, max_value=90, key="retirement_age")
        money_input(st, "退職後の毎月の生活費（万円）", "monthly_living_expenses_man", 200, "住居費、食費、医療費など")
        money_input(st, "退職後の毎月の年金収入（万円）", "monthly_pension_income_man", 200, "公的年金などの見込み額")
        st.number_input("シミュレーション終了年齢", min_value=st.session_state.retirement_age, max_value=110, key="final_age")
    back, forward = st.columns(2)
    back.button("← 戻る", use_container_width=True, on_click=go_to, args=(st, 1))
    forward.button("結果を見る →", type="primary", use_container_width=True, on_click=go_to, args=(st, 3))


def render_result(st, pd) -> None:
    st.markdown('<div class="step">STEP 3　シミュレーション結果</div>', unsafe_allow_html=True)
    guide(st, "guide_result.png", "結果が出ました！ 4つのポイントとグラフを見ながら、無理のない未来設計を考えましょう。")
    result = simulate_assets(
        st.session_state.current_age,
        man_yen_to_yen(st.session_state.current_assets_man),
        man_yen_to_yen(st.session_state.monthly_contribution_man),
        st.session_state.annual_return_percent,
        st.session_state.retirement_age,
        man_yen_to_yen(st.session_state.monthly_living_expenses_man),
        man_yen_to_yen(st.session_state.monthly_pension_income_man),
        st.session_state.final_age,
    )
    columns = st.columns(4)
    columns[0].metric("退職時の推定資産", yen(result.assets_at_retirement))
    columns[1].metric("退職後の毎月不足額", yen(result.monthly_shortfall))
    columns[2].metric("資産がなくなる推定年齢", f"{result.depletion_age}歳" if result.depletion_age else "期間内は残る")
    columns[3].metric("終了年齢での推定資産", yen(result.final_assets))
    df = pd.DataFrame(result.annual_rows)
    st.subheader("資産推移グラフ")
    st.line_chart(df.set_index("年齢"), height=360)
    st.subheader("年間結果表")
    display_df = df.copy()
    display_df["資産残高"] = display_df["資産残高"].map(yen)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.caption("税金、社会保険料、物価上昇、退職金などは含みません。実際の計画は専門家にもご相談ください。")
    st.button("← 条件を見直す", use_container_width=True, on_click=go_to, args=(st, 2))


if __name__ == "__main__":
    main()
