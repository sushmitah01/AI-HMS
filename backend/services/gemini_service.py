import google.generativeai as genai
import os
import json
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        self.model = None

    def configure(self):
        # Called after app context is set up or lazily
        api_key = current_app.config.get('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')

    def _get_model(self):
        if not self.model:
            logger.debug("Configuring Gemini model...")
            self.configure()
        return self.model

    def _extract_json(self, text):
        """Extracts JSON from markdown code blocks or raw text."""
        try:
            # Look for JSON code blocks
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            return json.loads(text.strip())
        except Exception as e:
            logger.warning("JSON extraction failed: %s. Raw text: %r", e, text)
            raise e

    def predict_diagnosis(self, symptoms):
        model = self._get_model()
        if not model:
            return [{"condition": "AI Service Unavailable", "confidence": 0}]

        prompt = f"""
        Act as a Doctor. Analyze these symptoms: "{symptoms}".
        Provide a list of up to 3 possible diagnoses.
        Return ONLY a JSON array with objects containing 'condition' (string) and 'confidence' (integer 0-100).
        Example: [{{"condition": "Flu", "confidence": 80}}]
        """
        try:
            response = model.generate_content(prompt)
            logger.debug("Gemini predict_diagnosis response: %s", response.text)
            return self._extract_json(response.text)
        except Exception as e:
            logger.exception("Gemini predict_diagnosis failed")
            return [{"condition": f"Error: {str(e)}", "confidence": 0}]

    def suggest_prescription(self, diagnosis, patient_context=None):
        model = self._get_model()
        if not model:
            return []

        context_str = f" for a {patient_context}" if patient_context else ""
        prompt = f"""
        Act as a Doctor. Suggest a standard prescription for: "{diagnosis}"{context_str}.
        Consider the patient's profile (age, gender, etc.) if provided to adjust dosages or avoid contraindications.
        Return ONLY a JSON array of medicines. Each object:
        - name (string)
        - dosage (string)
        - frequency (string, e.g., '1-0-1')
        - duration (string)
        - notes (string, optional - e.g. 'Take after food')
        Example: [{{"name": "Paracetamol", "dosage": "500mg", "frequency": "1-0-1", "duration": "5 days", "notes": "Take after food"}}]
        """
        try:
            response = model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            logger.exception("Gemini suggest_prescription failed")
            return []
            
    def generate_notes(self, clinical_data):
        model = self._get_model()
        if not model:
            return "AI Service Unavailable"

        prompt = f"""
        Generate specialized medical notes (SOAP format) based on this input:
        {clinical_data}
        Return formatted markdown text.
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating notes: {str(e)}"

    def check_interactions(self, medicines):
        model = self._get_model()
        if not model:
            return "AI Service Unavailable"

        med_list = ", ".join([m.get('name', 'Unknown') for m in medicines])
        prompt = f"""
        Act as a Clinical Pharmacist. Check for drug interactions between these medicines: "{med_list}".
        Return a short warning text if there are interactions, or "No significant interactions found." if safe.
        Keep it concise.
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error checking interactions: {str(e)}"

    def hospital_faq(self, question):
        model = self._get_model()
        if not model: return "AI Service Unavailable"
        
        prompt = f"""
        Act as a Hospital Receptionist. Answer: "{question}".
        Context: AI-HMS General Hospital, 123 Health Ave, Open 24/7. OPD: 9-5. Visiting: 4-7 PM.
        Formatting Rules:
        - Use ONLY bullet points for main facts.
        - EXTREMELY concise. Max 3-4 bullets.
        - No long paragraphs.
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def explain_prescription(self, med_list):
        model = self._get_model()
        if not model: return "AI Service Unavailable"

        prompt = f"""
        Act as a Patient Assistant. Briefly explain: "{med_list}".
        Formatting Rules:
        1. **Medicine Name** (Bold)
        2. **Main Use**: (1 short bullet)
        3. **Key Advice**: (Quick bullets like "Take with food", "No alcohol")
        4. **Safety**: (1 critical warning bullet)
        - NO long intros or outros. Keep it visual and clean.
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def explain_lab_report(self, report_text):
        model = self._get_model()
        if not model: return "AI Service Unavailable"

        prompt = f"""
        Act as a Patient Assistant. Explain simply: "{report_text}".
        Formatting Rules:
        - **Subject**: (Bold)
        - **Current Value**: (Brief)
        - **Status**: (High/Low/Normal - 1 word)
        - **What it means**: (1 short sentence)
        - **Disclaimer**: (1 short line: Consult your doctor.)
        - Use bullets and BOLDS. STRICTLY CONCISE.
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def patient_ai_diagnosis(self, symptoms):
        model = self._get_model()
        if not model:
            return [{"condition": "AI Service Unavailable", "confidence": 0, "specialization": "General Medicine"}]

        prompt = f"""
        Act as a Medical Triage Assistant. Analyze these symptoms for a patient: "{symptoms}".
        1. Identify up to 3 possible conditions.
        2. Recommend the most relevant medical department or specialization for each (e.g., Cardiology, Neurology, ENT, General Medicine).
        3. Do NOT provide medicine dosages.
        
        Return ONLY a JSON array of objects. Each object must have:
        - condition (string)
        - confidence (integer 0-100)
        - specialization (string - Recommended department)
        - advice (string - 1 short tip, e.g., "Stay hydrated", "Avoid bright lights")
        
        Example: [{{"condition": "Migraine", "confidence": 85, "specialization": "Neurology", "advice": "Rest in a quiet, dark room"}}]
        """
        try:
            response = model.generate_content(prompt)
            logger.debug("Gemini patient_ai_diagnosis response: %s", response.text)
            return self._extract_json(response.text)
        except Exception as e:
            logger.exception("Gemini patient_ai_diagnosis failed")
            return [{"condition": f"Analysis Error ({str(e)})", "confidence": 0, "specialization": "Help Desk", "advice": "Please check backend logs."}]

    def symptom_pre_check(self, symptoms):
        model = self._get_model()
        if not model: return "AI Service Unavailable"

        prompt = f"""
        Act as a Triage Assistant. Symptoms: "{symptoms}".
        Formatting Rules:
        - **Potential Cause**: (Short bullet)
        - **Suggested Care**: (Short bullets, e.g., Rest, Fluids)
        - **Urgency**: (Normal/Urgent/Emergency - 1 word)
        - **Disclaimer**: (Required short sentence)
        - Max 5 total bullets. NO paragraphs.
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_system_report(self, stats):
        model = self._get_model()
        if not model: return "AI Service Unavailable"

        prompt = f"""
        Act as a Hospital Management Consultant. Analyze these hospital stats: {json.dumps(stats)}.
        Provide a professional executive summary.
        Formatting Rules:
        - **Executive Overview**: (Short paragraph)
        - **Operational Highlights**: (Bullets)
        - **Resource Recommendations**: (Actionable bullets)
        - **Future Forecast**: (1 sentence)
        - Use Markdown, BOLDS and Bullets. Keep it professional and concise.
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

gemini_service = GeminiService()
