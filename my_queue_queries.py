

def get_current_patient_data(df, current_patient):
    res = df[df["patient_id"] == current_patient].drop('patient_id', axis=1)
    print("here")
    return res

def update_table_patient_data(df, current_patient):
    res = df[df['patient_id'] == current_patient]
    print(current_patient)
    return res

def get_patient_values(df, current_patient):
    res = df[df['patient_id'] == current_patient]['value']
    print(current_patient)
    return res

def get_sensors_values(df, sensor_type, step):
    res = df[df["name"] == sensor_type]["value"]
    return res.iloc[::step]