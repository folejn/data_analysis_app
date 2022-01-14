

def get_current_patient_data(df, current_patient):
    res = df[df["patient_id"] == current_patient].drop('patient_id', axis=1)
    print("here")
    return res

def update_table_patient_data(df, current_patient):
    res = df[df['patient_id'] == current_patient]
    print("here")
    return res

def get_patient_values(df, current_patient):
    res = df[df['patient_id'] == current_patient]['value']
    print("here")
    return res