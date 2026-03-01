import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="태양광 금융 시뮬레이션", layout="wide")
st.title("🌞 태양광 금융 시뮬레이션")

# =========================
# 참고용 SMP/REC 단가표(예시)
# =========================
months = [f"{i}월" for i in range(1, 13)]
smp_values = [117.11, 116.39, 113.12, 124.63, 125.50, 118.02, 120.39, 117.39, 112.90, 101.53, 94.81, 90.44]
rec_values = [69.76, 72.16, 72.15, 72.41, 72.39, 71.96, 71.65, 71.86, 71.97, 72.31, 72.14, 72.29]
smp_df = pd.DataFrame({"SMP(원/kWh)": smp_values, "REC(원/kWh)": rec_values}, index=months)

st.subheader("📊 SMP / REC 단가표")
st.caption("참고용(과거 추이)입니다. 실제 계산은 아래에서 입력한 SMP/REC 단가 1회 값으로 20년 동일 단가로 계산합니다.")
st.dataframe(smp_df.style.format("{:.2f}"), width=420, height=260)

# =========================
# 입력
# =========================
st.header("📝 기본 입력값")

area_unit = st.radio("면적 단위", ["평", "㎡"], horizontal=True)
if area_unit == "평":
    area_py = st.number_input("부지 면적 (평)", value=3000, min_value=1, step=1)
    area_m2 = area_py * 3.3
else:
    area_m2 = st.number_input("부지 면적 (㎡)", value=9900, min_value=1, step=1)
    area_py = area_m2 / 3.3
st.write(f"면적: {area_py:,.0f} 평 (≈ {area_m2:,.0f}㎡)")

plant_type = st.selectbox("발전소 타입", ["노지형", "지붕형"])
if plant_type == "노지형":
    rec_factor = 1.0
    base_area = 3000
    install_cost_per_100kw = 12000
else:
    rec_factor = 1.5
    base_area = 2000
    install_cost_per_100kw = 10000
    st.info(f"지붕형 REC 가중치 적용: REC × {rec_factor}")

capacity_kw = area_py / base_area * 1000
st.write(f"예상 발전용량: {capacity_kw:.0f} kW")

# 단가/금융
smp_price = st.number_input("SMP 단가 (원/kWh) - 1회 입력(20년 고정)", value=101.16)
rec_price = st.number_input("REC 단가 (원/kWh) - 1회 입력(20년 고정)", value=72.31)
interest_rate = st.number_input("대출 이자율 (%)", value=6.0)
operation_years = st.number_input("운영연수 (년)", value=20, min_value=1, step=1)
loan_ratio = st.number_input("대출 비율 (%)", value=80, min_value=0, max_value=100)

st.divider()

# 유지보수(용량 고정비)
st.subheader("🛠 유지보수(O&M) 입력")
st.caption("유지보수비는 용량 기준 고정비로 가정합니다. (SMP/REC와 무관)")
om_unit_cost_mankw_per_kw_year = st.number_input(
    "유지보수 단가 (만원 / kW · 년)",
    value=3.0,
    min_value=0.0,
    step=0.1,
    help="예: 3.0 입력 = 1kW당 연 3만원"
)
om_inflation = st.number_input("유지보수비 물가 반영률(%)", value=1.0, min_value=0.0, step=0.1)

st.divider()

