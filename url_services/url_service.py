import requests
import time
import threading
import pandas as pd
from url_services.repository import set

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
                for measurment in patient_json["trace"]["sensors"]:
                    measurment['anomaly'] = str(measurment['anomaly'])
                    sensors_dict[p_id].append(measurment)
                    
            dfs = [pd.DataFrame(sensors_dict[i]) for i in self.id_range]
            for i in self.id_range:
                dfs[i-1]["patient_id"] = i
            df = pd.concat(dfs)
            set(df)
        print(f"Service {self.Name} finished operating")
        
            
    def set_flag(self, flag):
        self.ifRunFlag = flag
        

            
                
