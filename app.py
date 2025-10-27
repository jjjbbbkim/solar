import streamlit as st
import requests
from bs4 import BeautifulSoup
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
smp_price = st.sidebar.number_input("SMP 단가(원/kWh)", value=120, step=1)
rec_price_mwh = st.sidebar.number_input("REC 단가(원/MWh)", value=65000, step=1)
rec_price = rec_price_mwh / 1000  # kWh 단위로 변환

# ===== 5. 전력거래소 SMP 월별 가격 크롤링 =====
try:
    url = "https://www.kpx.or.kr/smpMonthly.es?mid=a10404080300&device=pc"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'tbl_type01'})
    rows = table.find_all('tr')[1:]  # 헤더 제외
    smp_data = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 1:
            month = cols[0].text.strip()
            price = int(cols[1].text.strip().replace(',', ''))
            smp_data.append((month, price))
except Exception as e:
    st.warning(f"SMP 데이터 크롤링 실패: {e}")
    smp_data = []

# 이전 달 SMP 강조 표시
previous_month = datetime.now().month - 1 if datetime.now().month > 1 else 12
highlighted_smp = None
st.subheader("📈 월별 SMP 가격")
for month, price in smp_data:
    try:
        month_num = int(month.split('-')[1])
    except:
        continue
    if month_num == previous_month:
        st.markdown(f"**{month} SMP 가격 (이전 달 기준): {price:,} 원/kWh**")
        highlighted_smp = price
    else:
        st.write(f"{month} SMP 가격: {price:,} 원/kWh")

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
    annual_smp = annual_generation * (highlighted_smp if highlighted_smp else smp_price)
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
