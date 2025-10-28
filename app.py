import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# 1️⃣ 페이지 설정
# -----------------------------
st.set_page_config(page_title="태양광 수익 & 금융 모델", layout="wide")
st.title("🌞 태양광 수익 & 금융 시뮬레이션")
st.caption("📅 하루 3.6시간 발전 기준, SMP/REC 단가 적용, 효율 0.4%/년 감소, 유지비 3% 시작, 1%씩 증가")

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
st.dataframe(smp_df.style.format("{:,}").set_properties(**{'text-align': 'center'}), width=500, height=300)

# -----------------------------
# 3️⃣ 발전소 정보 입력
# -----------------------------
st.header("📝 발전소 정보 입력")
plant_type = st.selectbox("발전소 타입", ["노지형", "지붕형"])
if plant_type == "노지형":
    rec_factor = 1.0
    base_area = 3000
    install_cost_per_100kw = 12000  # 만원
else:
    rec_factor = 1.5
    base_area = 2000
    install_cost_per_100kw = 10000  # 만원
st.write(f"REC 가중치: {rec_factor}")

area_py = st.number_input("부지 면적 (평)", min_value=1, value=3000, step=1)
area_m2 = area_py * 3.3
capacity_kw = area_py / base_area * 1000
st.write(f"계산된 발전용량: {capacity_kw:.0f} kW ({area_m2:.0f} ㎡)")

smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)

st.header("💰 금융 정보")
interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
loan_term_years = st.number_input("대출 상환기간 (년)", value=20)

# -----------------------------
# 4️⃣ 계산 버튼
# -----------------------------
if st.button("계산하기"):

    # -----------------------------
    # 월별 유지비용 계산 (3% 시작, 매년 1% 증가)
    # -----------------------------
    months_total = loan_term_years * 12
    base_maintenance_rate = 0.03
    monthly_maintenance_array = np.array([
        capacity_kw/100*install_cost_per_100kw*10_000 * base_maintenance_rate * (1.01 ** ((m-1)//12)) / 12
        for m in range(1, months_total+1)
    ])

    total_investment = capacity_kw/100*install_cost_per_100kw*10_000 + monthly_maintenance_array.sum()

    # -----------------------------
    # 월별 발전량 (3.6시간/일, 30일 기준) + 효율 감소 0.4%/년
    # -----------------------------
    monthly_gen_array = capacity_kw * 3.6 * 30 * (1 - 0.004 * ((np.arange(1, months_total+1)-1)//12))

    # -----------------------------
    # 월별 수익
    # -----------------------------
    monthly_profit = monthly_gen_array * (smp_price + rec_price * rec_factor)
    cumulative_profit = np.cumsum(monthly_profit)

    # -----------------------------
    # 원리금 균등상환 계산 (20년, 마지막 달 잔여원금 0)
    # -----------------------------
    r = interest_rate/100/12
    n = months_total
    monthly_payment = total_investment * r * (1+r)**n / ((1+r)**n - 1)
    remaining_loan_array = []
    remaining = total_investment
    for _ in range(n):
        remaining -= monthly_payment
        remaining_loan_array.append(max(remaining,0))
    remaining_loan_array = np.array(remaining_loan_array)

    # -----------------------------
    # 연 단위 금융모델 표
    # -----------------------------
    years = np.arange(1, loan_term_years+1)
    summary_yearly = pd.DataFrame({
        "총 누적 수익 (만원)": [int(round(cumulative_profit[y*12-1]/10_000,0)) for y in years],
        "연간 상환금 (만원)": [int(round(monthly_payment*12/10_000,0)) for y in years],
        "연간 유지비용 (만원)": [int(round(monthly_maintenance_array[(y-1)*12:y*12].sum()/10_000,0)) for y in years],
        "남은 원금/순수익 (만원)": [
            -int(round(remaining_loan_array[y*12-1]/10_000,0)) if remaining_loan_array[y*12-1]>0
            else int(round((cumulative_profit[y*12-1]-total_investment)/10_000,0))
            for y in years
        ]
    })
    summary_yearly.index = [f"{y}년차" for y in years]

    def color_remaining(val):
        return 'color: red' if val < 0 else 'color: black'

    st.subheader("📈 금융 모델 (연 단위)")
    st.dataframe(summary_yearly.style.applymap(color_remaining, subset=['남은 원금/순수익 (만원)']), width=900, height=500)

    # -----------------------------
    # 연 단위 원리금 균등상환 표
    # -----------------------------
    loan_df_yearly = pd.DataFrame({
        "월별 상환금 (만원)": [int(round(monthly_payment*12/10_000,0))]*loan_term_years,
        "월별 유지비용 (만원)": [int(round(monthly_maintenance_array[(y-1)*12:y*12].sum()/10_000,0)) for y in years],
        "잔여 원금 (만원)": [int(round(remaining_loan_array[y*12-1]/10_000,0)) for y in years]
    }, index=[f"{y}년차" for y in years])
    st.subheader("🏦 원리금 균등상환 (연 단위)")
    st.dataframe(loan_df_yearly.style.applymap(color_remaining, subset=['잔여 원금 (만원)']), width=900, height=500)

    # -----------------------------
    # 예상 회수기간
    # -----------------------------
    payback_month = np.argmax(cumulative_profit >= total_investment) + 1 if np.any(cumulative_profit >= total_investment) else None
    if payback_month:
        payback_years = payback_month/12
        st.success(f"✅ 예상 회수기간: 약 {payback_years:.1f}년 ({payback_month}개월)")
    else:
        st.warning("❗ 대출 기간 내 투자비 회수가 어려움")
