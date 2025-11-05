import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="태양광 수익 & 금융 시뮬레이션 (수정)", layout="wide")
st.title("🌞 태양광 수익 & 금융 시뮬레이션 (수정본)")
st.caption("1년차 이자만, 2년차부터 순수익 전액으로 우선 상환 — 20년 전체 표시 / 색상표시 정상화")

# SMP/REC 표 (간단)
months = [f"{i}월" for i in range(1,13)]
smp_values = [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90,0,0,0]
rec_values = [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97,0,0,0]
smp_df = pd.DataFrame({"SMP(원/kWh)": smp_values, "REC(원/kWh)": rec_values}, index=months)
st.subheader("📊 SMP/REC (예시)")
st.dataframe(smp_df.style.format("{:.2f}"), width=480, height=240)

# 입력부
st.header("📝 입력")
area_unit = st.radio("면적 단위", ["평","㎡"], horizontal=True)
if area_unit == "평":
    area_py = st.number_input("부지 면적 (평)", value=3000, min_value=1, step=1)
    area_m2 = area_py * 3.3
else:
    area_m2 = st.number_input("부지 면적 (㎡)", value=9900, min_value=1, step=1)
    area_py = area_m2 / 3.3
st.write(f"면적: {area_py:,.0f} 평  (≈ {area_m2:,.0f} ㎡)")

plant_type = st.selectbox("발전소 타입", ["노지형","지붕형"])
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
st.write(f"계산된 발전용량: {capacity_kw:.0f} kW")

smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)

interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
loan_term_years = st.number_input("운영연수 (년)", value=20, min_value=1)
loan_ratio = st.number_input("대출 비율 (%)", value=80, min_value=0, max_value=100)

if st.button("계산하기"):

    # 기본 수치
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원
    loan_amount = total_install_cost * loan_ratio / 100
    st.write(f"총 사업비: {total_install_cost:,.0f} 원, 대출금: {loan_amount:,.0f} 원")

    # 변수 초기화
    r = interest_rate / 100
    remaining_loan = loan_amount
    cumulative_cash = 0.0   # 누적 현금(순수익 - 상환금)을 누적
    results = []

    # 기준 수익(1년차 기준) — 유지비 계산의 기준으로 사용
    base_annual_gen = capacity_kw * 3.6 * 365
    base_annual_revenue = base_annual_gen * (smp_price + rec_price * rec_factor)
    base_maintenance_rate = 0.03  # 1년차 유지비율

    for year in range(1, int(loan_term_years) + 1):
        # 연간 발전량(효율감소 반영)
        efficiency = 1 - 0.004 * (year - 1)
        annual_gen = base_annual_gen * efficiency
        annual_revenue = annual_gen * (smp_price + rec_price * rec_factor)

        # 유지비: 1년차 기준 수익의 3%에서 시작, 연 1% 증가
        maintenance = base_annual_revenue * base_maintenance_rate * (1.01 ** (year - 1))

        # 순수익(현금 유입)
        net_profit = annual_revenue - maintenance

        # 1) 이자 계산 (항상 잔존원금에 대한 이자)
        interest_due = remaining_loan * r if remaining_loan > 0 else 0.0

        # 2) 지급 가능한 현금 = net_profit (요청대로 순수익 전액을 상환에 사용)
        # 우선 이자 지급, 남는 금액은 원금 상환
        paid_interest = min(net_profit, interest_due)
        remaining_cash_after_interest = net_profit - paid_interest

        # principal payment = 남은 현금으로 원금을 갚음 (최대 remaining_loan)
        principal_payment = min(max(remaining_cash_after_interest, 0.0), remaining_loan)

        # 실제 상환금(이자 + 원금)
        repayment = paid_interest + principal_payment

        # 누적 현금(= 지금까지 쌓인 잉여현금) = 이전 + (net_profit - repayment)
        cumulative_cash += (net_profit - repayment)

        # 잔여 대출 갱신
        remaining_loan = max(remaining_loan - principal_payment, 0.0)

        # 실질 지표: (누적 현금) - (남은 대출)  — 이것이 한 줄로 보는 '실질 누적 포지션'
        net_position = cumulative_cash - remaining_loan

        results.append({
            "연도": f"{year}년차",
            "발전수익 (만원)": int(round(annual_revenue / 10_000)),
            "유지비용 (만원)": int(round(maintenance / 10_000)),
            "순수익 (만원)": int(round(net_profit / 10_000)),
            "상환금 (만원)": int(round(repayment / 10_000)),
            "잔여대출 (만원)": int(round(remaining_loan / 10_000)),
            "실질 누적포지션 (만원)": int(round(net_position / 10_000))
        })

    df = pd.DataFrame(results).set_index("연도")

    # 색상: 실질 포지션 < 0 -> 빨강, >=0 -> 검정
    def style_pos(v):
        return 'color: red' if v < 0 else 'color: black'

    st.subheader("📈 20년 시뮬레이션 (순수익 우선 상환)")
    st.dataframe(df.style.applymap(style_pos, subset=["실질 누적포지션 (만원)"]).format("{:,}"),
                 width=1000, height=520)

    # 흑자 전환 연도 (실질 포지션 >= 0 최초 연도)
    pos_array = np.array(df["실질 누적포지션 (만원)"])
    payback_idx = next((i for i,v in enumerate(pos_array) if v >= 0), None)
    if payback_idx is not None:
        st.success(f"✅ 흑자(실질포지션 ≥ 0) 전환: {payback_idx+1}년차")
    else:
        st.warning("❗ 20년 내 흑자전환 불가")
