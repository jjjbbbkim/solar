import streamlit as st
import pandas as pd

# 페이지 기본 설정
st.set_page_config(page_title="태양광 수익 계산기", layout="wide")
st.title("🌞 태양광 수익 계산기 (2025년 기준, 3.6시간 발전 기준)")

# -----------------------
# 1️⃣ SMP & REC 표 (2025년 1~9월 데이터)
# -----------------------
months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
smp_values = [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90,None,None,None]
rec_values = [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97,None,None,None]

smp_rec_df = pd.DataFrame({
    "월": months,
    "SMP 가격(원/kWh)": smp_values,
    "REC 가격(원/kWh)": rec_values
})

# 강조 함수 (최고 빨강, 최저 파랑)
def highlight_extremes(val, column):
    if pd.isna(val): 
        return ''
    col_max = smp_rec_df[column].max()
    col_min = smp_rec_df[column].min()
    if val == col_max:
        return 'color: red; font-weight: bold'
    elif val == col_min:
        return 'color: blue; font-weight: bold'
    else:
        return ''

# 스타일 적용
smp_style = (
    smp_rec_df.style
    .format({"SMP 가격(원/kWh)": "{:.2f}", "REC 가격(원/kWh)": "{:.2f}"})
    .applymap(lambda v: highlight_extremes(v, "SMP 가격(원/kWh)"), subset=["SMP 가격(원/kWh)"])
    .applymap(lambda v: highlight_extremes(v, "REC 가격(원/kWh)"), subset=["REC 가격(원/kWh)"])
)

st.markdown("### 📊 2025년 월별 육지 SMP & REC 단가 (3.6시간 발전 기준)")
st.table(smp_style.hide(axis="index"))  # ✅ 인덱스 숨김

# 기준 단가 (9월)
current_smp = 112.90
current_rec = 71.97

# -----------------------
# 2️⃣ 발전소 타입 선택
# -----------------------
st.markdown("### ⚙️ 1. 발전소 타입 선택")
plant_type = st.radio("발전소 타입을 선택하세요", ["노지", "지붕"])

if plant_type == "노지":
    rec_weight = 1.0
    base_area = 3000  # 평당 1MW
    install_cost_per_100kw = 12000  # 1.2억 (만원 단위)
else:
    rec_weight = 1.5
    base_area = 2000
    install_cost_per_100kw = 10000  # 1.0억 (만원 단위)

# -----------------------
# 3️⃣ 부지 면적 입력
# -----------------------
st.markdown("### 📐 2. 부지 면적 입력")
area_py = st.number_input("면적 (평)", min_value=1, value=3000, step=1)
area_m2 = area_py * 3.3
st.write(f"면적(㎡): {area_m2:,.0f} ㎡")

capacity_kw = area_py / base_area * 1000
st.success(f"예상 발전용량: {capacity_kw:.0f} kW")

# -----------------------
# 4️⃣ SMP & REC 단가 입력
# -----------------------
st.markdown("### ⚡ 3. SMP & REC 단가")
smp = st.number_input("SMP 단가 (원/kWh)", value=float(current_smp))
rec = st.number_input("REC 단가 (원/kWh)", value=float(current_rec))
st.info(f"※ 기준 단가: 2025년 9월 SMP {current_smp}원/kWh, REC {current_rec}원/kWh 반영")

# -----------------------
# 5️⃣ 금융 정보
# -----------------------
st.markdown("### 💰 4. 금융 정보")
interest_rate = 6.0  # %
loan_term = 20  # 년
repay_options = [5, 10]

# -----------------------
# 6️⃣ 계산하기
# -----------------------
if st.button("💡 수익 계산하기"):
    # 설치비용
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw  # 만원 단위
    
    # 연간 발전량 (3.6시간 기준)
    annual_gen_kwh = capacity_kw * 3.6 * 365
    
    # 연간 수익
    annual_revenue = annual_gen_kwh * (smp + rec * rec_weight)
    
    # 원금 회수 기간
    payback_years = (total_install_cost * 10000) / annual_revenue

    st.subheader("📈 계산 결과")
    st.write(f"총 설치비용: {total_install_cost:,.0f} 만원 ({'노지' if plant_type == '노지' else '지붕'} 기준)")
    st.write(f"연간 예상 발전량: {annual_gen_kwh:,.0f} kWh (**3.6시간 기준**)")
    st.write(f"연간 예상 수익: {annual_revenue:,.0f} 원")
    st.write(f"원금 회수 기간: {payback_years:.1f} 년")

    st.markdown("#### 💳 원리금 상환 시뮬레이션")
    for repay_year in repay_options:
        monthly_payment = (total_install_cost * (1 + interest_rate/100)) / (repay_year * 12)
        st.write(f"{repay_year}년 상환 시 월 납입금: {monthly_payment:,.0f} 만원")
