import streamlit as st
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import os
import textwrap

# --- 頁面配置 (寬螢幕儀表板佈局) ---
st.set_page_config(page_title="Michael's Terminal", layout="wide", initial_sidebar_state="expanded")

# --- 載入 config.json 設定檔以作為預設值 ---
default_capital = 189000
default_risk = 0.5
default_rate = 156.45
default_sl = 0.200
default_rr = "4:1"

if os.path.exists("config.json"):
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
            default_capital = int(cfg.get("capital", 189000))
            
            # 處理風險百分比 (例如 "0.5%" 或 0.5)
            risk_str = cfg.get("risk", "0.5%")
            if isinstance(risk_str, str) and risk_str.endswith("%"):
                default_risk = float(risk_str.rstrip("%"))
            else:
                default_risk = float(risk_str)
                
            default_rate = float(cfg.get("rate", 156.45))
            default_sl = float(cfg.get("stop_loss", 0.200))
            default_rr = cfg.get("rr_ratio", "4:1")
    except Exception:
        pass

# --- 獲取今日開盤價 ---
@st.cache_data(ttl=3600)  # 快取一小時，避免重複請求過於頻繁
def get_usdjpy_open_price():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/USDJPY=X?range=1d&interval=1d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        result = data['chart']['result'][0]
        open_prices = result['indicators']['quote'][0]['open']
        valid_opens = [x for x in open_prices if x is not None]
        if valid_opens:
            return round(valid_opens[-1], 2)
    except Exception:
        pass
    return None

# 試圖抓取今日開盤價
yahoo_open_rate = get_usdjpy_open_price()
if yahoo_open_rate is not None:
    default_rate = yahoo_open_rate
    rate_source_msg = f"💡 今日開盤匯率已自動同步：{yahoo_open_rate} (Yahoo Finance)"
else:
    rate_source_msg = "⚠️ 無法連線至 Yahoo Finance，已使用設定檔之預設匯率"

# --- 高階 CSS 注入 (極致暗黑玻璃風與霓虹紅漸層) ---
st.markdown(textwrap.dedent("""
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800;900&display=swap" rel="stylesheet">
    <style>
    /* 全域背景與字型 */
    .stApp {
        background: linear-gradient(135deg, #0a0813 0%, #110d22 50%, #05040a 100%);
        color: #f1f1f1;
        font-family: 'Outfit', 'Inter', 'Noto Sans TC', sans-serif;
    }
    /* 側邊欄樣式 */
    [data-testid="stSidebar"] {
        background-color: rgba(13, 10, 25, 0.9) !important;
        border-right: 1px solid rgba(255, 75, 43, 0.15) !important;
    }
    /* 主標題區 */
    .terminal-title {
        background: linear-gradient(90deg, #ff416c 0%, #ff4b2b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 2.6rem;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .terminal-subtitle {
        color: #8b88a5;
        font-size: 0.95rem;
        margin-bottom: 25px;
        letter-spacing: 2px;
        font-weight: 500;
    }
    /* 玻璃感儀表板卡片 */
    .dashboard-card {
        background: rgba(20, 16, 38, 0.65);
        border: 1px solid rgba(255, 75, 43, 0.15);
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    .dashboard-card:hover {
        border-color: rgba(255, 75, 43, 0.35);
        box-shadow: 0 10px 30px rgba(255, 75, 43, 0.08);
    }
    /* 計算器結果框 */
    .result-box {
        background: rgba(255, 75, 43, 0.05);
        border: 1.5px dashed rgba(255, 75, 43, 0.35);
        padding: 22px;
        border-radius: 12px;
        text-align: center;
        margin-top: 15px;
        transition: all 0.3s ease;
    }
    .result-title {
        color: #8b88a5;
        font-size: 0.85rem;
        letter-spacing: 2px;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .result-val {
        background: linear-gradient(90deg, #ff416c 0%, #ff4b2b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.8rem;
        font-weight: 900;
        line-height: 1.1;
        text-shadow: 0 0 25px rgba(255, 75, 43, 0.3);
    }
    /* 新聞卡片 */
    .news-item {
        border-left: 4px solid #ff4b2b;
        background: rgba(255, 75, 43, 0.02);
        padding: 14px 18px;
        margin-bottom: 12px;
        border-radius: 0 10px 10px 0;
        transition: all 0.2s ease;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    .news-item:hover {
        transform: translateX(5px);
        background: rgba(255, 75, 43, 0.06);
    }
    .news-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    .badge {
        font-size: 0.75rem;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-USD {
        background: #ff4b2b;
        color: white;
    }
    .badge-JPY {
        background: #ff416c;
        color: white;
    }
    .news-time {
        color: #8b88a5;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .news-content {
        color: #e2e1e9;
        font-weight: 600;
        font-size: 1rem;
        line-height: 1.4;
    }
    /* 客製化輸入控制項標籤 */
    div[data-testid="stNumberInput"] label, div[data-testid="stSelectbox"] label {
        color: #a3a0c2 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.5px;
    }
    </style>
"""), unsafe_allow_html=True)

