# 총 설치비용
total_install_cost = capacity_kw / 100 * install_cost_per_100kw * 10_000  # 원 단위

# 월별 유지비용 (총 사업비의 4.5% ÷ 12)
monthly_maintenance = total_install_cost * 0.045 / 12

# 월별 발전량 (하루 3.6시간, 30일 기준) + 발전효율 감소
monthly_gen_list = []
for m in months:
    year = (m-1)//12  # 경과 년수
    efficiency_factor = 1 - 0.004 * year
    monthly_gen = capacity_kw * 3.6 * 30 * efficiency_factor
    monthly_gen_list.append(monthly_gen)

monthly_gen_array = np.array(monthly_gen_list)

# 월별 수익 계산
monthly_profit = monthly_gen_array * (smp_price + rec_price * rec_factor) - monthly_maintenance

# 누적 수익
cumulative_profit = np.cumsum(monthly_profit)
remaining_principal = np.maximum(total_install_cost - cumulative_profit, 0)

# 원리금 균등 상환 계산 (기존과 동일)
r = interest_rate / 100 / 12
n = loan_term_years * 12
monthly_payment = total_install_cost * r * (1+r)**n / ((1+r)**n - 1)
remaining_loan = total_install_cost - np.cumsum([monthly_payment]*len(months))
