import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# 1️⃣ 페이지 설정
# -----------------------------
st.set_page_config(page_title="태양광 수익 & 금융 모델", layout="wide")
st.title("🌞 태양광 수익 & 금융 시뮬레이션")
st.caption("📅 기준: 하루 3.6시간 발전 기준, 2025년 9월 SMP 112.9원, REC 71.97원 기준")

# -----------------------------
# 2️⃣ 월별 SMP/REC 단가표
# -----------------------------
st.header("📊 월별 SMP/REC 단가표")
data = {
    "월": ["1월","2월","3월","4월","5월","6월","7월","8월","9월"],
    "SMP(원/kWh)": [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90],
    "REC(원/kWh)": [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97],
}
smp_df = pd.DataFrame(data)
st.dataframe(smp_df.style.format({"SMP(원/kWh)":"{:.2f}", "REC(원/kWh)":"{:.2f}"}), width=500, height=250)

# -----------------------------
# 3️⃣ 입력 정보
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

    months = np.arange(1, loan_term_years*12 + 1)
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원 단위

    # 월별 유지비용 (총 사업비의 3% ÷ 12)
    monthly_maintenance = total_install_cost * 0.03 / 12

    # 월별 발전량 (3.6시간/일, 30일 기준) + 효율 감소 0.4%/년
    monthly_gen_list = []
    for m in months:
        year = (m-1)//12  # 경과 년수
        efficiency_factor = 1 - 0.004 * year  # 연 0.4% 감소
        monthly_gen = capacity_kw * 3.6 * 30 * efficiency_factor
        monthly_gen_list.append(monthly_gen)
    monthly_gen_array = np.array(monthly_gen_list)

    # 월별 수익
    monthly_profit = monthly_gen_array * (smp_price + rec_price * rec_factor) - monthly_maintenance
    cumulative_profit = np.cumsum(monthly_profit)
    remaining_principal = np.maximum(total_install_cost - cumulative_profit, 0)

    # 원리금 균등 상환
    r = interest_rate / 100 / 12
    n = loan_term_years * 12
    monthly_payment = total_install_cost * r * (1+r)**n / ((1+r)**n - 1)
    remaining_loan = total_install_cost - np.cumsum([monthly_payment]*len(months))

    # -----------------------------
    # 5️⃣ 투자금 기반 금융 모델 표
    # -----------------------------
    st.subheader("📈 투자금 기준 금융 모델")
    st.caption("※ 유지비용 3%, 발전효율 연 0.4% 감소 적용")
    summary_df = pd.DataFrame({
        "월": months,
        "총 누적 수익 (만원)": (cumulative_profit / 10_000).round(1),
        "남은 원금 (만원)": (remaining_principal / 10_000).round(1),
        "월별 상환금 (만원)": round(monthly_payment / 10_000,1),
        "잔여 원금 (만원)": (remaining_loan / 10_000).round(1)
    })
    summary_df_display = summary_df[summary_df["월"] % 12 == 0].reset_index(drop=True)
    summary_df_display["운영 연수"] = (summary_df_display["월"] / 12).astype(int)
    summary_df_display = summary_df_display[["운영 연수", "총 누적 수익 (만원)", "남은 원금 (만원)",
                                             "월별 상환금 (만원)", "잔여 원금 (만원)"]]
    st.dataframe(summary_df_display, width=800, height=400)

    # -----------------------------
    # 6️⃣ 20년 원리금 균등 상환 + 유지비용 포함
    # -----------------------------
    st.subheader("🏦 20년 원리금 균등상환 + 유지비용")
    st.caption("※ 유지비용 3%, 발전효율 연 0.4% 감소 적용")
    loan_df = pd.DataFrame({
        "월": months,
        "월별 상환금 (만원)": round(monthly_payment / 10_000 + monthly_maintenance / 10_000, 1),
        "잔여 원금 (만원)": (remaining_loan / 10_000).round(1)
    })
    loan_df_display = loan_df[loan_df["월"] % 12 == 0].reset_index(drop=True)
    loan_df_display["운영 연수"] = (loan_df_display["월"]/12).astype(int)
    loan_df_display = loan_df_display[["운영 연수", "월별 상환금 (만원)", "잔여 원금 (만원)"]]
    st.dataframe(loan_df_display, width=600, height=400)

    # -----------------------------
    # 7️⃣ 예상 회수기간
    # -----------------------------
    payback_month = np.argmax(remaining_principal == 0) + 1 if np.any(remaining_principal == 0) else None
    if payback_month:
        payback_years = payback_month / 12
        st.success(f"✅ 예상 회수기간: 약 {payback_years:.1f}년 ({payback_month}개월)")
    else:
        st.warning("❗ 대출 기간 내 투자비 회수가 어려움")
