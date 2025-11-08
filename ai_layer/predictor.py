# ai_layer/predictor.py
import google.generativeai as genai

genai.configure(api_key="AIzaSyDSiYA9jToklR5j1KOPiop9ogCjUL5HLQ0")
#for m in genai.list_models():
 #   print(m.name)

def explain_risk(risk_level, location):
    prompt = f"El riesgo en {location} es {risk_level}. Genera una explicación simple y empática para un asegurado."
    response = genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt)
    return response.text
