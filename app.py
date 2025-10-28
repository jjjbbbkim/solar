# -----------------------------
# 원리금 균등상환 표 (연 단위, 20년차에 잔여원금 0)
# -----------------------------
years = np.arange(1, loan_term_years+1)
monthly_payment_full = total_install_cost * (r * (1+r)**n) / ((1+r)**n - 1)
remaining = total_install_cost
loan_df_yearly = pd.DataFrame(columns=["월별 상환금 (만원)", "월별 유지비용 (만원)", "잔여 원금 (만원)"])

for y in years:
    start_month = (y-1)*12
    end_month = y*12
    # 연간 유지비용
    yearly_maintenance = monthly_maintenance_array[start_month:end_month].sum()
    # 연간 상환금
    yearly_payment = monthly_payment_full * 12
    # 잔여원금 계산
    remaining -= yearly_payment
    if y == loan_term_years:
        remaining = 0  # 마지막 20년차에 모두 상환
    loan_df_yearly.loc[f"{y}년차"] = [
        int(round(yearly_payment / 10_000, 0)),
        int(round(yearly_maintenance / 10_000, 0)),
        int(round(max(remaining,0) / 10_000, 0))
    ]

# 색상 적용 함수
def color_remaining(val):
    return 'color: red' if val > 0 else 'color: black'

st.subheader("🏦 원리금 균등상환 (연 단위)")
st.dataframe(loan_df_yearly.style.applymap(color_remaining, subset=['잔여 원금 (만원)']), width=900, height=500)
