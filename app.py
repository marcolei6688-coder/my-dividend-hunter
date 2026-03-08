import streamlit as st
import yfinance as yf
import google.generativeai as genai

# --- 1. 配置與 Key 讀取 ---
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ Secrets 中找不到 GOOGLE_API_KEY。")
    st.stop()

# 核心：配置 API Key 並指定 API 版本
genai.configure(api_key=api_key)

st.set_page_config(page_title="AI 高息股獵人", layout="wide")

# --- 2. 數據功能 ---
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        dy = (info.get("dividendYield", 0) or 0) * 100
        pr = (info.get("payoutRatio", 0) or 0) * 100
        return {
            "name": info.get("longName", "未知公司"),
            "yield": round(dy, 2) if dy < 100 else round(dy/100, 2),
            "payout": round(pr, 2) if pr < 200 else round(pr/100, 2),
            "price": info.get("currentPrice", 0),
            "currency": info.get("currency", "HKD")
        }
    except: return None

# --- 3. 介面介面 ---
st.title("🏹 AI 高息股獵人 (V2 相容版)")

# 加入推介按鈕
st.subheader("🔥 今日推介")
hot_list = ["0941.HK", "0005.HK", "0011.HK"]
cols = st.columns(len(hot_list))
selected_ticker = None
for i, t in enumerate(hot_list):
    if cols[i].button(f"查看 {t}"): selected_ticker = t

ticker_input = st.text_input("輸入代號", value=selected_ticker if selected_ticker else "0941.HK")

if st.button("啟動 AI 深度審核"):
    data = get_stock_data(ticker_input)
    if data:
        st.write(f"### {data['name']} 數據概覽")
        c1, c2, c3 = st.columns(3)
        c1.metric("股息率", f"{data['yield']}%")
        c2.metric("派息比率", f"{data['payout']}%")
        c3.metric("現價", f"{data['price']} {data['currency']}")
        
        with st.spinner('正在分析中...'):
            # 重點：使用 GenerativeModel 的標準化呼叫，避免 v1beta 錯誤
            # 優先嘗試 gemini-1.5-flash
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"分析股票 {ticker_input}：股息率 {data['yield']}%, 派息比率 {data['payout']}%。請給予收息建議與安全分 (1-10)。繁體中文回答。"
                response = model.generate_content(prompt)
                
                st.success("✅ AI 分析成功")
                st.write(response.text)
            except Exception as e:
                st.error(f"❌ AI 呼叫失敗：{str(e)}")
                st.info("請檢查 GitHub 上的 requirements.txt 是否包含最新版 google-generativeai")
