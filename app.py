import streamlit as st
import pandas as pd
import numpy as np

# matplotlib 자동 설치 (로컬에서 실행할 때 유용)
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    import os
    os.system("pip install matplotlib")
    import matplotlib.pyplot as plt

# -----------------------------
# 기본 데이터 (2025년 기준 SMP, REC 단가)
# -----------------------------
data = {
    "월": ["1월","2월","3월","4월","5월","6월","7월","8월","9월"],
    "SMP(원/kWh)": [117.11,116.39,113.12,124.63,125.50,118.02,120.39,117.39,112.90],
    "REC(원/kWh)": [69.76,72.16,72.15,72.41,72.39,71.96,71.65,71.86,71.97],
}
smp_df = pd.DataFrame(data)

# -----------------------------
# 1️⃣ 기본정보
# -----------------------------
st.title("태양광 수익성 분석 대시보드")
st.write("기준: 하루 3.6시간 발전 기준, 2025년 9월 SMP 112.9원 기준")

# 발전소 타입 선택
type_choice = st.radio("발전소 타입", ["노지형", "지붕형"], horizontal=True)

# 설치비용 계산
if type_choice == "노지형":
    install_cost = 120_000_000  # 1.2억원
    rec_factor = 1.0
else:
    install_cost = 100_000_000  # 1억원
    rec_factor = 1.5
    st.write(f"※ 지붕형 REC 가중치 적용: x{rec_factor}")

# -----------------------------
# 2️⃣ SMP & REC 월별 단가표
# -----------------------------
st.subheader("📊 월별 SMP·REC 단가표")
st.dataframe(smp_df.style.format({"SMP(원/kWh)":"{:.2f}", "REC(원/kWh)":"{:.2f}"}),
             width=500, height=250)

# -----------------------------
# 3️⃣ 회수기간 계산 함수
# -----------------------------
def calc_payback(smp, rec, capacity_kw=100, hours=3.6, rec_factor=1.0):
    monthly_gen = capacity_kw * hours * 30  # kWh
    revenue = (smp + rec * rec_factor) * monthly_gen  # 월 수익 (원)
    annual_profit = revenue * 12  # 연간 수익
    payback_years = install_cost / annual_profit
    return payback_years

# -----------------------------
# 4️⃣ 민감도 분석 (SMP, REC 변화에 따른 회수기간)
# -----------------------------
st.subheader("📈 민감도 분석 (SMP·REC 단가 변화에 따른 회수기간)")

smp_values = np.linspace(100, 140, 9)  # SMP 단가 범위
rec_values = np.linspace(65, 80, 9)    # REC 단가 범위

payback_matrix = np.zeros((len(rec_values), len(smp_values)))

for i, rec in enumerate(rec_values):
    for j, smp in enumerate(smp_values):
        payback_matrix[i, j] = calc_payback(smp, rec, rec_factor=rec_factor)

fig, ax = plt.subplots(figsize=(7,5))
im = ax.imshow(payback_matrix, cmap="RdYlGn_r", origin="lower")

# 축 라벨 및 틱
ax.set_xticks(np.arange(len(smp_values)))
ax.set_yticks(np.arange(len(rec_values)))
ax.set_xticklabels([f"{v:.0f}" for v in smp_values])
ax.set_yticklabels([f"{v:.0f}" for v in rec_values])

# 축 제목 명확히 표시
ax.set_xlabel("SMP 단가 (원/kWh)", fontsize=12)
ax.set_ylabel("REC 단가 (원/kWh)", fontsize=12)
ax.set_title("SMP·REC 단가 변화에 따른 회수기간(년)", fontsize=13, weight="bold")

# 색상바 (회수기간)
cbar = plt.colorbar(im)
cbar.set_label("회수기간 (년)", fontsize=12)

st.pyplot(fig)
