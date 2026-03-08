import streamlit as st
import yfinance as yf
import google.generativeai as genai

# --- 安全讀取 API Key ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("❌ 未在 Secrets 中偵測到 API Key。")
    st.stop()

st.set_page_config(page_title="AI 高息股獵人", layout="wide")

# --- 數據獲取函數 ---
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # 修正股息率與派息比率單位
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

# --- 主介面 ---
st.title("🏹 AI 高息股獵人 (終極穩定版)")

# 增加推介位增加內容豐富度
st.subheader("🔥 熱門高息股推介")
hot_list = ["0941.HK", "0005.HK", "0011.HK"]
cols = st.columns(len(hot_list))
selected_ticker = None
for i, t in enumerate(hot_list):
    if cols[i].button(f"查看 {t}"): selected_ticker = t

ticker_input = st.text_input("輸入股票代號", value=selected_ticker if selected_ticker else "0941.HK")

if st.button("開始 AI 深度分析"):
    data = get_stock_data(ticker_input)
    if data:
        c1, c2, c3 = st.columns(3)
        c1.metric("股息率", f"{data['yield']}%")
        c2.metric("派息比率", f"{data['payout']}%")
        c3.metric("債務比率", f"{data['debt']}")
        
        with st.spinner('AI 正在嘗試多個通道進行分析...'):
            # 自動嘗試不同模型名稱以避開 404 錯誤
            ai_success = False
            for m_name in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
                try:
                    model = genai.GenerativeModel(m_name)
                    prompt = f"分析股票 {ticker_input} ({data['name']})：股息率{data['yield']}%, 派息比率{data['payout']}%, 債務比率{data['debt']}。評估派息持續性並給予1-10分安全分。繁體中文回答。"
                    response = model.generate_content(prompt)
                    st.info(f"🤖 AI 報告 (經由 {m_name} 分析)")
                    st.write(response.text)
                    ai_success = True
                    break
                except: continue
            
            if not ai_success:
                st.error("❌ 所有 AI 模型呼叫失敗，請確認 API Key 權限。")
    else:
        st.error("無法獲取數據，請檢查代號。")
