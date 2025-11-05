import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------
# 1️⃣ 페이지 설정
# -----------------------------
st.set_page_config(page_title="태양광 금융모델 (순수익 상환형)", layout="wide")
st.title("🌞 태양광 금융모델 (순수익 상환형)")
st.caption("📊 1년차 이자만 상환, 2년차부터 순수익으로 대출상환")

# -----------------------------
# 2️⃣ 발전소 정보 입력
# -----------------------------
st.header("📝 발전소 기본 정보")

# 단위 선택
area_unit = st.radio("입력 단위 선택", ["평", "㎡"], horizontal=True)

if area_unit == "평":
    area_py = st.number_input("부지 면적 (평)", min_value=1, value=3000, step=1)
    area_m2 = area_py * 3.3
else:
    area_m2 = st.number_input("부지 면적 (㎡)", min_value=1, value=10000, step=1)
    area_py = area_m2 / 3.3

st.write(f"면적 변환: **{area_py:.0f} 평 / {area_m2:.0f} ㎡**")

# 발전소 타입
plant_type = st.selectbox("발전소 타입", ["노지형", "지붕형"])
if plant_type == "노지형":
    rec_factor = 1.0
    base_area = 3000
    install_cost_per_100kw = 12000  # 만원
else:
    rec_factor = 1.5
    base_area = 2000
    install_cost_per_100kw = 10000  # 만원
    st.caption(f"REC 가중치 1.5 적용 → REC 단가 × 1.5 = **{round(71.97*1.5, 1)} 원/kWh**")

capacity_kw = area_py / base_area * 1000
st.write(f"📐 계산된 발전용량: **{capacity_kw:.0f} kW**")

# 단가 입력
smp_price = st.number_input("SMP 단가 (원/kWh)", value=112.9)
rec_price = st.number_input("REC 단가 (원/kWh)", value=71.97)

# -----------------------------
# 3️⃣ 금융 정보 입력
# -----------------------------
st.header("💰 금융 정보")

interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
loan_term_years = st.number_input("대출 상환기간 (년)", value=20)
loan_ratio = st.number_input("총 사업비 대비 대출 비율 (%)", value=80)

# -----------------------------
# 4️⃣ 계산 버튼
# -----------------------------
if st.button("계산하기"):
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원 단위
    loan_amount = total_install_cost * loan_ratio / 100
    st.subheader("💵 투자 개요")
    st.write(f"총 사업비: **{total_install_cost:,.0f} 원**")
    st.write(f"대출금액 ({loan_ratio}%): **{loan_amount:,.0f} 원**")

    # -----------------------------
    # 5️⃣ 연도별 수익 및 상환 계산
    # -----------------------------
    r = interest_rate / 100
    remaining_loan = loan_amount

    results = []
    base_maintenance_rate = 0.03
    base_revenue = capacity_kw * 3.6 * 365 * (smp_price + rec_price * rec_factor)  # 1년차 기준 발전수익

    for year in range(1, loan_term_years + 1):
        # 발전효율 감소
        efficiency = 1 - 0.004 * (year - 1)
        annual_generation = capacity_kw * 3.6 * 365 * efficiency
        annual_revenue = annual_generation * (smp_price + rec_price * rec_factor)

        # 유지비용 (1년차 3%, 이후 연 1%씩 증가)
        maintenance = base_revenue * base_maintenance_rate * (1.01 ** (year - 1))

        # 순수익 (세전)
        net_profit = annual_revenue - maintenance

        # 연간 이자
        interest_payment = remaining_loan * r

        # 1년차는 이자만 상환
        if year == 1:
            repayment = interest_payment
            principal_payment = 0
        else:
            principal_payment = min(net_profit, remaining_loan)
            repayment = interest_payment + principal_payment
            remaining_loan -= principal_payment

        # 잔여대출이 모두 상환되면 순수익 흑자 계산
        surplus = 0
        if remaining_loan == 0:
            surplus = max(net_profit - interest_payment, 0)

        results.append({
            "연도": f"{year}년차",
            "발전수익 (만원)": round(annual_revenue / 10_000),
            "유지비용 (만원)": round(maintenance / 10_000),
            "순수익 (만원)": round(net_profit / 10_000),
            "이자 (만원)": round(interest_payment / 10_000),
            "상환금 (만원)": round(repayment / 10_000),
            "잔여대출 (만원)": round(remaining_loan / 10_000),
            "순수익(흑자) (만원)": round(surplus / 10_000)
        })

        if remaining_loan <= 0:
            break  # 대출 상환 완료 시 종료

    # -----------------------------
    # 6️⃣ 표로 출력
    # -----------------------------
    df = pd.DataFrame(results)
    df.set_index("연도", inplace=True)

    def color_loan(val):
        return 'color: red' if val > 0 else 'color: black'

    st.subheader("📈 금융모델 (연간 순수익 상환 방식)")
    st.dataframe(df.style.format("{:,}")
                 .applymap(color_loan, subset=["잔여대출 (만원)"]),
                 width=950, height=500)

    # -----------------------------
    # 7️⃣ 회수기간 표시
    # -----------------------------
    payback_year = next((i+1 for i, v in enumerate(df["잔여대출 (만원)"]) if v == 0), None)
    if payback_year:
        st.success(f"✅ 예상 대출 완전 상환 시점: {payback_year}년차")
    else:
        st.warning("❗ 20년 내 대출 상환이 완료되지 않습니다.")
