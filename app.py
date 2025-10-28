import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# 1️⃣ 페이지 설정
# -----------------------------
st.set_page_config(page_title="태양광 수익 & 금융 모델", layout="wide")
st.title("🌞 태양광 수익 & 금융 시뮬레이션")
st.caption("📅 기준: 하루 3.6시간 발전 기준, SMP/REC 단가 적용")

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

    months_array = np.arange(1, loan_term_years*12 + 1)
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원 단위

    # -----------------------------
    # 월별 유지비용 계산 (3.5% 시작, 매년 1% 증가)
    # -----------------------------
    base_maintenance_rate = 0.035
    monthly_maintenance_array = np.array([
        total_install_cost * base_maintenance_rate * (1.01 ** ((m-1)//12)) / 12
        for m in months_array
    ])

    # -----------------------------
    # 월별 발전량 (3.6시간/일, 30일 기준) + 효율 감소 0.4%/년
    # -----------------------------
    monthly_gen_array = capacity_kw * 3.6 * 30 * (1 - 0.004 * ((months_array-1)//12))

    # -----------------------------
    # 월별 수익
    # -----------------------------
    monthly_profit = monthly_gen_array * (smp_price + rec_price * rec_factor) - monthly_maintenance_array
    cumulative_profit = np.cumsum(monthly_profit)
    remaining_principal = np.maximum(total_install_cost - cumulative_profit, 0)

    # -----------------------------
    # 원리금 균등 상환 계산
    # -----------------------------
    r = interest_rate / 100 / 12
    n = loan_term_years * 12
    monthly_payment = total_install_cost * r * (1+r)**n / ((1+r)**n - 1)

    # 잔여원금 계산
    remaining_loan_array = []
    remaining = total_install_cost
    for mp in [monthly_payment]*len(months_array):
        remaining -= mp
        remaining_loan_array.append(max(remaining,0))
    remaining_loan_array = np.array(remaining_loan_array)

    # -----------------------------
    # 5️⃣ 금융 모델 표 (12개월 단위)
    # -----------------------------
    summary_df = pd.DataFrame({
        "총 누적 수익 (만원)": (cumulative_profit/10_000).round(0).astype(int),
        "남은 원금 (만원)": (remaining_principal/10_000).round(0),
        "월별 상환금 (만원)": (monthly_payment/10_000 + monthly_maintenance_array/10_000).round(0),
        "월별 유지비용 (만원)": (monthly_maintenance_array/10_000).round(0),
        "잔여 원금 (만원)": (remaining_loan_array/10_000).round(0)
    })

    # 12개월 단위로 필터링
    summary_df_display = summary_df[months_array % 12 == 0].reset_index(drop=True)
    # 운영연수 index 설정
    summary_df_display.index = [f"{i}년차" for i in range(1,len(summary_df_display)+1)]

    # 잔여원금 색상 적용
    def color_remaining(val):
        return 'color: red' if val > 0 else 'color: black'

    st.subheader("📈 금융 모델 (월별 상환 + 유지비용)")
    st.dataframe(summary_df_display.style.format("{:,}").applymap(color_remaining, subset=['잔여 원금 (만원)']), width=900, height=400)

    # -----------------------------
    # 6️⃣ 원리금 균등상환 표
    # -----------------------------
    st.subheader("🏦 원리금 균등상환")
    loan_df = pd.DataFrame({
        "월별 상환금 (만원)": round(monthly_payment / 10_000, 1),
        "월별 유지비용 (만원)": (monthly_maintenance_array/10_000).round(0),
        "잔여 원금 (만원)": (remaining_loan_array/10_000).round(0)
    })
    loan_df.index = [f"{i}년차" for i in range(1,len(loan_df)+1)]
    st.dataframe(loan_df.style.format("{:,}").applymap(color_remaining, subset=['잔여 원금 (만원)']), width=700, height=400)

    # -----------------------------
    # 7️⃣ 예상 회수기간
    # -----------------------------
    payback_month = np.argmax(remaining_principal == 0) + 1 if np.any(remaining_principal == 0) else None
    if payback_month:
        payback_years = payback_month / 12
        st.success(f"✅ 예상 회수기간: 약 {payback_years:.1f}년 ({payback_month}개월)")
    else:
        st.warning("❗ 대출 기간 내 투자비 회수가 어려움")



