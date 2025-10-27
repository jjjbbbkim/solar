import streamlit as st
import pandas as pd

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
smp = st.sidebar.number_input("SMP 단가(원/kWh)", value=120.00, step=0.01)
rec_price = st.sidebar.number_input("REC 단가(원/kWh)", value=65.00, step=0.01)

# ===== 5️⃣ SMP 월별 가격 표시 (2행) =====
st.subheader("📊 2025년 육지 SMP 가격")
months = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월"]  # 필요시 12월까지 추가 가능
smp_values = [117.11, 116.39, 113.12, 124.63, 125.5, 118.02, 120.39, 117.39, 112.9]

smp_df = pd.DataFrame([months, smp_values], index=["월", "SMP 가격(원/kWh)"])
st.dataframe(smp_df.style.format("{:.2f}"), width=900, height=100)  # 가로 길이 늘려서 한눈에 보기

# ===== 6️⃣ 금융 정보 입력 =====
st.sidebar.header("4️⃣ 금융 정보")
default_total_cost = int((capacity / 100) * 1200)
total_cost = st.sidebar.number_input("총 설치비용(만원)", value=default_total_cost, step=1)
self_ratio = st.sidebar.number_input("자기자본 비율(%)", value=20, step=1)
loan_amount = total_cost * (1 - self_ratio / 100)
interest_rate = 0.06
years_list = [5, 10, 20]

# ===== 7️⃣ 수익 및 금융 계산 =====
if st.button("💰 계산하기"):
    utilization_rate = 0.16
    annual_generation = capacity * 1000 * 24 * 365 * utilization_rate

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
