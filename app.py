import streamlit as st
import yfinance as yf
import google.generativeai as genai

# --- 1. 雲端安全讀取 API Key ---
# Streamlit 會自動去你啱啱設定嘅 Secrets 度搵 GOOGLE_API_KEY
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("請在 Streamlit Cloud Settings 中設定 GOOGLE_API_KEY")

st.set_page_config(page_title="AI 高息股獵人", layout="wide")
st.title("🏹 AI 高息股獵人 (雲端穩定版)")

# 2. 數據獲取函數
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        dy_raw = info.get("dividendYield", 0) or 0
        div_yield = dy_raw * 100 if dy_raw < 1 else dy_raw
        pr_raw = info.get("payoutRatio", 0) or 0
        payout = pr_raw * 100 if pr_raw < 2 else pr_raw
        
        return {
            "name": info.get("longName", "未知公司"),
            "yield": round(div_yield, 2),
            "payout": round(payout, 2),
            "debt": round(info.get("debtToEquity", 0) or 0, 2),
            "price": info.get("currentPrice", 0),
            "currency": info.get("currency", "HKD")
        }
    except: return None

# 3. 介面
ticker_input = st.text_input("輸入股票代號 (如: 0941.HK, 0005.HK, KO)", "0941.HK")

if st.button("開始掃描並進行 AI 審核"):
    data = get_stock_data(ticker_input)
    if data:
        c1, c2, c3 = st.columns(3)
        c1.metric("股息率", f"{data['yield']}%")
        c2.metric("派息比率", f"{data['payout']}%")
        c3.metric("債務比率", f"{data['debt']}")
        st.write(f"**公司:** {data['name']} | **現價:** {data['price']} {data['currency']}")
        
        with st.spinner('AI 正在由美國伺服器分析中...'):
            try:
                # 雲端環境通常直接用 gemini-1.5-flash 就得
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"分析股票 {ticker_input} ({data['name']})：股息率{data['yield']}%, 派息比率{data['payout']}%, 債務比率{data['debt']}。評估派息持續性並給予1-10分。繁體中文回答。"
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e:
                st.error(f"AI 分析失敗：{e}")
    else:
        st.error("搵唔到數據，請檢查代號。")
