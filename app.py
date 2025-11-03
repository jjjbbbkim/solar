import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# 🌞 페이지 설정
# -----------------------------
st.set_page_config(page_title="태양광 수익 & 금융 시뮬레이션", layout="wide")
st.title("🌞 태양광 수익 & 금융 시뮬레이션")
st.caption("📅 기준: 하루 3.6시간 발전, 유지비용은 1년차 발전수익의 3%로 시작해 매년 1% 증가")

# -----------------------------
# 📊 월별 SMP/REC 단가표
# -----------------------------
st.header("📊 월별 SMP/REC 단가표")
months = [f"{i}월" for i in range(1, 13)]
smp_values = [117.11, 116.39, 113.12, 124.63, 125.50, 118.02, 120.39, 117.39, 112.90, 0, 0, 0]
rec_values = [69.76, 72.16, 72.15, 72.41, 72.39, 71.96, 71.65, 71.86, 71.97, 0, 0, 0]

smp_df = pd.DataFrame({
    "SMP(원/kWh)": smp_values,
    "REC(원/kWh)": rec_values
}, index=months)
st.dataframe(smp_df.style.format("{:,}"), width=500, height=300)

# -----------------------------
# 🏗️ 발전소 기본 정보
# -----------------------------
st.header("🏗️ 발전소 정보 입력")

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

with col2:
    area_unit = st.radio("면적 단위 선택", ["평", "㎡"], horizontal=True)

if area_unit == "평":
    area_input = st.number_input("부지 면적 (평)", min_value=1, value=3000, step=10)
    area_m2 = area_input * 3.3
    area_display = f"{area_input:,}평 ({area_m2:,.0f}㎡)"
else:
    area_input = st.number_input("부지 면적 (㎡)", min_value=1, value=9900, step=10)
    area_py = area_input / 3.3
    area_display = f"{area_input:,}㎡ ({area_py:,.0f}평)"

st.write(f"📏 선택 면적: {area_display}")

capacity_kw = (area_input / base_area * 1000) if area_unit == "평" else (area_input / (base_area * 3.3) * 1000)
st.write(f"⚡ 계산된 발전용량: {capacity_kw:.0f} kW")

# -----------------------------
# 💸 금융 정보 입력
# -----------------------------
st.header("💰 금융 정보")

col1, col2, col3 = st.columns(3)
with col1:
    smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
with col2:
    rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)
    if plant_type == "지붕형":
        st.caption(f"→ 가중치 적용 단가: **{rec_price * 1.5:.2f} 원/kWh**")
with col3:
    rec_weight = rec_factor

interest_rate = st.number_input("이자율 (%)", value=6.0)
loan_term_years = st.number_input("운영 연한 (년)", value=20)
loan_ratio = st.number_input("대출 비율 (%)", min_value=0, max_value=100, value=70)

# -----------------------------
# 🚀 계산 시작
# -----------------------------
if st.button("계산하기"):

    # 총 사업비 (원 단위)
    total_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000
    loan_amount = total_cost * (loan_ratio / 100)
    st.subheader("📘 사업비 요약")
    st.write(f"총 사업비: **{total_cost:,.0f}원**")
    st.write(f"대출금액 ({loan_ratio}%): **{loan_amount:,.0f}원**")

    # -----------------------------
    # 연간 발전량, 수익, 유지비용 계산
    # -----------------------------
    years = np.arange(1, loan_term_years + 1)
    daily_hours = 3.6
    days_per_month = 30
    months_per_year = 12

    # 연별 효율 감소 적용 (연 0.4%)
    yearly_efficiency = (1 - 0.004) ** (years - 1)

    # 연별 발전량(kWh)
    yearly_gen = capacity_kw * daily_hours * days_per_month * months_per_year * yearly_efficiency

    # 연별 발전수익
    yearly_revenue = yearly_gen * (smp_price + rec_price * rec_weight)

    # 유지비용 (1년차는 발전수익의 3%, 이후 매년 1% 증가)
    maintenance_rate = [0.03 * (1.01 ** (y - 1)) for y in years]
    yearly_maintenance = yearly_revenue[0] * np.array(maintenance_rate)

    # 순수익 (유지비용 차감)
    yearly_profit = yearly_revenue - yearly_maintenance

    # -----------------------------
    # 💰 대출 이자만 상환 (1년차)
    # 이후 원금 상환 포함 (2년차~)
    # -----------------------------
    r = interest_rate / 100
    yearly_interest_only = loan_amount * r
    remaining_loan = loan_amount
    yearly_principal_payment = np.zeros(loan_term_years)

    for i in range(1, loan_term_years):
        # 2년차부터 원금 균등 상환
        yearly_principal_payment[i] = loan_amount / (loan_term_years - 1)
        remaining_loan -= yearly_principal_payment[i]

    # 연별 상환금 = 이자 + 원금
    yearly_payment = np.zeros(loan_term_years)
    yearly_payment[0] = yearly_interest_only
    yearly_payment[1:] = yearly_interest_only + yearly_principal_payment[1:]

    # -----------------------------
    # 순수익 - 상환금 모델
    # -----------------------------
    yearly_net_profit = yearly_profit - yearly_payment
    cumulative_profit = np.cumsum(yearly_net_profit)
    remaining_balance = cumulative_profit - loan_amount  # 잔여대출과 순수익의 차이

    summary_df = pd.DataFrame({
        "연간 발전수익 (만원)": (yearly_revenue / 10_000).round(0).astype(int),
        "연간 유지비용 (만원)": (yearly_maintenance / 10_000).round(0).astype(int),
        "연간 순수익 (만원)": (yearly_profit / 10_000).round(0).astype(int),
        "연간 상환금 (만원)": (yearly_payment / 10_000).round(0).astype(int),
        "순수익-상환 후 잔액 (만원)": (yearly_net_profit / 10_000).round(0).astype(int),
        "누적 순수익-대출차감 (만원)": (remaining_balance / 10_000).round(0).astype(int)
    }, index=[f"{y}년차" for y in years])

    # 색상 표시
    def color_balance(val):
        return 'color: red' if val < 0 else 'color: black'

    st.subheader("📈 금융모델 (1년차 이자상환 / 순수익 - 대출금 기준)")
    st.dataframe(
        summary_df.style.format("{:,}")
        .applymap(color_balance, subset=["누적 순수익-대출차감 (만원)"]),
        width=1000, height=550
    )

    # -----------------------------
    # 💵 회수 시점 표시
    # -----------------------------
    payback_idx = np.argmax(remaining_balance > 0)
    if remaining_balance[payback_idx] > 0:
        st.success(f"✅ 예상 흑자 전환 시점: 약 {payback_idx + 1}년차")
    else:
        st.warning("❗ 20년 내 대출금 회수 불가능")