# --- 側邊欄配置 (資訊面板) ---
st.sidebar.markdown(textwrap.dedent("""
    <div style="background: rgba(255, 75, 43, 0.1); border: 1px solid rgba(255, 75, 43, 0.2); padding: 15px; border-radius: 12px; margin-bottom: 20px;">
        <span style="color: #FF4B2B; font-weight: bold; font-size: 1.1em;">⚡ TERMINAL LIVE</span><br>
        <span style="color: #8b88a5; font-size: 0.85em;">自動讀取設定檔 & 追蹤新聞中</span>
    </div>
"""), unsafe_allow_html=True)

st.sidebar.subheader("⚙️ 目前載入的預設值")
st.sidebar.json({
    "本金 (Capital)": default_capital,
    "風險 (Risk %)": f"{default_risk}%",
    "預設匯率 (Rate)": default_rate,
    "預設止損 (Stop Loss)": default_sl,
    "預設盈虧比 (R:R Ratio)": default_rr
})

st.sidebar.markdown("---")
st.sidebar.caption(f"本地測試模式 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# --- 主頁面標題 ---
st.markdown('<div class="terminal-title">Michael\'s Terminal</div>', unsafe_allow_html=True)
st.markdown('<div class="terminal-subtitle">INTELLIGENT TRADING HUB & RISK CALCULATOR</div>', unsafe_allow_html=True)

# --- 網頁主要格線排版：左欄(計算器)，右欄(新聞) ---
col_calc, col_news = st.columns([7, 5], gap="large")

# --- 左欄：手數計算器 ---
with col_calc:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("🧮 手數計算器 (Position Sizing)")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        capital = st.number_input("本金 (CAPITAL)", value=default_capital, step=1000)
        
        # 建立風險百分比選項，若 config 中的預設值不在選項內則動態插入
        risk_options = [1.0, 0.5, 0.25, 0.125]
        if default_risk not in risk_options:
            risk_options.insert(0, default_risk)
        try:
            risk_index = risk_options.index(default_risk)
        except ValueError:
            risk_index = 1
            
        risk_pct = st.selectbox("風險 (RISK %)", risk_options, index=risk_index)
        
    with col_b:
        rate = st.number_input("匯率 (RATE)", value=default_rate, format="%.2f", help=rate_source_msg)
        sl_pips = st.number_input("止損 (SL PIPS)", value=default_sl, format="%.3f")
        
    with col_c:
        rr_options = ["4:1", "2:1", "自訂 (Custom)"]
        if default_rr not in rr_options:
            rr_options.insert(0, default_rr)
        try:
            rr_index = rr_options.index(default_rr)
        except ValueError:
            rr_index = 0
        rr_selection = st.selectbox("盈虧比 (R:R RATIO)", rr_options, index=rr_index)
        if rr_selection == "自訂 (Custom)":
            rr_val = st.number_input("自訂比例 (:1)", value=3.0, step=0.5, format="%.1f")
        else:
            try:
                rr_val = float(rr_selection.split(":")[0])
            except ValueError:
                rr_val = 4.0

    # 手數計算公式
    lots = (capital * (risk_pct / 100) * rate) / (100000 * sl_pips) if sl_pips > 0 else 0.0

    st.markdown(textwrap.dedent(f"""
        <div class="result-box">
            <div class="result-title">RECOMMENDED LOTS</div>
            <div class="result-val">{lots:.4f}</div>
        </div>
    """), unsafe_allow_html=True)

    # 計算新增指標
    risk_amount = capital * (risk_pct / 100)
    max_profit = risk_amount * rr_val
    leverage_200k = (lots * 100000) / 200000
    actual_leverage = (lots * 100000) / capital if capital > 0 else 0.0

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(textwrap.dedent(f"""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 75, 43, 0.15); padding: 15px; border-radius: 12px; text-align: center;">
                <div style="color: #8b88a5; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">單筆承受風險</div>
                <div style="color: #ff4b2b; font-size: 1.4rem; font-weight: 800; margin-top: 5px;">${risk_amount:,.2f}</div>
            </div>
        """), unsafe_allow_html=True)
    with col_m2:
        st.markdown(textwrap.dedent(f"""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(0, 230, 118, 0.15); padding: 15px; border-radius: 12px; text-align: center;">
                <div style="color: #8b88a5; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">單筆最大獲利金額</div>
                <div style="color: #00e676; font-size: 1.4rem; font-weight: 800; margin-top: 5px;">${max_profit:,.2f}</div>
            </div>
        """), unsafe_allow_html=True)
    with col_m3:
        st.markdown(textwrap.dedent(f"""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 75, 43, 0.15); padding: 15px; border-radius: 12px; text-align: center;">
                <div style="color: #8b88a5; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">槓桿比率 (相對20萬)</div>
                <div style="color: #ff416c; font-size: 1.4rem; font-weight: 800; margin-top: 5px;">{leverage_200k:.2f}x</div>
            </div>
        """), unsafe_allow_html=True)
    with col_m4:
        st.markdown(textwrap.dedent(f"""
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 75, 43, 0.15); padding: 15px; border-radius: 12px; text-align: center;">
                <div style="color: #8b88a5; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">實際帳戶槓桿</div>
                <div style="color: #00e676; font-size: 1.4rem; font-weight: 800; margin-top: 5px;">{actual_leverage:.2f}x</div>
            </div>
        """), unsafe_allow_html=True)

    # 關閉 dashboard-card 的 div
    st.markdown("</div>", unsafe_allow_html=True)

# --- 右欄：高衝擊新聞警示 ---
with col_news:
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("🚨 USD/JPY 近三日高衝擊新聞 (GMT+8)")
    
    # 抓取新聞數據
    def get_news():
        url = "https://www.forexfactory.com/ff_calendar_this_week.xml"
        try:
            r = requests.get(url, timeout=10)
            root = ET.fromstring(r.content)
            events = []
            
            # GMT+8 今天、明天、後天
            gmt8_now = datetime.utcnow() + timedelta(hours=8)
            local_today = gmt8_now.date()
            local_tomorrow = local_today + timedelta(days=1)
            local_after_tomorrow = local_today + timedelta(days=2)
            
            for event in root.findall('event'):
                # 兼容處理 currency 或 country 標籤
                curr_elem = event.find('currency')
                curr = curr_elem.text if curr_elem is not None else event.find('country').text
                
                impact = event.find('impact').text
                
                if curr in ['USD', 'JPY'] and impact == 'High':
                    raw_time = event.find('time').text
                    raw_date = event.find('date').text
                    
                    # 轉換為 GMT+8 時間來決定本地日期與時間
                    try:
                        dt_str = f"{raw_date} {raw_time}"
                        gmt_dt = datetime.strptime(dt_str, "%m-%d-%Y %I:%M%p")
                        gmt8_dt = gmt_dt + timedelta(hours=8)
                        event_local_date = gmt8_dt.date()
                        gmt8_time_str = gmt8_dt.strftime("%H:%M")
                    except Exception:
                        event_local_date = datetime.strptime(raw_date, "%m-%d-%Y").date()
                        gmt8_time_str = f"{raw_time} (GMT)"
                        gmt8_dt = None
                    
                    # 判斷是否在 今日、明日、後日 範圍內
                    if local_today <= event_local_date <= local_after_tomorrow:
                        # 決定日期標記
                        if event_local_date == local_today:
                            date_label = "今日"
                        elif event_local_date == local_tomorrow:
                            date_label = "明日"
                        elif event_local_date == local_after_tomorrow:
                            date_label = "後日"
                        else:
                            date_label = event_local_date.strftime("%m/%d")
                            
                        events.append({
                            "title": event.find('title').text,
                            "time": raw_time,
                            "date": raw_date,
                            "curr": curr,
                            "gmt8_time": gmt8_time_str,
                            "date_label": date_label,
                            "local_date": event_local_date,
                            "sort_dt": gmt8_dt if gmt8_dt else datetime.combine(event_local_date, datetime.min.time())
                        })
            
            # 按時間排序，讓最近的新聞排在最上面
            events.sort(key=lambda x: x["sort_dt"])
            return events
        except Exception:
            return None

    # 執行獲取數據
    news_data = get_news()
    
    if news_data:
        for item in news_data:
            badge_class = f"badge-{item['curr']}"
            st.markdown(textwrap.dedent(f"""
                <div class="news-item">
                    <div class="news-header">
                        <span class="badge {badge_class}">{item['curr']}</span>
                        <span class="news-time">🕒 {item['date_label']} {item['gmt8_time']} <span style="opacity: 0.5; font-size: 0.85em;">(GMT: {item['time']})</span></span>
                    </div>
                    <div class="news-content">{item['title']}</div>
                </div>
            """), unsafe_allow_html=True)
    else:
        st.markdown(textwrap.dedent("""
            <div style="background: rgba(46, 204, 113, 0.05); border-left: 4px solid #2ecc71; padding: 15px; border-radius: 6px; margin-top: 10px;">
                <span style="color: #2ecc71; font-weight: 700; font-size: 1.05em;">✔ 近三日安全無虞</span><br>
                <small style="color: #8b88a5; font-size: 0.85em;">目前 Forex Factory 今日與未來兩日無 USD/JPY 的高衝擊 (High Impact) 新聞事件。</small>
            </div>
        """), unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)