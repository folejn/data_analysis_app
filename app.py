from flask import Flask
from repository.patient_repository import PatientRepository
from url_services.url_service import UrlService

app = Flask(__name__)
repository = PatientRepository()
url_service = UrlService("service", 0, "http://tesla.iem.pw.edu.pl:9080/v2/monitor/2", repository)
url_service.start()
 
@app.route('/')
def hello_world():
    return f'Hello World \n {repository.getAll()}'
