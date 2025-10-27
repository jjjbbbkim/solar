import streamlit as st

st.set_page_config(page_title="태양광 수익 계산기", layout="wide")

st.title("🌞 태양광 발전 수익 계산기")

# ===== 1. 발전 타입 선택 =====
st.sidebar.header("1️⃣ 발전소 타입")
plant_type = st.sidebar.selectbox("발전소 타입 선택", ["노지", "지붕"])

# ===== 2. 면적 입력 =====
st.sidebar.header("2️⃣ 면적 입력")
area_input_type = st.sidebar.radio("면적 입력 단위", ["평", "㎡"])
if area_input_type == "평":
    area = st.sidebar.number_input("면적(평)", min_value=1.0, step=1.0)
    area_m2 = area * 3.3
else:
    area_m2 = st.sidebar.number_input("면적(㎡)", min_value=1.0, step=1.0)
    area = area_m2 / 3.3

# ===== 3. 발전용량 계산 =====
if plant_type == "노지":
    capacity = (area / 3000) * 1000  # kW
    rec_weight = 1.0
else:
    capacity = (area / 2000) * 1000  # kW
    rec_weight = 1.5

st.write(f"✅ 계산된 발전용량: {capacity:.2f} kW")
st.write(f"✅ 적용 REC 가중치: {rec_weight}")

# ===== 4. SMP/REC 단가 입력 =====
st.sidebar.header("3️⃣ 가격 입력")
smp_price = st.sidebar.number_input("SMP 단가(원/kWh)", value=120.0)
rec_price = st.sidebar.number_input("REC 단가(원/REC)", value=65000.0)

# ===== 5. 금융 정보 입력 =====
st.sidebar.header("4️⃣ 금융 정보")
total_cost = st.sidebar.number_input("총 설치비용(원)", value=1_300_000_000)
self_ratio = st.sidebar.number_input("자기자본 비율(%)", value=20)
loan_amount = total_cost * (1 - self_ratio/100)
interest_rate = 0.06  # 연 6%
years_list = [5, 10, 20]

# ===== 6. 버튼 클릭 시 계산 =====
if st.button("💰 계산하기"):
    # 연간 발전량
    utilization_rate = 0.16  # 예시 16% 이용률
    annual_generation = capacity * 1000 * 24 * 365 * utilization_rate / 1000  # kWh
    annual_smp = annual_generation * smp_price
    annual_rec = annual_generation * rec_price * rec_weight
    annual_revenue = annual_smp + annual_rec

    st.subheader("📊 수익 결과")
    st.write(f"연간 발전량: {annual_generation:,.2f} kWh")
    st.write(f"연간 SMP 수익: {annual_smp:,.0f} 원")
    st.write(f"연간 REC 수익: {annual_rec:,.0f} 원")
    st.write(f"총 연간 수익: {annual_revenue:,.0f} 원")

    # ===== 월별 상환 계산 =====
    st.subheader("🏦 금융 상환 시뮬레이션")
    for years in years_list:
        n = years * 12
        r = interest_rate / 12
        monthly_payment = loan_amount * (r * (1+r)**n) / ((1+r)**n - 1)
        st.write(f"{years}년 상환 월 납부금: {monthly_payment:,.0f} 원")
