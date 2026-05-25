import json
import paho.mqtt.client as mqtt
import ssl
from pymongo import MongoClient

# MongoDB Atlas 雲端資料庫
MONGO_URI = "mongodb+srv://gary315077_db_user:ErI87hh8cMUSHlPq@cluster0.heyijrc.mongodb.net/?appName=Cluster0"

try:
    print("正在連線至 MongoDB Atlas...")
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # 資料庫資料表
    db = mongo_client["FabMonitoring"]
    collection = db["telemetry"]
    #測試連線
    mongo_client.server_info() 
    print(">>> 成功連線至 MongoDB 雲端資料庫！\n")
except Exception as e:
    print(f"MongoDB 連線失敗，請檢查網路或密碼: {e}")
    exit()

# HiveMQ設定
BROKER = "4f12e6a849174187bea125835545e381.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "Gary123"
PASSWORD = "Gary20050905"
TOPIC = "fab/equipment/telemetry"

# MQTT接收 存檔
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(">>> 成功連線至 HiveMQ 轉運站！開始監聽機台數據...")
        client.subscribe(TOPIC)
    else:
        print(f"HiveMQ 連線失敗，錯誤碼: {rc}")

def on_message(client, userdata, msg):
    #收到資料時會觸發函式
    payload_str = msg.payload.decode('utf-8')
    print(f"[攔截資料] {payload_str}")
    
    try:
        # JSON轉回Python字典
        data = json.loads(payload_str)
        #存進 MongoDB
        collection.insert_one(data)
        print("   └─> [成功] 已永久寫入 MongoDB 資料庫！\n")
    except Exception as e:
        print(f"   └─> [失敗] 寫入資料庫發生錯誤: {e}\n")

if __name__ == "__main__":
    # 初始化MQTT 訂閱者Client
    client = mqtt.Client(client_id="Fab_Cloud_Backend", protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)

    client.connect(BROKER, PORT, 60)
    
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n系統關閉。")
        client.disconnect()