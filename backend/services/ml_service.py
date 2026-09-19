import joblib
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)


class MLService:
    def __init__(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_path, '../ml/models')
        
        try:
            self.risk_model = joblib.load(os.path.join(model_path, 'health_risk_model.joblib'))
            self.readmission_model = joblib.load(os.path.join(model_path, 'readmission_model.joblib'))
        except Exception as e:
            logger.error("Error loading ML models: %s", e)
            self.risk_model = None
            self.readmission_model = None

    def predict_health_risk(self, data):
        if not self.risk_model: return "Model Error"

        # Reindex explicitly to the order the model was trained on — do not
        # rely on incoming dict/JSON key order, which is not guaranteed
        # (Flask's JSON encoder can reorder keys, and newer scikit-learn
        # versions raise a hard error on any column-order mismatch).
        df = pd.DataFrame([data])[list(self.risk_model.feature_names_in_)]
        prediction = self.risk_model.predict(df)[0]
        return prediction

    def predict_readmission(self, data):
        if not self.readmission_model: return 0.0

        df = pd.DataFrame([data])[list(self.readmission_model.feature_names_in_)]
        probability = self.readmission_model.predict_proba(df)[0][1] # Prob of class 1 (Yes)
        return round(float(probability) * 100, 2)

    def predict_disease(self, symptoms_text):
        # Basic Rule-Based System (Mock AI)
        symptoms = symptoms_text.lower()
        predictions = []

        rules = {
            'flu': ['fever', 'cough', 'headache', 'fatigue'],
            'covid-19': ['fever', 'cough', 'loss of taste', 'breathing difficulty'],
            'diabetes': ['thirst', 'frequency of urination', 'hunger', 'fatigue'],
            'hypertension': ['headache', 'dizziness', 'blurred vision'],
            'migraine': ['headache', 'nausea', 'sensitivity to light'],
            'malaria': ['fever', 'chills', 'sweating', 'headache'],
            'pneumonia': ['cough', 'fever', 'chills', 'breathing difficulty']
        }

        for disease, keywords in rules.items():
            match_count = sum(1 for k in keywords if k in symptoms)
            if match_count >= 1:
                confidence = min((match_count / len(keywords)) * 100 + 40, 95) # Base 40%, cap 95%
                predictions.append({'condition': disease.title(), 'confidence': round(confidence, 1)})
        
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return predictions[:3] if predictions else [{'condition': 'General Viral Infection', 'confidence': 30.0}]

ml_service = MLService()
