# processing_layer/risk.py
def calculate_risk(df):
    avg_temp = df["temperature"].mean()
    avg_precip = df["precipitation"].mean()
    score = (avg_precip * 0.7 + avg_temp * 0.3) / 100
    if score > 0.7:
        return "Alto"
    elif score > 0.4:
        return "Medio"
    else:
        return "Bajo"
