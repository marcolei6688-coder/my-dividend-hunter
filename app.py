import streamlit as st
import yfinance as yf
import google.generativeai as genai

# --- 1. 安全讀取 API Key (請務必在 Streamlit Cloud Secrets 設定新 Key) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("❌ 未偵測到 API Key。請在 Streamlit Cloud Settings 中設定 Secrets。")
    st.stop()

st.set_page_config(page_title="AI 高息股獵人", layout="wide", page_icon="🏹")

# --- 2. 獲取數據函數 ---
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        dy = (info.get("dividendYield", 0) or 0) * 100
        pr = (info.get("payoutRatio", 0) or 0) * 100
        return {
            "symbol": ticker,
            "name": info.get("longName", "未知公司"),
            "yield": round(dy, 2) if dy < 100 else round(dy/100, 2), # 修正單位
            "payout": round(pr, 2) if pr < 200 else round(pr/100, 2),
            "debt": round(info.get("debtToEquity", 0) or 0, 2),
            "price": info.get("currentPrice", 0),
            "currency": info.get("currency", "HKD")
        }
    except: return None

# --- 3. 今日精選推介 (增加內容豐富度，利於 AdSense 審核) ---
def show_recommendations():
    st.subheader("🔥 今日 AI 精選高息股")
    hot_list = ["0941.HK", "0005.HK", "0011.HK", "1299.HK"]
    cols = st.columns(len(hot_list))
    selected = None
    for i, t in enumerate(hot_list):
        with cols[i]:
            if st.button(f"查看 {t}"): selected = t
    return selected

# --- 4. 主介面 ---
st.title("🏹 AI 高息股獵人 (雲端終極版)")
rec_ticker = show_recommendations()

st.markdown("---")
ticker_input = st.text_input("輸入股票代號 (例如: 0941.HK, AAPL)", value=rec_ticker if rec_ticker else "0941.HK")

if st.button("開始 AI 深度分析"):
    data = get_stock_data(ticker_input)
    if data:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("股息率", f"{data['yield']}%")
        c2.metric("派息比率", f"{data['payout']}%")
        c3.metric("債務比率", f"{data['debt']}")
        c4.metric("現價", f"{data['price']} {data['currency']}")
        
        with st.spinner('AI 正在由雲端分析中...'):
            # 嘗試不同模型名稱以避開 404
            success = False
            for m_name in ['gemini-1.5-flash', 'gemini-pro']:
                try:
                    model = genai.GenerativeModel(m_name)
                    prompt = f"分析股票 {ticker_input} ({data['name']})：股息率{data['yield']}%, 派息比率{data['payout']}%, 債務比率{data['debt']}。評估派息持續性並給予1-10分安全分。繁體中文回答。"
                    response = model.generate_content(prompt)
                    st.info(f"🤖 AI 報告 ({m_name})")
                    st.write(response.text)
                    success = True
                    break
                except: continue
            if not success: st.error("❌ AI 連線失敗，請檢查 API Key 是否有效。")
    else:
        st.error("搵唔到數據，請檢查代號。")

st.markdown("---")
st.caption("🚨 本工具僅供參考，不構成投資建議。")
