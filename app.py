import streamlit as st
import requests
import pandas as pd

# --- 頁面配置 ---
st.set_page_config(page_title="Lot Size Pro", layout="centered")

# --- 注入自定義 CSS (維持紅色系專業風格) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; }
    h1, h2, h3 { color: #DEFF9A !important; text-align: center; }
    div[data-baseweb="select"] > div { background-color: #1E1E1E !important; color: white !important; }
    .stNumberInput input { background-color: #1E1E1E !important; color: #DEFF9A !important; }
    .result-box {
        background-color: #1A1A1A;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-top: 20px;
    }
    .result-val {
        color: #FF5252;
        font-size: 50px;
        font-weight: bold;
        font-family: 'Arial';
    }
    </style>
    """, unsafe_allow_html=True)

# --- 核心邏輯 ---
CONTRACT_SIZE = 100000

def fetch_rate():
    try:
        url = "https://api.frankfurter.dev/v2/latest?from=USD&to=JPY"
        data = requests.get(url, timeout=5).json()
        return data['rates']['JPY']
    except:
        return 156.45

# --- UI 介面 ---
st.title("LOT SIZE Calculator Pro")

# 獲取初始匯率
if 'init_rate' not in st.session_state:
    st.session_state.init_rate = fetch_rate()

# 輸入區域
with st.container():
    risk = st.selectbox("風險比例 (RISK %)", [1.0, 0.5, 0.25, 0.125], index=1)
    capital = st.number_input("帳戶本金 (CAPITAL)", value=189000, step=1000)
    rate = st.number_input("市場匯率 (RATE)", value=st.session_state.init_rate, format="%.2f")
    sl = st.number_input("止損點數 (SL PIPS)", value=0.200, format="%.3f")

# 計算公式
# $$ \text{Lot Size} = \frac{\text{Capital} \times (\text{Risk} / 100) \times \text{Rate}}{\text{Contract Size} \times \text{SL}} $$

if sl > 0:
    lots = (capital * (risk / 100) * rate) / (CONTRACT_SIZE * sl)
else:
    lots = 0.0

# --- 結果顯示 ---
st.markdown(f"""
    <div class="result-box">
        <p style="color: gray; font-weight: bold;">RECOMMENDED POSITION</p>
        <div class="result-val">{lots:.4f}</div>
        <p style="color: gray60;">STANDARD LOTS</p>
    </div>
    """, unsafe_allow_html=True)

st.caption(f"系統狀態：數據載入完畢 | 更新時間 {pd.Timestamp.now().strftime('%H:%M')}")