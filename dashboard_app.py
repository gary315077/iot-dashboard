import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from sklearn.ensemble import IsolationForest
import requests
import time 

st.set_page_config(page_title="半導體機台 AI 戰情室", layout="wide")
st.title("🏭 半導體設備預測性維護 - AI 即時監測儀表板")

MONGO_URI = st.secrets["MONGO_URI"]

@st.cache_data(ttl=5) 
def fetch_data():
    client = MongoClient(MONGO_URI)
    db = client["FabMonitoring"]
    collection = db["telemetry"]
    
    recent_data = list(collection.find({}).sort("timestamp", -1).limit(300))
    
    df = pd.json_normalize(recent_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df.sort_values('timestamp')

def send_discord_alert(vibration_value):
    webhook_url = st.secrets["DISCORD_WEBHOOK"]
    
    data = {
        "embeds": [{
            "title": "⚠️ 設備異常預警",
            "description": "AI 孤立森林模型偵測到異常，請派員確認！",
            "color": 16711680,
            "fields": [
                {"name": "機台代號", "value": "Etch_Machine_A01", "inline": True},
                {"name": "當前震動頻率", "value": f"{vibration_value:.2f} Hz", "inline": True}
            ]
        }]
    }
    requests.post(webhook_url, json=data)

try:
    df = fetch_data()

    st.sidebar.header("AI 模型參數設定")
    contamination = st.sidebar.slider("異常偵測靈敏度 (Contamination)", 0.01, 0.2, 0.05)
    
    features = ['metrics.vibration_hz', 'metrics.temperature_c']
    model = IsolationForest(contamination=contamination, random_state=42)
    df['anomaly_score'] = model.fit_predict(df[features])
    
    df['is_anomaly'] = df['anomaly_score'].apply(lambda x: "異常 (Danger)" if x == -1 else "正常 (Normal)")

    if df['anomaly_score'].iloc[-1] == -1:
        send_discord_alert(df['metrics.vibration_hz'].iloc[-1])
        st.toast("⚠️ 異常警報已推播至 Discord 頻道！", icon="🚨")

    col1, col2, col3 = st.columns(3)
    col1.metric("總監測數據量", f"{len(df)} 筆")
    col2.metric("偵測到異常次數", f"{len(df[df['anomaly_score'] == -1])} 筆")
    col3.metric("目前機台狀態", "警告" if df['anomaly_score'].iloc[-1] == -1 else "良好")

    st.subheader("📊 機台震動頻率即時分析")
    fig = px.scatter(df, x='timestamp', y='metrics.vibration_hz', 
                     color='is_anomaly', 
                     color_discrete_map={"正常 (Normal)": "blue", "異常 (Danger)": "red"},
                     title="震動頻率時間序列圖 (AI 標記異常點)")
    fig.add_hline(y=135, line_dash="dash", line_color="orange", annotation_text="靜態安全閾值 (135Hz)")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 原始數據明細")
    st.dataframe(df[['timestamp', 'device_id', 'metrics.vibration_hz', 'metrics.temperature_c', 'is_anomaly']].tail(10))

    time.sleep(5) 
    st.rerun()

except Exception as e:
    st.error(f"連線失敗或資料不足: {e}")
    st.info("請確保 iot_publisher.py 正在執行中，且資料庫內有足夠數據。")
