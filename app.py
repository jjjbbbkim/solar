# -----------------------------
# 5️⃣ 금융 모델 표 (연 단위)
# -----------------------------
summary_df = pd.DataFrame({
    "총 누적 수익 (만원)": (cumulative_profit/10_000).round(0).astype(int),
    "남은 원금/순수익 (만원)": [
        int(rp/10_000) if rp>0 else int((cumulative_profit[i]-total_install_cost)/10_000)
        for i, rp in enumerate(remaining_principal)
    ],
    "월별 상환금 (만원)": (monthly_payment/10_000 + monthly_maintenance_array/10_000).round(0).astype(int),
    "월별 유지비용 (만원)": (monthly_maintenance_array/10_000).round(0).astype(int)
})

# 연 단위 집계
years = np.arange(1, loan_term_years+1)
summary_yearly = pd.DataFrame({
    "총 누적 수익 (만원)": [summary_df["총 누적 수익 (만원)"].iloc[y*12-1] for y in years],
    "남은 원금/순수익 (만원)": [summary_df["남은 원금/순수익 (만원)"].iloc[y*12-1] for y in years],
    "월별 상환금 (만원)": [summary_df["월별 상환금 (만원)"].iloc[y*12-12:y*12].sum() for y in years],
    "월별 유지비용 (만원)": [summary_df["월별 유지비용 (만원)"].iloc[y*12-12:y*12].sum() for y in years]
})
summary_yearly.index = [f"{y}년차" for y in years]

# 잔여원금 >0 빨강, 순수익 검정
def color_remaining(val):
    return 'color: red' if val > 0 else 'color: black'

st.subheader("📈 금융 모델 (연 단위)")
st.dataframe(summary_yearly.style.format("{:,}").applymap(color_remaining, subset=['남은 원금/순수익 (만원)']), width=900, height=500)

# -----------------------------
# 6️⃣ 원리금 균등상환 표 (연 단위)
# -----------------------------
st.subheader("🏦 원리금 균등상환 (연 단위)")
loan_df_yearly = pd.DataFrame({
    "월별 상환금 (만원)": [(monthly_payment/10_000).round(1) * 12 for y in years],
    "월별 유지비용 (만원)": [(monthly_maintenance_array[(y-1)*12:y*12]/10_000).round(1).sum() for y in years],
    "잔여 원금 (만원)": [(remaining_loan_array[y*12 -1]/10_000).round(1) for y in years]
})
loan_df_yearly.index = [f"{y}년차" for y in years]
st.dataframe(loan_df_yearly.style.format("{:,}").applymap(color_remaining, subset=['잔여 원금 (만원)']), width=900, height=500)