# =========================
# 계산
# =========================
if st.button("계산하기"):
    # 총 사업비, 대출금
    total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원
    loan_amount = total_install_cost * loan_ratio / 100
    equity_amount = total_install_cost - loan_amount

    st.write(f"💰 총 사업비: {total_install_cost:,.0f} 원")
    st.write(f"🏦 대출금액: {loan_amount:,.0f} 원")
    st.write(f"👤 자기자본(참고): {equity_amount:,.0f} 원")

    # 기본 변수
    r = interest_rate / 100
    remaining_loan = float(loan_amount)

    cumulative_cash = 0.0  # (상환 후 남은 현금) 누적

    # 1년차 기준 발전량/매출
    # 업계 평균 가정: 일 평균 발전시간 3.6h
    base_annual_gen_kwh = capacity_kw * 3.6 * 365  # kWh/year

    # 유지비(용량 고정): 입력은 만원/kW·년 → 원으로 변환
    base_om_cost_won = capacity_kw * (om_unit_cost_mankw_per_kw_year * 10_000)

    results = []
    for year in range(1, int(operation_years) + 1):
        # 발전효율(연 0.4% 저하)
        efficiency = 1 - 0.004 * (year - 1)
        annual_gen_kwh = base_annual_gen_kwh * efficiency

        annual_revenue_won = annual_gen_kwh * (smp_price + rec_price * rec_factor)

        # 유지비(용량 고정 + 물가)
        maintenance_won = base_om_cost_won * ((1 + om_inflation / 100) ** (year - 1))

        net_profit_won = annual_revenue_won - maintenance_won

        # 연 이자
        interest_due_won = remaining_loan * r if remaining_loan > 0 else 0.0

        if year == 1:
            # 1년차는 이자만 납부
            paid_interest_won = min(net_profit_won, interest_due_won) if net_profit_won > 0 else 0.0
            principal_payment_won = 0.0
        else:
            # 2년차부터는 순수익으로 우선 상환(이자→원금)
            paid_interest_won = min(max(net_profit_won, 0.0), interest_due_won)
            remaining_cash_after_interest = net_profit_won - paid_interest_won
            principal_payment_won = min(max(remaining_cash_after_interest, 0.0), remaining_loan)

        repayment_won = paid_interest_won + principal_payment_won

        # 원금 차감
        remaining_loan = max(remaining_loan - principal_payment_won, 0.0)

        # 상환 후 남은 현금 누적
        cumulative_cash += (net_profit_won - repayment_won)

        # 누적 포지션 = (상환 후 남은 현금 누적) - (남은 대출원금)
        net_position_won = cumulative_cash - remaining_loan

        results.append({
            "연도": f"{year}년차",
            "발전 수익": int(round(annual_revenue_won / 10_000)),   # 만원
            "유지비": int(round(maintenance_won / 10_000)),      # 만원
            "순 수익": int(round(net_profit_won / 10_000)),        # 만원
            "누적 포지션": int(round(net_position_won / 10_000))   # 만원
        })

    df = pd.DataFrame(results).set_index("연도")

    # ===== KPI 요약 박스 =====
    st.subheader("📌 요약(20년차 기준)")
    c1, c2, c3 = st.columns(3)

    # 20년차 기준(마지막 루프 값 기반)
    remaining_loan_mankw = int(round(remaining_loan / 10_000))
    cumulative_cash_mankw = int(round(cumulative_cash / 10_000))
    net_position_mankw = int(round((cumulative_cash - remaining_loan) / 10_000))

    c1.metric("잔여 대출원금(만원)", f"{remaining_loan_mankw:,}")
    c2.metric("누적 현금(만원)", f"{cumulative_cash_mankw:,}")
    c3.metric("누적 포지션(만원)", f"{net_position_mankw:,}")

    # 색상: 누적 포지션 <0 빨강, >=0 검정
    def color_pos(v):
        return "color: red" if v < 0 else "color: black"

    st.subheader("📈 연도별 누적 포지션")
    st.caption("1년차는 이자만 상환 (단위: 만 원) 
    누적 포지션 = (상환 후 남은 현금 누적) - (남은 대출원금)")
    st.dataframe(
        df.style.applymap(color_pos, subset=["누적 포지션"]).format("{:,}"),
        use_container_width=True
    )

    # 흑자 전환 연도 찾기
    pos_array = np.array(df["누적 포지션"])
    payback_idx = next((i for i, v in enumerate(pos_array) if v >= 0), None)
    if payback_idx is not None:
        st.success(f"✅ 누적 포지션 흑자 전환 시점: {payback_idx + 1}년차")
    else:
        st.warning("❗ 운영연수 내 누적 포지션 흑자 전환 불가")

