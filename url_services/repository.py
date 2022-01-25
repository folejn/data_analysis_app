from redis import Redis
import pandas as pd
import pyarrow as pa
from datetime import datetime
from rq import Queue

conn1 = Redis('127.0.0.1', 6379)
q1 = Queue('low', connection=conn1, job_timeout='3m')
db = Redis('127.0.0.1', 6379, db=1)

anomalies_db = Redis('127.0.0.1', 6379, db=2)

measurements_list = "measurments"
def set(df):
    context = pa.default_serialization_context()
    db.lpush(measurements_list,  context.serialize(df).to_buffer().to_pybytes())
    if db.llen(measurements_list) > 600:
        db.rpop(measurements_list)
    
def get(index):
    #df = pd.read_msgpack(db.lindex(measurements_list, index))
    context = pa.default_serialization_context()
    df = context.deserialize(db.lindex(measurements_list, index))
    return df

def get_latest():
    context = pa.default_serialization_context()
    df = context.deserialize(db.lindex(measurements_list, 0))
    return df

def get_all():
    context = pa.default_serialization_context()
    listed = db.lrange(measurements_list,0,-1)
    dfs = []
    for elem in listed:
        single_df = context.deserialize(elem)
        dfs.append(single_df)
    return pd.concat(dfs)


def add_anomaly(current_patient, df):
    context = pa.default_serialization_context()
    df['datetime'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    anomalies_db.lpush(current_patient, context.serialize(df).to_buffer().to_pybytes())
    
def get_anomalies(current_patient):
    context = pa.default_serialization_context()
    listed = anomalies_db.lrange(current_patient,0,-1)
    dfs = []
    for elem in listed:
        single_df = context.deserialize(elem)
        dfs.append(single_df)
    try:
        return pd.concat(dfs)
    except ValueError:
        return pd.DataFrame()