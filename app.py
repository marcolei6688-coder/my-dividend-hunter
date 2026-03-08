import streamlit as st
import yfinance as yf
import google.generativeai as genai

# --- 1. 檢查並讀取 API Key ---
# 呢度係最容易出錯嘅地方，我加咗詳細提示
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("❌ 找不到 GOOGLE_API_KEY。請檢查 Streamlit Cloud 的 Secrets 設定。")
    st.info("💡 提示：Secrets 格式應該係 GOOGLE_API_KEY = '你的Key'")
    st.stop()

st.set_page_config(page_title="AI 高息股獵人", layout="wide", page_icon="🏹")

# --- 2. 核心數據抓取 ---
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        dy = (info.get("dividendYield", 0) or 0) * 100
        pr = (info.get("payoutRatio", 0) or 0) * 100
        return {
            "symbol": ticker,
            "name": info.get("longName", "未知公司"),
            "yield": round(dy, 2) if dy < 100 else round(dy/100, 2),
            "payout": round(pr, 2) if pr < 200 else round(pr/100, 2),
            "debt": round(info.get("debtToEquity", 0) or 0, 2),
            "price": info.get("currentPrice", 0),
            "currency": info.get("currency", "HKD")
        }
    except: return None

# --- 3. 介面設計 ---
st.title("🏹 AI 高息股獵人 (終極穩定版)")

# 推介位
st.subheader("🔥 今日精選")
hot_list = ["0941.HK", "0005.HK", "0011.HK"]
cols = st.columns(len(hot_list))
selected_ticker = None
for i, t in enumerate(hot_list):
    if cols[i].button(f"查看 {t}", key=f"btn_{t}"): selected_ticker = t

st.markdown("---")
ticker_input = st.text_input("輸入股票代號", value=selected_ticker if selected_ticker else "0941.HK")

if st.button("開始 AI 分析"):
    data = get_stock_data(ticker_input)
    if data:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("股息率", f"{data['yield']}%")
        c2.metric("派息比率", f"{data['payout']}%")
        c3.metric("債務比率", f"{data['debt']}")
        c4.metric("現價", f"{data['price']} {data['currency']}")
        
        with st.spinner('AI 正在由雲端分析中...'):
            # 嘗試多個模型名稱，解決 404 問題
            model_found = False
            for m_name in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
                try:
                    model = genai.GenerativeModel(m_name)
                    prompt = f"分析股票 {ticker_input} ({data['name']})：股息率{data['yield']}%, 派息比率{data['payout']}%, 債務比率{data['debt']}。評估其派息持續性並給予1-10分安全分。繁體中文回答。"
                    response = model.generate_content(prompt)
                    st.success(f"🤖 AI 分析完成 ({m_name})")
                    st.write(response.text)
                    model_found = True
                    break
                except Exception as e:
                    continue # 失敗就試下一個模型
            
            if not model_found:
                st.error("❌ AI 分析失敗。請確保你的新 Key 已經生效（有時需要幾分鐘），且擁有 Gemini API 權限。")
    else:
        st.error("搵唔到數據，請檢查代號（例如港股要加 .HK）。")
