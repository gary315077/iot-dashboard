import time
import random
import json
from datetime import datetime
import paho.mqtt.client as mqtt
import ssl

class FabEquipmentSensor:
    def __init__(self, device_id):
        self.__device_id = device_id
        self.__is_running = True
        self.__vibration_freq = 120.0  
        self.__chamber_temp = 25.0     
        self.__gas_pressure = 1.01     

    @property
    def device_id(self):
        return self.__device_id

    def __simulate_data(self):
        if self.__is_running:
            # 還原基線
            if hasattr(self, '_true_baseline'):
                self.__vibration_freq = self._true_baseline
            
            # 物理老化
            self.__vibration_freq += random.uniform(0.1, 0.4)
            self.__chamber_temp += random.uniform(0.01, 0.05)
            
            #歲修保養
            if self.__vibration_freq > 260.0:
                print("\n[系統提示] 機台歲修保養，數值重置...\n")
                self.__vibration_freq = 120.0
                self.__chamber_temp = 25.0
            
            # 備份基線   
            self._true_baseline = self.__vibration_freq
            
            #噪音與突波
            self.__vibration_freq += random.uniform(-1.5, 1.5) 
            
            #瞬間異常突波
            if random.random() > 0.95: 
                self.__vibration_freq += random.uniform(30.0, 50.0)

    def generate_payload(self):
        self.__simulate_data()
        payload = {
            "device_id": self.device_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "status": "RUNNING" if self.__is_running else "STOPPED",
                "vibration_hz": round(self.__vibration_freq, 2),
                "temperature_c": round(self.__chamber_temp, 2),
                "pressure_atm": round(self.__gas_pressure, 3)
            }
        }
        return json.dumps(payload)

BROKER = "4f12e6a849174187bea125835545e381.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "Gary123"
PASSWORD = "Gary20050905"
TOPIC = "fab/equipment/telemetry"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(">>> 成功連線至 HiveMQ 雲端轉運站！")
    else:
        print(f"連線失敗，錯誤碼: {rc}")

#  主程式
if __name__ == "__main__":
    client = mqtt.Client(client_id="Fab_Edge_Node_01", protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)

    print("嘗試連線中...")
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    
    # 建立機台實體
    equipment_1 = FabEquipmentSensor(device_id="Etch_Machine_A01")
    print(f"啟動 {equipment_1.device_id} 數據上傳管線...\n")

    try:
        while True:
            #產生資料
            payload = equipment_1.generate_payload()
            
            # 發佈
            client.publish(TOPIC, payload)
            print(f"[上傳雲端] {payload}")
            
            time.sleep(2) 
            
    except KeyboardInterrupt:
        print("\n手動中斷連線。")
        client.loop_stop()
        client.disconnect()