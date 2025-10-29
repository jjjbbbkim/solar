import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# 🌞 페이지 기본 설정
# -----------------------------
st.set_page_config(page_title="태양광 수익 & 금융 시뮬레이션", layout="wide")
st.title("🌞 태양광 수익 및 금융 시뮬레이션")
st.caption("📅 하루 3.6시간 발전 기준, 유지비 3% (연 1% 증가), 효율 저하 0.4%/년 반영")

# -----------------------------
# 📊 SMP / REC 단가표
# -----------------------------
st.header("📊 월별 SMP / REC 단가표")

months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
smp_values = [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90,0,0,0]
rec_values = [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97,0,0,0]

smp_rec_df = pd.DataFrame({"SMP(원/kWh)": smp_values, "REC(원/kWh)": rec_values}, index=months)
st.dataframe(smp_rec_df.style.format("{:.2f}"), width=400, height=300)

# -----------------------------
# 🏗️ 발전소 정보 입력
# -----------------------------
st.header("🏗️ 발전소 정보 입력")

col1, col2 = st.columns(2)
with col1:
    plant_type = st.selectbox("발전소 타입", ["노지형", "지붕형"])
    area_py = st.number_input("부지 면적 (평)", min_value=1, value=3000, step=10)
    smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
with col2:
    rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)
    interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
    loan_term_years = st.number_input("대출 상환기간 (년)", value=20)
    loan_ratio = st.slider("대출 비율 (%)", 0, 100, 80)

# -----------------------------
# ⚙️ 기본 계산
# -----------------------------
if plant_type == "노지형":
    rec_factor = 1.0
    base_area = 3000
    install_cost_per_100kw = 12000  # 만원
else:
    rec_factor = 1.5
    base_area = 2000
    install_cost_per_100kw = 10000  # 만원

area_m2 = area_py * 3.3
capacity_kw = area_py / base_area * 1000
total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원 단위
loan_amount = total_install_cost * (loan_ratio / 100)

st.markdown(f"""
✅ **계산된 발전용량:** {capacity_kw:,.0f} kW  
🏦 **총 사업비:** {total_install_cost/10_000:,.0f} 만원  
💰 **대출금:** {loan_amount/10_000:,.0f} 만원 (비율 {loan_ratio}%)
""")

# -----------------------------
# 💰 계산 버튼
# -----------------------------
if st.button("계산하기"):

    # 1️⃣ 발전량 (기준 3.6h/day, 효율 감소 0.4%/년)
    base_annual_gen = capacity_kw * 3.6 * 365
    annual_gen = [base_annual_gen * (1 - 0.004 * i) for i in range(loan_term_years)]

    # 2️⃣ 발전수익 (SMP + REC*가중치)
    annual_revenue = [g * (smp_price + rec_price * rec_factor) for g in annual_gen]

    # 3️⃣ 유지비 (1년차 발전수익의 3%에서 시작, 연 1% 증가)
    annual_maintenance = [annual_revenue[0] * 0.03 * ((1.01) ** i) for i in range(loan_term_years)]

    # 4️⃣ 원리금 균등상환
    r = interest_rate / 100 / 12
    n = loan_term_years * 12
    monthly_payment = loan_amount * r * (1+r)**n / ((1+r)**n - 1)
    annual_payment = monthly_payment * 12

    st.info(f"💳 월 상환액 (원리금 균등상환): {monthly_payment:,.0f} 원 /월")

    # 5️⃣ 연도별 순수익 계산
    cumulative_profit = 0
    rows = []
    for i in range(loan_term_years):
        revenue = annual_revenue[i]
        maintenance = annual_maintenance[i]
        repayment = annual_payment
        net_profit = revenue - maintenance - repayment
        cumulative_profit += net_profit
        rows.append({
            "운영연도": f"{i+1}년차",
            "연간 발전수익 (만원)": round(revenue / 10_000),
            "유지비용 (만원)": round(maintenance / 10_000),
            "원리금상환 (만원)": round(repayment / 10_000),
            "연간 순수익 (만원)": round(net_profit / 10_000),
            "누적 순수익 (만원)": round(cumulative_profit / 10_000)
        })

    df = pd.DataFrame(rows).set_index("운영연도")

    # 색상 지정: 순수익 < 0 → 빨간색, ≥0 → 검정
    def highlight(val):
        return 'color: red' if val < 0 else 'color: black'

    # 6️⃣ 결과 표
    st.subheader("📈 금융 모델 (20년 시뮬레이션)")
    st.dataframe(
        df.style.format("{:,}")
        .applymap(highlight, subset=["연간 순수익 (만원)", "누적 순수익 (만원)"]),
        width=900,
        height=500
    )

    # 7️⃣ 흑자전환 시점 계산
    np_values = np.array(df["누적 순수익 (만원)"])
    payback_idx = np.argmax(np_values > 0)
    if np.any(np_values > 0):
        payback_year = payback_idx + 1
        st.success(f"✅ 총 사업비 및 원리금 상환 후 흑자전환 시점: **{payback_year}년차**")
    else:
        st.warning("❗ 20년 내 흑자전환이 어려움")
