import streamlit as st

# 제목
st.title("🌞 태양광 수익 계산기")

# 입력
st.subheader("기본 입력값")
capacity = st.number_input("발전용량 (kW)", min_value=1.0, step=1.0)
smp = st.number_input("SMP 단가 (원/kWh)", value=120.0)
rec = st.number_input("REC 단가 (원/REC)", value=65000.0)

# 버튼 클릭 시 계산
if st.button("계산하기"):
    annual_revenue = capacity * 365 * 4 * smp
    st.success(f"예상 연간 수익: {annual_revenue:,.0f} 원")
