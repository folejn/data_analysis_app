import requests, json
import time
import threading

class UrlService(threading.Thread):
    def __init__(self, threadName, threadID ,url, repository):
        threading.Thread.__init__(self)
        self.url = url
        self.__delay = 1
        self.Name = threadName
        self.ID = threadID
        self.repository = repository
    def run(self):
        print("Service started operating...")
        self._fetch();
        print("Service finished operating")
    def _fetch(self):
        count = 50
        while count > 0:
            time.sleep(self.__delay)
            url = requests.get(self.url)
            data = json.loads(url.text)
            print(f"{data}")
            self.repository.add(data)
            count -= 1
            
                
