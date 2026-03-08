import streamlit as st
import yfinance as yf
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 配置中心
# ==========================================
# 請確保已在 Google AI Studio 獲取 API Key
GOOGLE_API_KEY = "AIzaSyA0IY4OE-krq8aYtEZ4kGFoOcOT8tbUZp4" 
genai.configure(api_key=GOOGLE_API_KEY)

st.set_page_config(
    page_title="AI 高息股獵人", 
    layout="wide", 
    page_icon="🏹"
)

# ==========================================
# 2. 核心邏輯 (數據抓取與模型偵測)
# ==========================================

@st.cache_data(ttl=3600)
def get_stock_data(ticker):
    """抓取股票數據並進行單位修正"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or 'longName' not in info:
            return None
            
        # 修正股息率 (Dividend Yield)
        dy_raw = info.get("dividendYield", 0) or 0
        div_yield = dy_raw * 100 if dy_raw < 1 else dy_raw
        
        # 修正派息比率 (Payout Ratio)
        pr_raw = info.get("payoutRatio", 0) or 0
        payout = pr_raw * 100 if pr_raw < 2 else pr_raw
        
        return {
            "symbol": ticker,
            "name": info.get("longName", "未知"),
            "yield": round(div_yield, 2),
            "payout": round(payout, 2),
            "debt": round(info.get("debtToEquity", 0) or 0, 2),
            "price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
            "currency": info.get("currency", "HKD"),
            "sector": info.get("sector", "N/A")
        }
    except:
        return None

def get_ai_model():
    """自動偵測可用模型，避免 404 錯誤"""
    try:
        # 列出所有支援生成內容的模型
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先選擇順序
        targets = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for name in targets:
            if name in available:
                return genai.GenerativeModel(name)
        
        if available:
            return genai.GenerativeModel(available[0])
    except Exception as e:
        st.error(f"模型偵測異常: {e}")
    return None

# ==========================================
# 3. 介面佈局
# ==========================================

st.title("🏹 AI 高息股獵人")
st.caption(f"數據更新時間：{datetime.now().strftime('%Y-%m-%d')} | 基於 Gemini 3 Flash 高速分析")

tab1, tab2 = st.tabs(["🔍 自主股票掃描", "🏆 2026 年度推介榜"])

# --- Tab 1: 自主掃描 ---
with tab1:
    c1, c2 = st.columns([2, 2])
    with c1:
        ticker_input = st.text_input("輸入股票代號 (例: 0005.HK, 0941.HK, KO, VZ)", "0941.HK").upper()
        run_analysis = st.button("開始 AI 深度審核")

    if run_analysis:
        with st.spinner('獲取財報數據並召喚 AI 分析師...'):
            data = get_stock_data(ticker_input)
            if data:
                # 數據指標卡片
                met1, met2, met3, met4 = st.columns(4)
                met1.metric("預估股息率", f"{data['yield']}%")
                met2.metric("派息比率", f"{data['payout']}%")
                met3.metric("債務權益比", f"{data['debt']}")
                met4.metric("現價", f"{data['price']} {data['currency']}")
                
                st.write(f"**公司名稱:** {data['name']} | **所屬行業:** {data['sector']}")
                
                # AI 內容生成
                model = get_ai_model()
                if model:
                    prompt = f"""
                    你是一位專業價值投資分析師。請評價股票 {data['symbol']} ({data['name']})：
                    數據：股息率 {data['yield']}%, 派息比率 {data['payout']}%, 債務比率 {data['debt']}。
                    分析要求：
                    1. 評估派息的安全性與可持續性。
                    2. 結合目前的宏觀環境給予評價。
                    3. 給予 1-10 分的「收息推薦度」。
                    請使用繁體中文，條列式回答。
                    """
                    try:
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.subheader(f"🤖 AI 深度審核報告 ({model.model_name.split('/')[-1]})")
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"AI 生成報告失敗，請檢查 API Key 權限。錯誤: {e}")
                else:
                    st.error("找不到可用模型。")
            else:
                st.warning("查無數據，請確認代號格式（港股請加 .HK）。")

# --- Tab 2: 2026 年度推介榜 ---
with tab2:
    st.subheader("🌟 2026 高息防禦型精選")
    st.markdown("這份名單專注於在利率變動環境下具備**強勁現金流**與**穩定派息紀錄**的企業。")
    
    if st.button("🔄 刷新推介榜數據"):
        st.cache_data.clear()

    # 預設推介名單
    recommend_list = ["0941.HK", "0005.HK", "0823.HK", "VZ", "KO", "ABBV"]
    recom_results = []
    
    for r_ticker in recommend_list:
        res = get_stock_data(r_ticker)
        if res: recom_results.append(res)
    
    if recom_results:
        df_recom = pd.DataFrame(recom_results)
        # 整理表格顯示
        st.dataframe(
            df_recom[['symbol', 'name', 'yield', 'payout', 'price', 'currency', 'sector']], 
            use_container_width=True, 
            hide_index=True
        )
        
        # 息率對比圖
        st.subheader("📊 精選股息率對比")
        st.bar_chart(df_recom.set_index('name')['yield'])
        
        # AI 組合建議
        if st.checkbox("查看 AI 組合配置策略"):
            with st.spinner("AI 正在評估配置策略..."):
                model = get_ai_model()
                if model:
                    summary_str = df_recom[['symbol', 'yield', 'sector']].to_string()
                    strategy_prompt = f"分析以下高息股組合的風險散佈，並給予 2026 年的配置建議：\n{summary_str}"
                    res_strat = model.generate_content(strategy_prompt)
                    st.success(res_strat.text)
    else:
        st.error("暫時無法獲取推介清單數據。")

# --- Footer ---
st.markdown("---")
st.caption("🚨 免責聲明：本工具由 AI 生成分析，僅供學習參考，不構成任何形式的投資建議。")