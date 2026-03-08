import streamlit as st
import yfinance as yf
import google.generativeai as genai
import os

# --- 1. 配置與安全檢查 ---
st.set_page_config(page_title="AI 高息股獵人", layout="wide", page_icon="🏹")

# 從 Streamlit Secrets 讀取 Key
API_KEY = st.secrets.get("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ 找不到 GOOGLE_API_KEY！請確保已在 Streamlit Cloud 的 Secrets 中設定。")
    st.stop()

# 初始化配置：不指定版本，讓 SDK 自動選擇最新的穩定版本
genai.configure(api_key=API_KEY)

# --- 2. 數據獲取 ---
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # yfinance 數據有時是小數，有時是百分比，這裡做統一轉換
        dy = (info.get("dividendYield", 0) or 0) * 100
        pr = (info.get("payoutRatio", 0) or 0) * 100
        return {
            "name": info.get("longName", "未知公司"),
            "yield": round(dy, 2) if dy < 100 else round(dy/100, 2),
            "payout": round(pr, 2) if pr < 200 else round(pr/100, 2),
            "price": info.get("currentPrice", 0),
            "currency": info.get("currency", "HKD")
        }
    except Exception as e:
        return None

# --- 3. 網頁介面 ---
st.title("🏹 AI 高息股獵人 (最新穩定版)")

# 熱門推介位
st.subheader("🔥 今日推介")
hot_list = ["0941.HK", "0005.HK", "0011.HK"]
cols = st.columns(len(hot_list))
selected_ticker = None
for i, t in enumerate(hot_list):
    if cols[i].button(f"查看 {t}", key=f"btn_{t}"):
        selected_ticker = t

st.markdown("---")
ticker_input = st.text_input("輸入股票代號 (例如: 0941.HK)", value=selected_ticker if selected_ticker else "0941.HK")

if st.button("啟動 AI 深度分析"):
    data = get_stock_info(ticker_input)
    if data:
        st.write(f"### {data['name']} 數據概覽")
        c1, c2, c3 = st.columns(3)
        c1.metric("預估股息率", f"{data['yield']}%")
        c2.metric("派息比率", f"{data['payout']}%")
        c3.metric("現價", f"{data['price']} {data['currency']}")
        
        with st.spinner('AI 正在由雲端進行分析...'):
            try:
                # 使用最新的 1.5-flash 模型，這是目前最穩定且快速的選擇
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"分析股票 {ticker_input}：股息率 {data['yield']}%, 派息比率 {data['payout']}%。請評估其派息持續性並給予 1-10 安全分。繁體中文回答。"
                
                # 呼叫 generate_content
                response = model.generate_content(prompt)
                
                st.subheader("🤖 AI 投資報告")
                st.success("分析完成！")
                st.write(response.text)
            except Exception as e:
                # 這裡會印出具體的錯誤，幫助我們診斷
                st.error(f"❌ AI 分析出錯：{str(e)}")
                st.info("💡 建議：請檢查 GitHub 上的 requirements.txt 是否已更新。")
    else:
        st.error("❌ 無法獲取股票數據，請檢查代號是否正確。")

st.markdown("---")
st.caption("🚨 免責聲明：本工具由 AI 生成，僅供參考，不構成投資建議。")
