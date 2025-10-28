import streamlit as st
import pandas as pd
import numpy as np

# matplotlib 자동 설치 (Streamlit Cloud 호환용)
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    import os
    os.system("pip install matplotlib")
    import matplotlib.pyplot as plt

# -----------------------------
# 1️⃣ 기본 데이터 (2025년 기준 SMP, REC 단가)
# -----------------------------
data = {
    "월": ["1월","2월","3월","4월","5월","6월","7월","8월","9월"],
    "SMP(원/kWh)": [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90],
    "REC(원/kWh)": [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97],
}
smp_df = pd.DataFrame(data)

# -----------------------------
# 2️⃣ 기본정보
# -----------------------------
st.title("태양광 수익성 분석 대시보드")
st.caption("📅 기준: 하루 3.6시간 발전 기준 (2025년 9월 SMP 112.9원 기준)")

# 발전소 타입 선택
type_choice = st.radio("발전소 타입 선택", ["노지형", "지붕형"], horizontal=True)

if type_choice == "노지형":
    install_cost = 120_000_000  # 1.2억원
    rec_factor = 1.0
else:
    install_cost = 100_000_000  # 1억원
    rec_factor = 1.5
    st.info("지붕형은 REC 가중치 1.5가 적용됩니다.")

# -----------------------------
# 3️⃣ SMP·REC 월별 단가표
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
# 5️⃣ 기간별 수익 계산
# -----------------------------
months = np.arange(1, 121)  # 10년 = 120개월
monthly_smp = np.mean(smp_df["SMP(원/kWh)"])
monthly_rec = np.mean(smp_df["REC(원/kWh)"])

# 월별 수익 & 누적 수익
monthly_profit = calc_monthly_profit(monthly_smp, monthly_rec, rec_factor=rec_factor)
cumulative_profit = monthly_profit * months
remaining_principal = install_cost - cumulative_profit
remaining_principal = np.maximum(remaining_principal, 0)  # 0 이하 방지

# -----------------------------
# 6️⃣ 그래프 ① 기간별 총 수익
# -----------------------------
st.subheader("💰 기간별 총 수익 (누적)")
fig1, ax1 = plt.subplots(figsize=(7,4))
ax1.plot(months, cumulative_profit / 1_000_000, color="green", linewidth=2.5)
ax1.set_title("기간별 총 누적 수익 (단위: 백만원)", fontsize=13, weight="bold")
ax1.set_xlabel("운영 개월 수")
ax1.set_ylabel("총 누적 수익 (백만원)")
ax1.grid(True, linestyle="--", alpha=0.5)
st.pyplot(fig1)

# -----------------------------
# 7️⃣ 그래프 ② 남은 원금 변화
# -----------------------------
st.subheader("📉 남은 원금 변화")
fig2, ax2 = plt.subplots(figsize=(7,4))
ax2.plot(months, remaining_principal / 1_000_000, color="red", linewidth=2)
ax2.set_title("남은 원금 변화 추이 (단위: 백만원)", fontsize=13, weight="bold")
ax2.set_xlabel("운영 개월 수")
ax2.set_ylabel("남은 원금 (백만원)")
ax2.grid(True, linestyle="--", alpha=0.5)
st.pyplot(fig2)

# -----------------------------
# 8️⃣ 요약 표시
# -----------------------------
payback_month = np.argmax(remaining_principal == 0) + 1 if np.any(remaining_principal == 0) else None
if payback_month:
    payback_years = payback_month / 12
    st.success(f"✅ 예상 회수기간: 약 {payback_years:.1f}년 ({payback_month}개월)")
else:
    st.warning("❗ 10년 내 투자비 회수가 어려움")
