from redis import Redis
import pandas as pd
import pyarrow as pa

db = Redis('127.0.0.1', 6379, db=1)
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