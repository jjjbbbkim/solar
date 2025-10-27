import streamlit as st
import pandas as pd

# ===== 페이지 설정 =====
st.set_page_config(page_title="태양광 수익 계산기", layout="wide")
st.title("🌞 태양광 발전 수익 계산기")

# ===== 1️⃣ 발전소 타입 선택 =====
st.sidebar.header("1️⃣ 발전소 타입")
plant_type = st.sidebar.selectbox("발전소 타입 선택", ["노지", "지붕"])

# ===== 2️⃣ 면적 입력 =====
st.sidebar.header("2️⃣ 면적 입력")
area_input_type = st.sidebar.radio("면적 입력 단위", ["평", "㎡"])
if area_input_type == "평":
    area = st.sidebar.number_input("면적(평)", min_value=1, step=1)
    area_m2 = area * 3.3
else:
    area_m2 = st.sidebar.number_input("면적(㎡)", min_value=1, step=1)
    area = int(area_m2 / 3.3)

# ===== 3️⃣ 발전용량 계산 =====
if plant_type == "노지":
    capacity = int((area / 3000) * 1000)
    rec_weight = 1.0
else:
    capacity = int((area / 2000) * 1000)
    rec_weight = 1.5

st.write(f"✅ 계산된 발전용량: {capacity} kW")
st.write(f"✅ 적용 REC 가중치: {rec_weight}")

# ===== 4️⃣ SMP/REC 단가 입력 =====
st.sidebar.header("3️⃣ 가격 입력")
default_smp = 112.9  # 9월 SMP 기준
smp = st.sidebar.number_input("SMP 단가(원/kWh)", value=default_smp, step=0.01)
rec_price = st.sidebar.number_input("REC 단가(원/kWh)", value=65.00, step=0.01)

# ===== 5️⃣ SMP 월별 가격 표시 (2열 세로표, 강조) =====
st.subheader("📊 2025년 육지 SMP 가격")

months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월"]
smp_values = [117.11,116.39,113.12,124.63,125.5,118.02,120.39,117.39,112.9]

smp_df = pd.DataFrame({
    "월": months,
    "SMP 가격(원/kWh)": smp_values
})

# 강조 함수: 최고값 빨강, 최저값 파랑
def highlight_extremes(val):
    if val == smp_df["SMP 가격(원/kWh)"].max():
        return 'color: red; font-weight: bold'
    elif val == smp_df["SMP 가격(원/kWh)"].min():
        return 'color: blue; font-weight: bold'
    else:
        return ''

# 2열 세로표 출력 (인덱스 제거)
st.table(
    smp_df.style.applymap(highlight_extremes, subset=["SMP 가격(원/kWh)"])
    .format({"SMP 가격(원/kWh)":"{:.2f}"})
)

# ===== 6️⃣ 금융 정보 입력 =====
st.sidebar.header("4️⃣ 금융 정보")
default_total_cost = int((capacity / 100) * 1200)  # 100kW당 1200만원
total_cost = st.sidebar.number_input("총 설치비용(만원)", value=default_total_cost, step=1)
self_ratio = st.sidebar.number_input("자기자본 비율(%)", value=20, step=1)
loan_amount = total_cost * (1 - self_ratio / 100)
interest_rate = 0.06
years_list = [5, 10, 20]

# ===== 7️⃣ 수익 및 금융 계산 =====
if st.button("💰 계산하기"):
    utilization_rate = 0.16  # 연간 평균 발전률
    annual_generation = capacity * 1000 * 24 * 365 * utilization_rate  # kWh

    annual_smp = annual_generation * smp
    annual_rec = annual_generation * rec_price * rec_weight
    annual_revenue = annual_smp + annual_rec

    st.subheader("📊 수익 결과")
    st.write(f"연간 발전량: {int(annual_generation):,} kWh")
    st.write(f"연간 SMP 수익: {annual_smp:,.2f} 원")
    st.write(f"연간 REC 수익: {annual_rec:,.2f} 원")
    st.write(f"총 연간 수익: {annual_revenue:,.2f} 원")

    st.subheader("🏦 금융 상환 시뮬레이션")
    for years in years_list:
        n = years * 12
        r = interest_rate / 12
        monthly_payment = loan_amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        st.write(f"{years}년 상환 월 납부금: {monthly_payment:,.2f} 만원")
