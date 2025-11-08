# business_layer/rules.py
def compute_payout(risk, insured_value):
    if risk == "Alto":
        return insured_value * 0.9
    elif risk == "Medio":
        return insured_value * 0.5
    else:
        return insured_value * 0.1
