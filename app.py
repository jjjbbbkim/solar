import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------
# 1️⃣ 페이지 설정
# -------------------------------------
st.set_page_config(page_title="태양광 수익 & 금융 시뮬레이션", layout="wide")
st.title("🌞 태양광 수익 & 금융 시뮬레이션")
st.caption("📅 하루 3.6시간 발전 기준, 효율 0.4%/년 감소, 유지비 3%(연 1% 증가) 적용")

# -------------------------------------
# 2️⃣ 월별 SMP / REC 단가표
# -------------------------------------
st.header("📊 월별 SMP / REC 단가표")

months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
smp_values = [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90,0,0,0]
rec_values = [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97,0,0,0]

smp_rec_df = pd.DataFrame({
    "SMP(원/kWh)": smp_values,
    "REC(원/kWh)": rec_values
}, index=months)

st.dataframe(
    smp_rec_df.style.format("{:.2f}")
    .set_properties(**{'text-align': 'center'}),
    width=450, height=320
)

# -------------------------------------
# 3️⃣ 발전소 정보 입력
# -------------------------------------
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
st.write(f"REC 가중치: **{rec_factor}**")

# 면적 단위 선택
area_unit = st.radio("면적 단위 선택", ["평", "㎡"], horizontal=True)

if area_unit == "평":
    area_py = st.number_input("부지 면적 (평)", min_value=1, value=3000, step=1)
    area_m2 = area_py * 3.3
    st.caption(f"≈ {area_m2:,.0f} ㎡")
else:
    area_m2 = st.number_input("부지 면적 (㎡)", min_value=1, value=9900, step=1)
    area_py = area_m2 / 3.3
    st.caption(f"≈ {area_py:,.0f} 평")

# 발전용량 계산
capacity_kw = area_py / base_area * 1000
st.write(f"계산된 발전용량: **{capacity_kw:,.0f} kW**")

# -------------------------------------
# 4️⃣ 단가 및 금융 정보
# -------------------------------------
st.header("⚙️ 단가 및 금융 정보")

col1, col2 = st.columns(2)
with col1:
    smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
    rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)
with col2:
    interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
    loan_term_years = st.number_input("대출 상환기간 (년)", value=20)
    loan_ratio = st.number_input("대출 비율 (% , 총 사업비 대비)", min_value=0, max_value=100, value=70)

# -------------------------------------
# 5️⃣ 계산 버튼
# -------------------------------------
if st.button("💡 수익 계산하기"):
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원 단위
    loan_amount = total_install_cost * (loan_ratio / 100)
    st.info(f"총 사업비: {total_install_cost/1_0000:,.0f} 만원 / 대출금: {loan_amount/1_0000:,.0f} 만원")

    # 월별 시간축
    months_array = np.arange(1, loan_term_years*12 + 1)

    # --------------------------
    # 월별 유지비용 (3% 시작, 매년 1% 증가)
    # --------------------------
    base_maintenance_rate = 0.03
    yearly_maintenance = np.array([
        total_install_cost * base_maintenance_rate * (1.01 ** (year-1))
        for year in range(1, loan_term_years+1)
    ])

    # --------------------------
    # 월별 발전량 (3.6시간/일, 30일 기준, 효율 0.4%/년 감소)
    # --------------------------
    monthly_gen_array = capacity_kw * 3.6 * 30 * (1 - 0.004 * ((months_array-1)//12))

    # --------------------------
    # 월별 수익
    # --------------------------
    monthly_profit = monthly_gen_array * (smp_price + rec_price * rec_factor)

    # --------------------------
    # 연간 데이터 집계
    # --------------------------
    yearly_profit = np.array([monthly_profit[i*12:(i+1)*12].sum() for i in range(loan_term_years)])
    yearly_maintenance = yearly_maintenance
    net_profit = yearly_profit - yearly_maintenance

    # --------------------------
    # 순수익으로 대출금 상환 (수익으로 차감)
    # --------------------------
    remaining_loan = []
    remaining = loan_amount
    for profit in net_profit:
        remaining -= profit
        remaining_loan.append(remaining)

    remaining_loan = np.array(remaining_loan)
    cumulative_profit = np.cumsum(net_profit)
    net_balance = cumulative_profit - loan_amount  # 순수익 전환 시점 확인용

    # --------------------------
    # 표 구성
    # --------------------------
    df = pd.DataFrame({
        "연간 발전수익 (만원)": (yearly_profit/10_000).round(0).astype(int),
        "연간 유지비용 (만원)": (yearly_maintenance/10_000).round(0).astype(int),
        "연간 순수익 (만원)": (net_profit/10_000).round(0).astype(int),
        "잔여 원금/순수익 (만원)": (remaining_loan/10_000).round(0)
    }, index=[f"{i}년차" for i in range(1, loan_term_years+1)])

    # --------------------------
    # 색상 적용 (빨간: 원금 남음 / 검정: 순수익)
    # --------------------------
    def color_balance(val):
        return 'color: red' if val > 0 else 'color: black'

    st.subheader("📈 금융모델 (수익 및 상환현황)")
    st.dataframe(
        df.style.format("{:,}")
        .applymap(color_balance, subset=["잔여 원금/순수익 (만원)"]),
        width=900, height=500
    )

    # --------------------------
    # 순수익 전환 시점 표시
    # --------------------------
    payback_year = np.argmax(remaining_loan < 0) + 1 if np.any(remaining_loan < 0) else None
    if payback_year:
        st.success(f"✅ 순수익 전환 예상 시점: 약 {payback_year}년차")
    else:
        st.warning("❗ 20년 내 투자비 회수가 어려움")
