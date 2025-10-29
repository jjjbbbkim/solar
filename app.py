import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# 1️⃣ 페이지 설정
# -----------------------------
st.set_page_config(page_title="태양광 수익 & 금융 모델", layout="wide")
st.title("🌞 태양광 수익 & 금융 시뮬레이션")
st.caption("📅 기준: 하루 3.6시간 발전 기준, 유지비용 3% (연 1% 증가), 발전효율 연 0.4% 감소")

# -----------------------------
# 2️⃣ SMP/REC 단가표
# -----------------------------
st.header("📊 월별 SMP/REC 단가표")

months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
smp_values = [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90,0,0,0]
rec_values = [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97,0,0,0]

smp_df = pd.DataFrame({
    "SMP(원/kWh)": smp_values,
    "REC(원/kWh)": rec_values
}, index=months)
st.dataframe(
    smp_df.style.format("{:.2f}").set_properties(**{'text-align': 'center'}),
    width=450, height=300
)

# -----------------------------
# 3️⃣ 발전소 정보 입력
# -----------------------------
st.header("📝 발전소 정보 입력")
col1, col2 = st.columns(2)

with col1:
    plant_type = st.selectbox("발전소 타입", ["노지형", "지붕형"])
    if plant_type == "노지형":
        rec_factor = 1.0
        base_area = 3000
        install_cost_per_100kw = 12000  # 만원
    else:
        rec_factor = 1.5
        base_area = 2000
        install_cost_per_100kw = 10000  # 만원

    area_py = st.number_input("부지 면적 (평)", min_value=1, value=3000, step=1)
    st.write(f"REC 가중치: {rec_factor}")

with col2:
    smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
    rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)
    interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
    loan_term_years = 20

area_m2 = area_py * 3.3
capacity_kw = area_py / base_area * 1000
total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원 단위
st.write(f"계산된 발전용량: {capacity_kw:.0f} kW ({area_m2:.0f}㎡)")
st.write(f"총 사업비: {total_install_cost:,.0f} 원")

loan_ratio = st.number_input("대출 비율 (%)", min_value=0, max_value=100, value=80, step=5)
loan_amount = total_install_cost * loan_ratio / 100
st.write(f"💰 대출금: {loan_amount:,.0f} 원")

# -----------------------------
# 4️⃣ 계산 버튼
# -----------------------------
if st.button("계산하기"):

    months_array = np.arange(1, loan_term_years * 12 + 1)

    # 월별 유지비용 (3% 시작, 매년 1% 증가)
    base_maintenance_rate = 0.03
    monthly_maintenance_array = np.array([
        total_install_cost * base_maintenance_rate * (1.01 ** ((m-1)//12)) / 12
        for m in months_array
    ])

    # 월별 발전량 (3.6시간/일, 30일 기준, 효율감소 반영)
    monthly_gen_array = capacity_kw * 3.6 * 30 * (1 - 0.004 * ((months_array - 1)//12))

    # 월별 발전수익 (원/kWh 단가 적용 → 단위 보정 /1000)
    monthly_profit = (monthly_gen_array * (smp_price + rec_price * rec_factor) / 1000) - monthly_maintenance_array

    # 누적 수익 계산
    cumulative_profit = np.cumsum(monthly_profit)

    # 원리금 균등상환 (20년 완전상환)
    r = interest_rate / 100 / 12
    n = loan_term_years * 12
    monthly_payment = loan_amount * r * (1+r)**n / ((1+r)**n - 1)

    # 대출 잔여원금 계산
    remaining_loan_array = []
    remaining = loan_amount
    for _ in range(len(months_array)):
        interest = remaining * r
        principal = monthly_payment - interest
        remaining -= principal
        remaining_loan_array.append(max(remaining, 0))
    remaining_loan_array = np.array(remaining_loan_array)

    # -----------------------------
    # 5️⃣ 금융 모델 (연 단위)
    # -----------------------------
    summary_df = pd.DataFrame({
        "총 누적 수익 (만원)": np.round(cumulative_profit[11::12] / 10_000, 0).astype(int),
        "월별 유지비용 (만원)": np.round(monthly_maintenance_array[11::12] / 10_000, 0),
        "연간 상환금 (만원)": np.round((monthly_payment * 12) / 10_000, 0),
        "남은 원금/순수익 (만원)": np.round((cumulative_profit[11::12] - loan_amount) / 10_000, 0)
    }, index=[f"{i}년차" for i in range(1, loan_term_years + 1)])

    # 색상 처리
    def color_balance(val):
        return 'color: red' if val < 0 else 'color
