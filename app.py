import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# 1️⃣ 기본 데이터 (2025년 SMP, REC 단가)
# -----------------------------
data = {
    "월": ["1월","2월","3월","4월","5월","6월","7월","8월","9월"],
    "SMP(원/kWh)": [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90],
    "REC(원/kWh)": [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97],
}
smp_df = pd.DataFrame(data)

# -----------------------------
# 2️⃣ 기본정보 입력
# -----------------------------
st.title("태양광 수익성 분석 대시보드")
st.caption("📅 기준: 하루 3.6시간 발전 기준 (2025년 9월 SMP 112.9원 기준)")

# 발전소 타입
type_choice = st.radio("발전소 타입 선택", ["노지형", "지붕형"], horizontal=True)

if type_choice == "노지형":
    install_cost = 120_000_000  # 1.2억
    rec_factor = 1.0
else:
    install_cost = 100_000_000  # 1억
    rec_factor = 1.5
    st.info("지붕형은 REC 가중치 1.5가 적용됩니다.")

# -----------------------------
# 3️⃣ SMP·REC 단가표
# -----------------------------
st.subheader("📊 월별 SMP·REC 단가표")
st.dataframe(
    smp_df.style.format({"SMP(원/kWh)":"{:.2f}", "REC(원/kWh)":"{:.2f}"}),
    width=500, height=250
)

# -----------------------------
# 4️⃣ 수익 계산 함수
# -----------------------------
def calc_monthly_profit(smp, rec, capacity_kw=100, hours=3.6, rec_factor=1.0):
    """월간 순수익 계산 (원 단위)"""
    monthly_gen = capacity_kw * hours * 30  # kWh
    revenue = (smp + rec * rec_factor) * monthly_gen
    return revenue

# -----------------------------
# 5️⃣ 10년(120개월) 수익 및 원금 계산
# -----------------------------
months = np.arange(1, 121)
monthly_smp = np.mean(smp_df["SMP(원/kWh)"])
monthly_rec = np.mean(smp_df["REC(원/kWh)"])

# 월별 수익 및 누적 계산
monthly_profit = calc_monthly_profit(monthly_smp, monthly_rec, rec_factor=rec_factor)
cumulative_profit = monthly_profit * months
remaining_principal = install_cost - cumulative_profit
remaining_principal = np.maximum(remaining_principal, 0)

# -----------------------------
# 6️⃣ 표로 표시
# -----------------------------
st.subheader("📅 기간별 총 수익 및 남은 원금")

summary_df = pd.DataFrame({
    "운영 개월": months,
    "총 누적 수익 (만원)": (cumulative_profit / 10_000).round(1),
    "남은 원금 (만원)": (remaining_principal / 10_000).round(1)
})

# 보기 쉽게 12개월 단위로 나누어 표시 (1년 간격)
summary_df_display = summary_df[summary_df["운영 개월"] % 12 == 0].reset_index(drop=True)
summary_df_display["운영 연수"] = (summary_df_display["운영 개월"] / 12).astype(int)
summary_df_display = summary_df_display[["운영 연수", "총 누적 수익 (만원)", "남은 원금 (만원)"]]

st.dataframe(summary_df_display.style.format("{:.1f}"), width=500, height=300)

# -----------------------------
# 7️⃣ 회수기간 계산
# -----------------------------
payback_month = np.argmax(remaining_principal == 0) + 1 if np.any(remaining_principal == 0) else None
if payback_month:
    payback_years = payback_month / 12
    st.success(f"✅ 예상 회수기간: 약 {payback_years:.1f}년 ({payback_month}개월)")
else:
    st.warning("❗ 10년 내 투자비 회수가 어려움")
