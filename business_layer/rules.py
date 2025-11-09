class InsuranceRules:
    """
    Define reglas de negocio para decidir:
    - Si una propiedad es asegurable
    - Qué tipo de seguro aplicar
    - Acciones recomendadas
    """
    def __init__(self):
        # Umbrales de riesgo (0-100)
        self.thresholds = {
            "low": 30,    # riesgo bajo → asegurable estándar
            "medium": 60, # riesgo medio → asegurable con prima alta o mitigación
            "high": 100   # riesgo alto → no asegurable o medidas obligatorias
        }

    # -----------------------------
    # 1. Evaluar asegurabilidad
    # -----------------------------
    def evaluate_insurability(self, risk_score):
        if risk_score <= self.thresholds['low']:
            return "Asegurable estándar"
        elif risk_score <= self.thresholds['medium']:
            return "Asegurable con prima elevada / medidas de mitigación"
        else:
            return "No asegurable o medidas obligatorias"

    # -----------------------------
    # 2. Sugerir tipo de póliza
    # -----------------------------
    def suggest_policy_type(self, factors):
        """
        Recibe los factores de riesgo calculados en RiskModel.get_factors()
        y recomienda tipo de seguro o cobertura especial
        """
        policy = []

        # Riesgo de inundación
        if factors.get('flood_rate',0) > 2:
            policy.append("Cobertura contra inundaciones")

        # Riesgo sísmico
        if factors.get('seismic_rate',0) > 2:
            policy.append("Cobertura sísmica")

        # Huracanes / tormentas
        if factors.get('hurricane_rate',0) > 1:
            policy.append("Cobertura por huracanes")

        # Incendios forestales
        if factors.get('fire_rate',0) > 1:
            policy.append("Cobertura contra incendios")

        # Riesgo volcánico
        if factors.get('volcano_distance_km',1000) < 50:
            policy.append("Cobertura por actividad volcánica")

        # Riesgo climático general
        if factors.get('temperature',0) > 40:
            policy.append("Cobertura por ola de calor / daños climáticos")

        return policy if policy else ["Cobertura estándar"]

    # -----------------------------
    # 3. Recomendaciones de mitigación
    # -----------------------------
    def mitigation_actions(self, risk_score, factors):
        """
        Sugerencias para reducir riesgo y mejorar asegurabilidad
        """
        actions = []

        if risk_score > self.thresholds['medium']:
            actions.append("Evaluar reubicación de la propiedad")
        if factors.get('flood_rate',0) > 2:
            actions.append("Instalar drenaje o barreras anti-inundación")
        if factors.get('vegetation',0) < 0.3:
            actions.append("Aumentar cobertura vegetal / protección contra erosión")
        if factors.get('volcano_distance_km',1000) < 50:
            actions.append("Revisar planes de evacuación y seguros especializados")

        return actions if actions else ["No se requieren acciones adicionales"]

