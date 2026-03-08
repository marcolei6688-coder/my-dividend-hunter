import streamlit as st
import yfinance as yf
import google.generativeai as genai

# --- 1. 極致 Key 偵測 ---
# 嘗試從 Secrets 讀取 Key
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.warning("⚠️ 偵測不到 GOOGLE_API_KEY！請確保你在 Streamlit Cloud 的 Secrets 設定中添加了正確的格式。")
    st.code("GOOGLE_API_KEY = '你的金鑰貼在這裡'")
    st.stop()
else:
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
            "debt": round(info.get("debtToEquity", 0) or 0, 2),
            "price": info.get("currentPrice", 0),
            "currency": info.get("currency", "HKD")
        }
    except: return None

# --- 3. 介面 ---
st.title("🏹 AI 高息股獵人 (除錯診斷版)")

ticker_input = st.text_input("輸入股票代號 (如 0941.HK)", "0941.HK")

if st.button("開始 AI 分析"):
    data = get_stock_data(ticker_input)
    if data:
        st.write(f"### {data['name']} 數據概覽")
        col1, col2, col3 = st.columns(3)
        col1.metric("股息率", f"{data['yield']}%")
        col2.metric("派息比率", f"{data['payout']}%")
        col3.metric("現價", f"{data['price']} {data['currency']}")
        
        with st.spinner('正在強制呼叫 AI 模型...'):
            # 強制嘗試最穩定的三個模型名稱
            models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
            ai_success = False
            
            for m in models_to_try:
                try:
                    model = genai.GenerativeModel(m)
                    prompt = f"分析 {ticker_input}：股息率{data['yield']}%, 派息比率{data['payout']}%。繁體中文簡潔分析。"
                    response = model.generate_content(prompt)
                    st.success(f"✅ 使用 {m} 分析成功！")
                    st.write(response.text)
                    ai_success = True
                    break
                except Exception as e:
                    st.write(f"❌ 模型 {m} 呼叫錯誤: {str(e)}")
                    continue
            
            if not ai_success:
                st.error("❌ 所有 AI 通道均失敗。這通常意味著 API Key 的權限尚未開通或已被限制。")

st.markdown("---")
st.caption("🚨 本工具由 AI 生成，僅供參考。")
