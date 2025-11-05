import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# 🌞 페이지 기본 설정
# -----------------------------
st.set_page_config(page_title="태양광 수익 & 금융 시뮬레이션", layout="wide")
st.title("🌞 태양광 수익 & 금융 시뮬레이션")
st.caption("📅 하루 3.6시간 발전 기준 / SMP+REC 단가 기반 / 연 0.4% 효율감소 / 유지비 연 1% 증가")

# -----------------------------
# 📊 SMP / REC 단가표
# -----------------------------
months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
smp_values = [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90,0,0,0]
rec_values = [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97,0,0,0]

smp_df = pd.DataFrame({
    "SMP(원/kWh)": smp_values,
    "REC(원/kWh)": rec_values
}, index=months)
st.subheader("📊 월별 SMP/REC 단가표")
st.dataframe(smp_df.style.format("{:,}"), width=500, height=300)

# -----------------------------
# 🏗 발전소 기본 정보 입력
# -----------------------------
st.header("📝 발전소 정보 입력")

plant_type = st.selectbox("발전소 타입", ["노지형", "지붕형"])
if plant_type == "노지형":
    rec_factor = 1.0
    base_area = 3000
    install_cost_per_100kw = 12000
else:
    rec_factor = 1.5
    base_area = 2000
    install_cost_per_100kw = 10000

area_unit = st.radio("면적 단위 선택", ["평", "㎡"], horizontal=True)
if area_unit == "평":
    area_py = st.number_input("부지 면적 (평)", min_value=1, value=3000, step=1)
    area_m2 = area_py * 3.3
else:
    area_m2 = st.number_input("부지 면적 (㎡)", min_value=1, value=9900, step=1)
    area_py = area_m2 / 3.3

st.write(f"면적: {area_py:.0f}평 ({area_m2:.0f}㎡)")

capacity_kw = area_py / base_area * 1000
st.write(f"발전용량: **{capacity_kw:.0f} kW**")

smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)

if plant_type == "지붕형":
    st.info(f"REC 가중치 1.5 적용 시 REC 단가: {rec_price * 1.5:.2f}원/kWh")

# -----------------------------
# 💰 금융 정보 입력
# -----------------------------
st.header("💰 금융 정보")

interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
loan_term_years = st.number_input("운영연수 (년)", value=20)
loan_ratio = st.number_input("대출 비율 (%)", value=70)

if st.button("계산하기"):
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000
    loan_amount = total_install_cost * (loan_ratio / 100)
    equity_amount = total_install_cost - loan_amount

    st.markdown(f"**총 사업비:** {total_install_cost/10_000:,.0f}만원")
    st.markdown(f"**대출금:** {loan_amount/10_000:,.0f}만원 / **자기자본:** {equity_amount/10_000:,.0f}만원")

    # -----------------------------
    # 📆 연도별 계산
    # -----------------------------
    r = interest_rate / 100
    remaining_loan = loan_amount
    cumulative_profit = 0
    results = []

    base_revenue = capacity_kw * 3.6 * 365 * (smp_price + rec_price * rec_factor)
    base_maintenance_rate = 0.03

    for year in range(1, loan_term_years + 1):
        efficiency = 1 - 0.004 * (year - 1)
        annual_generation = capacity_kw * 3.6 * 365 * efficiency
        annual_revenue = annual_generation * (smp_price + rec_price * rec_factor)
        maintenance = base_revenue * base_maintenance_rate * (1.01 ** (year - 1))
        net_profit = annual_revenue - maintenance

        interest_payment = remaining_loan * r
        principal_payment = 0 if year == 1 else max(0, min(net_profit - interest_payment, remaining_loan))
        repayment = interest_payment + principal_payment
        remaining_loan -= principal_payment

        # 누적순수익 (상환금 반영)
        cumulative_profit += (net_profit - repayment)

        results.append({
            "연도": f"{year}년차",
            "발전수익 (만원)": round(annual_revenue / 10_000),
            "유지비용 (만원)": round(maintenance / 10_000),
            "순수익 (만원)": round(net_profit / 10_000),
            "상환금 (만원)": round(repayment / 10_000),
            "잔여대출/순수익 (만원)": round(cumulative_profit / 10_000)
        })

    df = pd.DataFrame(results).set_index("연도")

    def color_value(val):
        color = 'red' if val < 0 else 'black'
        return f'color: {color}'

    st.subheader("📈 금융 모델 (20년 시뮬레이션)")
    st.dataframe(df.style.applymap(color_value, subset=["잔여대출/순수익 (만원)"]), width=1000, height=500)

    profit_year = next((i+1 for i, v in enumerate(df["잔여대출/순수익 (만원)"]) if v > 0), None)
    if profit_year:
        st.success(f"✅ 예상 흑자 전환 시점: 약 {profit_year}년차")
    else:
        st.warning("❗ 20년 내 흑자 전환 어려움")
