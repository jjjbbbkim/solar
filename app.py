import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="태양광 수익 계산기", layout="wide")
st.title("🌞 태양광 발전 수익 계산기")

# ===== 1. 발전 타입 선택 =====
st.sidebar.header("1️⃣ 발전소 타입")
plant_type = st.sidebar.selectbox("발전소 타입 선택", ["노지", "지붕"])

# ===== 2. 면적 입력 =====
st.sidebar.header("2️⃣ 면적 입력")
area_input_type = st.sidebar.radio("면적 입력 단위", ["평", "㎡"])
if area_input_type == "평":
    area = st.sidebar.number_input("면적(평)", min_value=1, step=1)
    area_m2 = area * 3.3
else:
    area_m2 = st.sidebar.number_input("면적(㎡)", min_value=1, step=1)
    area = int(area_m2 / 3.3)

# ===== 3. 발전용량 계산 =====
if plant_type == "노지":
    capacity = int((area / 3000) * 1000)
    rec_weight = 1.0
else:
    capacity = int((area / 2000) * 1000)
    rec_weight = 1.5

st.write(f"✅ 계산된 발전용량: {capacity} kW")
st.write(f"✅ 적용 REC 가중치: {rec_weight}")

# ===== 4. SMP/REC 단가 입력 =====
st.sidebar.header("3️⃣ 가격 입력")
smp_manual = st.sidebar.number_input("SMP 단가(원/kWh, 수동 입력)", value=120, step=1)
rec_price_mwh = st.sidebar.number_input("REC 단가(원/MWh)", value=65000, step=1)
rec_price = rec_price_mwh / 1000  # kWh 단위

# ===== 5. 전력거래소 SMP 월별 가격 가져오기 (수정) =====
smp_url = "https://new.kpx.or.kr/smpMonthly.es?mid=a10606080300&device=pc"
highlighted_smp = None

try:
    tables = pd.read_html(smp_url)
    smp_df = tables[0]

    # '구분' 컬럼이 포함된 행만 선택
    smp_df = smp_df[smp_df['구분'].str.contains('육지 SMP')]

    # '구분' 컬럼을 인덱스로 설정하고, 첫 번째 행을 컬럼명으로 설정
    smp_df.columns = smp_df.iloc[0]
    smp_df = smp_df.drop(0)

    # '2025년' 컬럼만 선택
    smp_df = smp_df[['2025년']]

    # 컬럼명을 '월별 SMP'로 변경
    smp_df.columns = ['월별 SMP']

    # 월별 SMP 가격을 정수로 변환
    smp_df['월별 SMP'] = smp_df['월별 SMP'].apply(pd.to_numeric, errors='coerce')

    # 이전 달 SMP 가격 강조
    current_month = datetime.now().month
    previous_month = current_month - 1 if current_month > 1 else 12
    highlighted_smp = smp_df.iloc[previous_month - 1, 0]

    st.subheader("📈 월별 SMP 가격")
    for idx, row in smp_df.iterrows():
        month_str = str(idx + 1) + "월"
        if idx + 1 == previous_month:
            st.markdown(f"**{month_str} SMP 가격 (이전 달 기준): {row['월별 SMP']:,} 원/kWh**")
        else:
            st.write(f"{month_str} SMP 가격: {row['월별 SMP']:,} 원/kWh")

except Exception as e:
    st.warning(f"SMP 데이터 불러오기 실패: {e}")
    highlighted_smp = smp_manual


# ===== 6. 금융 정보 입력 =====
st.sidebar.header("4️⃣ 금융 정보")
default_total_cost = int((capacity / 100) * 1200)  # 100kW당 1200만원
total_cost = st.sidebar.number_input("총 설치비용(만원)", value=default_total_cost, step=1)
self_ratio = st.sidebar.number_input("자기자본 비율(%)", value=20, step=1)
loan_amount = total_cost * (1 - self_ratio / 100)
interest_rate = 0.06
years_list = [5, 10, 20]

# ===== 7. 버튼 클릭 시 계산 =====
if st.button("💰 계산하기"):
    utilization_rate = 0.16
    annual_generation = capacity * 1000 * 24 * 365 * utilization_rate
    annual_smp = annual_generation * (highlighted_smp if highlighted_smp else smp_manual)
    annual_rec = annual_generation * rec_price * rec_weight
    annual_revenue = annual_smp + annual_rec

    st.subheader("📊 수익 결과")
    st.write(f"연간 발전량: {int(annual_generation):,} kWh")
    st.write(f"연간 SMP 수익: {int(annual_smp):,} 원")
    st.write(f"연간 REC 수익: {int(annual_rec):,} 원")
    st.write(f"총 연간 수익: {int(annual_revenue):,} 원")

    st.subheader("🏦 금융 상환 시뮬레이션")
    for years in years_list:
        n = years * 12
        r = interest_rate / 12
        monthly_payment = loan_amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        st.write(f"{years}년 상환 월 납부금: {int(monthly_payment):,} 만원")

