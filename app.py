import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="태양광 금융 시뮬레이션", layout="wide")
st.title("🌞 태양광 금융 시뮬레이션")

# =========================
# 참고용 SMP/REC 단가표(예시)
# =========================
months = [f"{i}월" for i in range(1, 13)]
smp_values = [117.11, 116.39, 113.12, 124.63, 125.50, 118.02, 120.39, 117.39, 112.90, 101.53, 94.81, 90.44]
rec_values = [69.76, 72.16, 72.15, 72.41, 72.39, 71.96, 71.65, 71.86, 71.97, 72.31, 72.14, 72.29]
smp_df = pd.DataFrame({"SMP(원/kWh)": smp_values, "REC(원/kWh)": rec_values}, index=months)

st.subheader("📊 SMP / REC 단가표")
st.caption("참고용(과거 추이)입니다.\n실제 계산은 아래에서 입력한 SMP/REC 단가 1회 값으로 20년 동일 단가로 계산합니다.")
st.dataframe(smp_df.style.format("{:.2f}"), width=420, height=260)

# =========================
# 입력
# =========================
st.header("📝 기본 입력값")

area_unit = st.radio("면적 단위", ["평", "㎡"], horizontal=True)
if area_unit == "평":
    area_py = st.number_input("부지 면적 (평)", value=3000, min_value=1, step=1)
    area_m2 = area_py * 3.3
else:
    area_m2 = st.number_input("부지 면적 (㎡)", value=9900, min_value=1, step=1)
    area_py = area_m2 / 3.3
st.write(f"면적: {area_py:,.0f} 평 (≈ {area_m2:,.0f}㎡)")

plant_type = st.selectbox("발전소 타입", ["노지형", "지붕형"])
if plant_type == "노지형":
    rec_factor = 1.0
    base_area = 3000
    install_cost_per_100kw = 12000
else:
    rec_factor = 1.5
    base_area = 2000
    install_cost_per_100kw = 10000
    st.info(f"지붕형 REC 가중치 적용: REC × {rec_factor}")

capacity_kw = area_py / base_area * 1000
st.write(f"예상 발전용량: {capacity_kw:.0f} kW")

smp_price = st.number_input("SMP 단가 (원/kWh) - 1회 입력(20년 고정)", value=101.16)
rec_price = st.number_input("REC 단가 (원/kWh) - 1회 입력(20년 고정)", value=72.31)

interest_rate = st.number_input("대출 이자율 (%)", value=6.0, min_value=0.0, step=0.1)
operation_years = st.number_input("운영연수 (년)", value=20, min_value=1, step=1)
loan_ratio = st.number_input("대출 비율 (%)", value=80, min_value=0, max_value=100)

st.divider()

# =========================
# 유지보수(O&M) 가정 (입력 없이 문구만)
# =========================
OM_RATE_FIXED = 4.0   # %
OM_INFL_FIXED = 1.0   # % (연 물가 반영)

st.subheader("🛠 유지보수(O&M) 가정")
st.caption(
    f"유지보수비 = 해당 연도 발전매출 × {OM_RATE_FIXED:.1f}%\n"
    f"물가 반영률 {OM_INFL_FIXED:.1f}%를 연차별로 적용합니다."
)

st.divider()

