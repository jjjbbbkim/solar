import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="태양광 금융모델", layout="wide")

st.title("☀️ 태양광 발전사업 금융모델 시뮬레이터")

# --------------------------
# 1️⃣ 기본 금융 정보 입력
# --------------------------
st.header("📋 금융정보 입력")

col1, col2, col3 = st.columns(3)

with col1:
    total_cost = st.number_input("총 사업비 (만원)", value=200000)
with col2:
    loan_ratio = st.slider("대출 비율 (%)", 0, 100, 70)
with col3:
    interest_rate = st.number_input("대출 이자율 (%)", value=5.0, step=0.1)

loan_term_years = 20
loan_amount = total_cost * (loan_ratio / 100)
own_capital = total_cost - loan_amount

st.write(f"💰 **총 사업비:** {total_cost:,.0f} 만원")
st.write(f"🏦 **대출금:** {loan_amount:,.0f} 만원")
st.write(f"💵 **자기자본:** {own_capital:,.0f} 만원")

# --------------------------
# 2️⃣ SMP / REC 단가표
# --------------------------
st.header("📊 SMP / REC 단가표")

months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
smp_values = np.random.randint(90, 130, 12)
rec_values = np.random.randint(60, 110, 12)
rec_weight = 1.5
rec_weighted = rec_values * rec_weight

price_df = pd.DataFrame({
    "SMP (원/kWh)": smp_values,
    "REC (원/kWh)": rec_values,
    "1.5 가중 REC (원/kWh)": rec_weighted
}, index=months)

styled_price_table = (
    price_df.style
    .set_table_styles([
        {"selector": "th", "props": [("min-width", "130px"), ("max-width", "180px"), ("text-align", "center")]},
        {"selector": "td", "props": [("min-width", "130px"), ("max-width", "180px"), ("text-align", "center")]}
    ])
    .format("{:,.0f}")
)

st.dataframe(styled_price_table, use_container_width=True, height=260)

# --------------------------
# 3️⃣ 금융모델 계산
# --------------------------
st.header("💰 20년 금융모델 (잔여대출/순수익)")

years = np.arange(1, loan_term_years + 1)

# 연간 발전수익 (효율 감소 4%)
initial_revenue = st.number_input("1년차 예상 발전수익 (만원)", value=30000)
revenues = [initial_revenue * ((1 - 0.04) ** (y - 1)) for y in years]

# 유지관리비 (1년차 수익의 3%, 매년 1%씩 증가)
maintenance_costs = []
for y in years:
    if y == 1:
        maintenance_costs.append(initial_revenue * 0.03)
    else:
        maintenance_costs.append(maintenance_costs[-1] * 1.01)

# 1년차 이자만 상환, 2년차부터 모든 수익 상환
remaining_loan = loan_amount
annual_interest = []
annual_payment = []
net_positions = []

for y in years:
    interest = remaining_loan * (interest_rate / 100)
    annual_interest.append(interest)
    
    if y == 1:
        payment = interest  # 1년차는 이자만 납부
    else:
        payment = revenues[y-1] - maintenance_costs[y-1]
        remaining_loan -= (payment - interest)
        if remaining_loan < 0:
            remaining_loan = 0
    
    annual_payment.append(payment)
    net_positions.append(remaining_loan if remaining_loan > 0 else payment - interest)

# 데이터프레임 구성
finance_df = pd.DataFrame({
    "연간 발전수익 (만원)": np.round(revenues, 0),
    "유지관리비 (만원)": np.round(maintenance_costs, 0),
    "연간 상환금 (만원)": np.round(annual_payment, 0),
    "잔여대출/순수익 (만원)": np.round(net_positions, 0)
}, index=[f"{y}년차" for y in years])

# 색상 구분 (빨강: 대출잔액, 검정: 순수익)
def highlight_value(val):
    if val > 0:
        return "color: red; font-weight: bold"
    else:
        return "color: black"

styled_finance_table = (
    finance_df.style
    .set_table_styles([
        {"selector": "th", "props": [("min-width", "140px"), ("max-width", "220px"), ("text-align", "center")]},
        {"selector": "td", "props": [("min-width", "140px"), ("max-width", "220px"), ("text-align", "center")]}
    ])
    .applymap(highlight_value, subset=["잔여대출/순수익 (만원)"])
    .format("{:,.0f}")
)

st.dataframe(styled_finance_table, use_container_width=True, height=520)

# --------------------------
# 4️⃣ 예상 회수 시점 표시
# --------------------------
try:
    payback_year = next(i for i, v in enumerate(net_positions) if v <= 0) + 1
    st.success(f"✅ 예상 순수익 전환 시점: **약 {payback_year}년차** 이후")
except StopIteration:
    st.warning("⚠️ 20년 내에 대출금 전액 상환이 어렵습니다.")
