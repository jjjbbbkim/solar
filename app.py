import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="태양광 금융 시뮬레이션", layout="wide")
st.title("🌞 태양광 금융 시뮬레이션")

# SMP/REC 단가표 (예시)
months = [f"{i}월" for i in range(1, 13)]
smp_values = [117.11, 116.39, 113.12, 124.63, 125.50, 118.02, 120.39, 117.39, 112.90, 0, 0, 0]
rec_values = [69.76, 72.16, 72.15, 72.41, 72.39, 71.96, 71.65, 71.86, 71.97, 0, 0, 0]
smp_df = pd.DataFrame({"SMP(원/kWh)": smp_values, "REC(원/kWh)": rec_values}, index=months)

st.subheader("📊 SMP / REC 단가표")
st.dataframe(smp_df.style.format("{:.2f}"), width=400, height=250)

# 입력
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

smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)
interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
loan_term_years = st.number_input("운영연수 (년)", value=20, min_value=1)
loan_ratio = st.number_input("대출 비율 (%)", value=80, min_value=0, max_value=100)

if st.button("계산하기"):
    # 총 사업비, 대출금
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원
    loan_amount = total_install_cost * loan_ratio / 100
    st.write(f"💰 총 사업비: {total_install_cost:,.0f} 원")
    st.write(f"🏦 대출금액: {loan_amount:,.0f} 원")

    # 기본 변수
    r = interest_rate / 100
    remaining_loan = loan_amount
    cumulative_cash = 0.0

    # 1년차 기준값
    base_annual_gen = capacity_kw * 3.6 * 365
    base_annual_revenue = base_annual_gen * (smp_price + rec_price * rec_factor)
    base_maintenance_rate = 0.03

    results = []
    for year in range(1, int(loan_term_years) + 1):
        # 발전효율
        efficiency = 1 - 0.004 * (year - 1)
        annual_gen = base_annual_gen * efficiency
        annual_revenue = annual_gen * (smp_price + rec_price * rec_factor)
        maintenance = base_annual_revenue * base_maintenance_rate * (1.01 ** (year - 1))
        net_profit = annual_revenue - maintenance

        # 연 이자
        interest_due = remaining_loan * r if remaining_loan > 0 else 0

        if year == 1:
            # 1년차는 이자만 납부
            repayment = interest_due
            principal_payment = 0
        else:
            # 2년차부터는 순수익 전액으로 우선 상환
            paid_interest = min(net_profit, interest_due)
            remaining_cash_after_interest = net_profit - paid_interest
            principal_payment = min(max(remaining_cash_after_interest, 0.0), remaining_loan)
            repayment = paid_interest + principal_payment

        # 원금 차감
        remaining_loan = max(remaining_loan - principal_payment, 0.0)
        cumulative_cash += (net_profit - repayment)
        net_position = cumulative_cash - remaining_loan

        results.append({
            "연도": f"{year}년차",
            "발전 수익": int(round(annual_revenue / 10_000)),
            "유지 비용": int(round(maintenance / 10_000)),
            "순수익": int(round(net_profit / 10_000)),
            "누적 금액": int(round(net_position / 10_000))
        })

    df = pd.DataFrame(results).set_index("연도")

    # 색상: 실질포지션 <0 빨강, >=0 검정
    def color_pos(v):
        return "color: red" if v < 0 else "color: black"

    st.subheader("📈 20년 실질 누적포지션")
    st.caption("1년차는 이자만 상환 (단위 : 만 원)")
    st.dataframe(df.style.applymap(color_pos, subset=["누적 금액"]).format("{:,}"))

    # 흑자 전환 연도 찾기
    pos_array = np.array(df["누적 금액"])
    payback_idx = next((i for i, v in enumerate(pos_array) if v >= 0), None)
    if payback_idx is not None:
        st.success(f"✅ 실질 흑자 전환 시점: {payback_idx + 1}년차")
    else:
        st.warning("❗ 20년 내 흑자 전환 불가")