# =========================
# 계산
# =========================
if st.button("계산하기"):
    # 총사업비/대출
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원
    loan_amount = total_install_cost * loan_ratio / 100
    equity_amount = total_install_cost - loan_amount

    st.write(f"💰 총 사업비: {total_install_cost:,.0f} 원")
    st.write(f"🏦 대출금액: {loan_amount:,.0f} 원")
    st.write(f"👤 자기자본(참고): {equity_amount:,.0f} 원")

    r = interest_rate / 100
    remaining_loan = float(loan_amount)

    # 잔여금 누적(= 상환 후 남은 현금 누적)
    cumulative_residual_cash = 0.0

    # 1년차 기준 발전량 (일 평균 발전시간 3.6h 가정)
    base_annual_gen_kwh = capacity_kw * 3.6 * 365

    results = []
    last_repayment_won = 0.0
    last_maintenance_won = 0.0
    last_revenue_won = 0.0
    last_residual_won = 0.0
    last_net_position_won = 0.0

    for year in range(1, int(operation_years) + 1):
        # 발전효율(연 0.4% 저하)
        efficiency = 1 - 0.004 * (year - 1)
        annual_gen_kwh = base_annual_gen_kwh * efficiency

        # 발전금(원)
        annual_revenue_won = annual_gen_kwh * (smp_price + rec_price * rec_factor)

        # 유지비(원): 매출 × 4% × 물가
        maintenance_won = annual_revenue_won * (OM_RATE_FIXED / 100) * ((1 + OM_INFL_FIXED / 100) ** (year - 1))

        # 운영단 순이익(원) = 매출 - 유지비
        operating_profit_won = annual_revenue_won - maintenance_won

        # 이자(원)
        interest_due_won = remaining_loan * r if remaining_loan > 0 else 0.0

        # 상환 로직: 1년차 이자만, 2년차부터 이자→원금(가능한 범위)
        if year == 1:
            paid_interest_won = min(max(operating_profit_won, 0.0), interest_due_won)
            principal_payment_won = 0.0
        else:
            paid_interest_won = min(max(operating_profit_won, 0.0), interest_due_won)
            remaining_cash_after_interest = operating_profit_won - paid_interest_won
            principal_payment_won = min(max(remaining_cash_after_interest, 0.0), remaining_loan)

        repayment_won = paid_interest_won + principal_payment_won
        remaining_loan = max(remaining_loan - principal_payment_won, 0.0)

        # 잔여금 = 발전금 - 유지비 - 상환금
        residual_cash_won = annual_revenue_won - maintenance_won - repayment_won

        # 누적 = (잔여금 누적) - (남은 대출원금)
        cumulative_residual_cash += residual_cash_won
        net_position_won = cumulative_residual_cash - remaining_loan

        results.append({
            "연차": year,
            "발전금": int(round(annual_revenue_won / 10_000)),
            "상환금": int(round(repayment_won / 10_000)),
            "유지비": int(round(maintenance_won / 10_000)),
            "잔여금": int(round(residual_cash_won / 10_000)),
            "누적": int(round(net_position_won / 10_000)),
        })

        last_revenue_won = annual_revenue_won
        last_maintenance_won = maintenance_won
        last_repayment_won = repayment_won
        last_residual_won = residual_cash_won
        last_net_position_won = net_position_won

    df = pd.DataFrame(results)

    # =========================
    # KPI 요약 박스
    # =========================
    st.subheader("📌 요약(마지막 연차 기준)")
    c1, c2, c3 = st.columns(3)
    c1.metric("잔여 대출원금(만원)", f"{int(round(remaining_loan / 10_000)):,}")
    c2.metric("잔여금 누적(만원)", f"{int(round(cumulative_residual_cash / 10_000)):,}")
    c3.metric("누적(만원)", f"{int(round(last_net_position_won / 10_000)):,}")

    # =========================
    # 표
    # =========================
    def color_neg_red(v):
        return "color: red" if v < 0 else "color: black"

    st.subheader("📈 연차별 누적 수익금")
    st.caption(
        "단위: 만 원\n"
        "누적 = 잔여금 누적 - 남은 대출원금"
    )

    styler = (
        df.style
        .applymap(color_neg_red, subset=["누적"])
        .format("{:,}")
        .set_table_styles(
            [
                {"selector": "th.row_heading", "props": [("display", "none")]},  # 왼쪽 index
                {"selector": "th.blank", "props": [("display", "none")]},        # 좌상단 빈칸
            ],
            overwrite=False,
        )
    )

    st.dataframe(styler, use_container_width=True)

    # 흑자 전환 연차 찾기(누적 >= 0)
    pos_array = np.array(df["누적"])
    payback_idx = next((i for i, v in enumerate(pos_array) if v >= 0), None)
    if payback_idx is not None:
        st.success(f"✅ 누적 흑자 전환 시점: {int(df.loc[payback_idx, '연차'])}년차")
    else:
        st.warning("❗ 운영연수 내 누적 흑자 전환 불가")
