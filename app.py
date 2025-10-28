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
# 2️⃣ 입력 정보 (한 페이지)
# -----------------------------
st.header("📝 입력 정보")

# 발전소 타입
plant_type = st.selectbox("발전소 타입", ["노지형", "지붕형"])
if plant_type == "노지형":
    rec_factor = 1.0
    base_area = 3000  # 평당 1MW
    install_cost_per_100kw = 12000  # 만원
else:
    rec_factor = 1.5
    base_area = 2000
    install_cost_per_100kw = 10000  # 만원
st.write(f"REC 가중치: {rec_factor}")

# 부지 면적
area_py = st.number_input("부지 면적 (평)", min_value=1, value=3000, step=1)
area_m2 = area_py * 3.3
capacity_kw = area_py / base_area * 1000
st.write(f"계산된 발전용량: {capacity_kw:.0f} kW ({area_m2:.0f} ㎡)")

# SMP & REC 단가
smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)

# 금융 정보
st.header("💰 금융 정보")
interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
loan_term_years = st.number_input("대출 상환기간 (년)", value=20)

# 계산 버튼
if st.button("계산하기"):

    # -----------------------------
    # 3️⃣ 월별 수익 & 상환 계산
    # -----------------------------
    months = np.arange(1, loan_term_years*12 + 1)
    monthly_gen = capacity_kw * 3.6 * 30  # kWh, 하루 3.6시간, 30일 기준
    monthly_profit = monthly_gen * (smp_price + rec_price * rec_factor)  # 원 단위

    # 누적 수익
    cumulative_profit = monthly_profit * months

    # 총 설치비용
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원 단위

    # 원리금 균등 상환 계산
    r = interest_rate / 100 / 12  # 월 이자율
    n = loan_term_years * 12
    monthly_payment = total_install_cost * r * (1+r)**n / ((1+r)**n - 1)
    remaining_loan = total_install_cost - np.cumsum([monthly_payment]*len(months))

    # 남은 원금
    remaining_principal = np.maximum(total_install_cost - cumulative_profit, 0)

    # -----------------------------
    # 4️⃣ 표 만들기
    # -----------------------------
    st.subheader("📊 월별 수익 & 금융 상환 모델")
    summary_df = pd.DataFrame({
        "월": months,
        "총 누적 수익 (만원)": (cumulative_profit / 10_000).round(1),
        "남은 원금 (만원)": (remaining_principal / 10_000).round(1),
        "월별 상환금 (만원)": round(monthly_payment / 10_000, 1),
        "잔여 원금 (만원)": (remaining_loan / 10_000).round(1)
    })

    # 12개월 단위로 표시
    summary_df_display = summary_df[summary_df["월"] % 12 == 0].reset_index(drop=True)
    summary_df_display["운영 연수"] = (summary_df_display["월"] / 12).astype(int)
    summary_df_display = summary_df_display[["운영 연수", "총 누적 수익 (만원)", "남은 원금 (만원)",
                                             "월별 상환금 (만원)", "잔여 원금 (만원)"]]

    st.dataframe(summary_df_display, width=800, height=400)

    # -----------------------------
    # 5️⃣ 예상 회수기간
    # -----------------------------
    payback_month = np.argmax(remaining_principal == 0) + 1 if np.any(remaining_principal == 0) else None
    if payback_month:
        payback_years = payback_month / 12
        st.success(f"✅ 예상 회수기간: 약 {payback_years:.1f}년 ({payback_month}개월)")
    else:
        st.warning("❗ 대출 기간 내 투자비 회수가 어려움")
