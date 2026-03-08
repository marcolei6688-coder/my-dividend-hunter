import streamlit as st
import yfinance as yf
import google.generativeai as genai

# --- 1. 安全讀取 API Key (透過 Streamlit Secrets) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("❌ 未偵測到 API Key。請在 Streamlit Cloud 的 Settings > Secrets 中設定。")
    st.stop()

# 頁面配置
st.set_page_config(page_title="AI 高息股獵人", layout="wide", page_icon="🏹")

# --- 2. 核心功能：抓取股票數據 ---
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 修正股息率與派息比率 (處理小數與百分比轉換)
        dy_raw = info.get("dividendYield", 0) or 0
        div_yield = dy_raw * 100 if dy_raw < 1 else dy_raw
        
        pr_raw = info.get("payoutRatio", 0) or 0
        payout = pr_raw * 100 if pr_raw < 2 else pr_raw
        
        return {
            "symbol": ticker,
            "name": info.get("longName", "未知公司"),
            "yield": round(div_yield, 2),
            "payout": round(payout, 2),
            "debt": round(info.get("debtToEquity", 0) or 0, 2),
            "price": info.get("currentPrice", 0),
            "currency": info.get("currency", "HKD"),
            "sector": info.get("sector", "未知行業")
        }
    except Exception:
        return None

# --- 3. 今日熱門推介功能 ---
def show_recommendations():
    st.subheader("🔥 今日 AI 精選高息股 (熱門追蹤)")
    # 預設熱門關注股
    hot_tickers = ["0941.HK", "0005.HK", "0011.HK", "KO"] 
    cols = st.columns(len(hot_tickers))
    
    selected_ticker = None
    for i, t in enumerate(hot_tickers):
        with cols[i]:
            if st.button(f"查看 {t}", key=f"btn_{t}"):
                selected_ticker = t
    return selected_ticker

# --- 4. 網頁主介面 ---
st.title("🏹 AI 高息股獵人 (終極穩定版)")
st.markdown("---")

# 顯示自動推介
recommended = show_recommendations()

st.markdown("---")
# 輸入框：點擊推介按鈕會自動填入代號
ticker_input = st.text_input("請輸入股票代號 (例如: 0941.HK, AAPL)", value=recommended if recommended else "0941.HK")

if st.button("開始 AI 深度分析"):
    with st.spinner('正在從交易所抓取數據...'):
        data = get_stock_data(ticker_input)
        
        if data:
            # 顯示數據指標
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("預估股息率", f"{data['yield']}%")
            col2.metric("派息比率", f"{data['payout']}%")
            col3.metric("債務權益比", f"{data['debt']}")
            col4.metric("現價", f"{data['price']} {data['currency']}")
            
            st.write(f"**公司名稱:** {data['name']} | **所屬行業:** {data['sector']}")
            st.markdown("---")

            # --- AI 分析部分 (加入多模型輪詢防止 404) ---
            with st.spinner('AI 正在由雲端進行深度分析...'):
                ai_success = False
                # 嘗試多個可用模型名稱
                model_candidates = ['gemini-1.5-flash', 'gemini-pro']
                
                for model_name in model_candidates:
                    try:
                        model = genai.GenerativeModel(model_name)
                        prompt = f"""
                        分析股票 {ticker_input} ({data['name']})：
                        股息率 {data['yield']}%, 派息比率 {data['payout']}%, 債務比率 {data['debt']}。
                        請評估派息持續性並給予 1-10 分安全分。請用繁體中文專業回答。
                        """
                        response = model.generate_content(prompt)
                        st.subheader(f"🤖 AI 深度審核報告 ({model_name})")
                        st.info(response.text)
                        ai_success = True
                        break 
                    except Exception:
                        continue 
                
                if not ai_success:
                    st.error("❌ 所有 AI 模型呼叫失敗。請確認你的新 API Key 已填入 Secrets。")
        else:
            st.error("❌ 找不到股票數據，請檢查代號。")

st.markdown("---")
st.caption("🚨 免責聲明：本工具由 AI 生成分析，僅供參考，不構成任何投資建議。")
