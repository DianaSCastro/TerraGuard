# main.py
from data_layer.data import get_weather
from processing_layer.risk_model import calculate_risk
from ai_layer.predictor import explain_risk
from business_layer.rules import compute_payout

def run_system():
    lat, lon = 25.67, -100.31  # Monterrey
    insured_value = 10000

    df = get_weather(lat, lon)
    risk = calculate_risk(df)
    payout = compute_payout(risk, insured_value)
    explanation = explain_risk(risk, "Monterrey, MX")

    print("Nivel de riesgo:", risk)
    print("Monto de pago estimado:", payout)
    print("Gemini dice:", explanation)

if __name__ == "__main__":
    run_system()
