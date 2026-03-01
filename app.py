import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="태양광 금융 시뮬레이션", layout="wide")
st.title("🌞 태양광 금융 시뮬레이션")

# =========================
# 참고용 SMP/REC 단가표
# =========================
months = [f"{i}월" for i in range(1, 13)]
smp_values = [117.11, 116.39, 113.12, 124.63, 125.50, 118.02, 120.39, 117.39, 112.90, 101.53, 94.81, 90.44]
rec_values = [69.76, 72.16, 72.15, 72.41, 72.39, 71.96, 71.65, 71.86, 71.97, 72.31, 72.14, 72.29]
smp_df = pd.DataFrame({"SMP(원/kWh)": smp_values, "REC(원/kWh)": rec_values}, index=months)

st.subheader("📊 SMP / REC 단가표")
st.caption("참고용(과거 추이)입니다.\n실제 계산은 아래 입력 단가 1회 값으로 20년 동일 단가로 계산합니다.")
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

smp_price = st.number_input("SMP 단가 (원/kWh)", value=101.16)
rec_price = st.number_input("REC 단가 (원/kWh)", value=72.31)
interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
operation_years = st.number_input("운영연수 (년)", value=20, min_value=1)
loan_ratio = st.number_input("대출 비율 (%)", value=80, min_value=0, max_value=100)

st.divider()

# =========================
# 유지보수 가정 (입력 없음)
# =========================
OM_RATE = 4.0
OM_INFL = 1.0

st.subheader("🛠 유지보수(O&M) 가정")
st.caption(
    f"유지보수비 = 해당 연도 발전매출 × {OM_RATE:.1f}%\n"
    f"물가 반영률 {OM_INFL:.1f}%를 연차별 적용"
)

st.divider()

# =========================
# 계산
# =========================
if st.button("계산하기"):

    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000
    loan_amount = total_install_cost * loan_ratio / 100
    equity_amount = total_install_cost - loan_amount

    st.write(f"💰 총 사업비: {total_install_cost:,.0f} 원")
    st.write(f"🏦 대출금액: {loan_amount:,.0f} 원")
    st.write(f"👤 자기자본(참고): {equity_amount:,.0f} 원")

    r = interest_rate / 100
    remaining_loan = float(loan_amount)
    cumulative_residual_cash = 0.0

    base_annual_gen = capacity_kw * 3.6 * 365

    results = []

    for year in range(1, int(operation_years) + 1):

        efficiency = 1 - 0.004 * (year - 1)
        annual_gen = base_annual_gen * efficiency
        annual_revenue = annual_gen * (smp_price + rec_price * rec_factor)

        maintenance = annual_revenue * (OM_RATE / 100) * ((1 + OM_INFL / 100) ** (year - 1))
        operating_profit = annual_revenue - maintenance

        interest_due = remaining_loan * r if remaining_loan > 0 else 0.0

        if year == 1:
            paid_interest = min(max(operating_profit, 0.0), interest_due)
            principal_payment = 0.0
        else:
            paid_interest = min(max(operating_profit, 0.0), interest_due)
            remaining_cash_after_interest = operating_profit - paid_interest
            principal_payment = min(max(remaining_cash_after_interest, 0.0), remaining_loan)

        repayment = paid_interest + principal_payment
        remaining_loan = max(remaining_loan - principal_payment, 0.0)

        residual_cash = annual_revenue - maintenance - repayment

        cumulative_residual_cash += residual_cash
        net_position = cumulative_residual_cash - remaining_loan

        results.append({
            "연차": year,
            "발전금": int(round(annual_revenue / 10000)),
            "상환금": int(round(repayment / 10000)),
            "유지비": int(round(maintenance / 10000)),
            "잔여금": int(round(residual_cash / 10000)),
            "누적": int(round(net_position / 10000)),
        })

    # 🔥 핵심: 연차를 index로 설정 (숫자 인덱스 제거)
    df = pd.DataFrame(results).set_index("연차")

    # KPI
    st.subheader("📌 요약(마지막 연차 기준)")
    c1, c2, c3 = st.columns(3)

    c1.metric("잔여 대출원금(만원)", f"{int(round(remaining_loan / 10000)):,}")
    c2.metric("잔여금 누적(만원)", f"{int(round(cumulative_residual_cash / 10000)):,}")
    c3.metric("누적(만원)", f"{int(round(net_position / 10000)):,}")

    # 표
    def color_pos(v):
        return "color: red" if v < 0 else "color: black"

    st.subheader("📈 연차별 누적 수익금")
    
    st.markdown(
        "단위: 만 원<br>"
        "누적 = 잔여금 누적 - 남은 대출원금",
        unsafe_allow_html=True
    )
    
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            "연차": st.column_config.NumberColumn(width="small"),
            "발전금": st.column_config.NumberColumn(width="medium"),
            "상환금": st.column_config.NumberColumn(width="medium"),
            "유지비": st.column_config.NumberColumn(width="medium"),
            "잔여금": st.column_config.NumberColumn(width="medium"),
            "누적": st.column_config.NumberColumn(width="medium"),
        },
    )

    # 흑자 전환
    pos_array = np.array(df["누적"])
    payback_idx = next((i for i, v in enumerate(pos_array) if v >= 0), None)

    if payback_idx is not None:
        st.success(f"✅ 누적 흑자 전환 시점: {payback_idx + 1}년차")
    else:
        st.warning("❗ 운영연수 내 누적 흑자 전환 불가")




