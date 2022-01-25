import requests
import time
import threading
import pandas as pd
from url_services.repository import set, add_anomaly

class UrlService(threading.Thread):
    def __init__(self, threadName):
        threading.Thread.__init__(self)
        self.__delay = 1
        self.Name = threadName
        self.ifRunFlag = True
        self.id_range = range(1, 7)
    def run(self):
        print(f"Service {self.Name} started operating...")
        while self.ifRunFlag:
            time.sleep(self.__delay)
            sensors_dict = {}
            for p_id in self.id_range:
                if p_id not in sensors_dict.keys():
                    sensors_dict[p_id] = []
                patient = requests.get(url=f"http://tesla.iem.pw.edu.pl:9080/v2/monitor/{p_id}")
                patient_json = patient.json()
                anomaly_detected = False
                for measurment in patient_json["trace"]["sensors"]:
                    if measurment['anomaly']:
                        anomaly_detected = True
                    measurment['anomaly'] = str(measurment['anomaly'])
                    sensors_dict[p_id].append(measurment)
                if anomaly_detected:
                    add_anomaly( p_id, pd.DataFrame(sensors_dict[p_id]))
                    
            dfs = [pd.DataFrame(sensors_dict[i]) for i in self.id_range]
            for i in self.id_range:
                dfs[i-1]["patient_id"] = i
            df = pd.concat(dfs)
            set(df)
        print(f"Service {self.Name} finished operating")
        
            
    def set_flag(self, flag):
        self.ifRunFlag = flag
        
service = UrlService("Request for data")
service.start()
time.sleep(6)
            
                
