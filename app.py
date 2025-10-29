import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="태양광 수익 & 금융 모델", layout="wide")
st.title("🌞 태양광 수익 & 금융 시뮬레이션")
st.caption("📅 기준: 하루 3.6시간 발전, 유지비 = 1년차 발전수익의 3% (연 1% 증가), 효율 연 0.4% 감소")

# -----------------------------
# SMP / REC 단가표
# -----------------------------
months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
smp_values = [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90,0,0,0]
rec_values = [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97,0,0,0]

smp_df = pd.DataFrame({
    "SMP(원/kWh)": smp_values,
    "REC(원/kWh)": rec_values
}, index=months)
st.dataframe(smp_df.style.format("{:.2f}"), width=450, height=300)

# -----------------------------
# 발전소 및 금융 정보 입력
# -----------------------------
st.header("📝 발전소 정보 입력")

col1, col2 = st.columns(2)
with col1:
    plant_type = st.selectbox("발전소 타입", ["노지형", "지붕형"])
    area_py = st.number_input("부지 면적 (평)", min_value=1, value=3000, step=1)
    interest_rate = st.number_input("대출 이자율 (%)", value=6.0)

with col2:
    smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
    rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)
    loan_ratio = st.number_input("대출 비율 (%)", min_value=0, max_value=100, value=80, step=5)

if plant_type == "노지형":
    rec_factor = 1.0
    base_area = 3000
    install_cost_per_100kw = 12000
else:
    rec_factor = 1.5
    base_area = 2000
    install_cost_per_100kw = 10000

capacity_kw = area_py / base_area * 1000
total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000
loan_term_years = 20
loan_amount = total_install_cost * loan_ratio / 100

st.write(f"계산된 발전용량: **{capacity_kw:.0f} kW**")
st.write(f"총 사업비: **{total_install_cost:,.0f} 원**, 대출금: **{loan_amount:,.0f} 원**")

# -----------------------------
# 계산 시작
# -----------------------------
if st.button("계산하기"):

    months_array = np.arange(1, loan_term_years * 12 + 1)

    # 1년차 발전수익 (100% 효율)
    monthly_gen_base = capacity_kw * 3.6 * 30
    annual_revenue_year1 = monthly_gen_base * 12 * (smp_price + rec_price * rec_factor)

    # 유지비용 (1년차 발전수익의 3% 기준, 연 1% 증가)
    annual_maintenance_costs = [
        annual_revenue_year1 * 0.03 * (1.01 ** i)
        for i in range(loan_term_years)
    ]
    monthly_maintenance_array = np.repeat(np.array(annual_maintenance_costs) / 12, 12)

    # 발전량 (연 0.4% 효율감소)
    monthly_gen_array = capacity_kw * 3.6 * 30 * (1 - 0.004 * ((months_array - 1)//12))

    # 발전수익
    monthly_profit = (monthly_gen_array * (smp_price + rec_price * rec_factor)) - monthly_maintenance_array
    cumulative_profit = np.cumsum(monthly_profit)

    # 원리금 균등상환 계산
    r = interest_rate / 100 / 12
    n = loan_term_years * 12
    monthly_payment = loan_amount * r * (1+r)**n / ((1+r)**n - 1)

    # 연도별 정리
    annual_summary = pd.DataFrame({
        "총 누적 수익 (만원)": np.round(cumulative_profit[11::12] / 10_000).astype(int),
        "연간 상환금 (만원)": np.round((monthly_payment * 12) / 10_000).astype(int),
        "연간 유지비 (만원)": np.round(np.array(annual_maintenance_costs) / 10_000).astype(int),
    }, index=[f"{i}년차" for i in range(1, loan_term_years + 1)])

    # 순수익 계산
    annual_summary["남은 원금/순수익 (만원)"] = (
        np.round((cumulative_profit[11::12] - monthly_payment * 12 * np.arange(1, loan_term_years+1)) / 10_000)
    ).astype(int)

    # 색상 처리
    def color_balance(val):
        return 'color: red' if val < 0 else 'color: black'

    st.subheader("📈 금융 모델 (연도별)")
    st.dataframe(
        annual_summary.style.format("{:,}").applymap(color_balance, subset=['남은 원금/순수익 (만원)']),
        width=950, height=450
    )

    # 원리금 균등상환 요약
    st.subheader("🏦 원리금 균등상환 요약")
    st.write(f"📅 월 상환액: **{monthly_payment:,.0f} 원**, 총 상환기간: {loan_term_years}년")
