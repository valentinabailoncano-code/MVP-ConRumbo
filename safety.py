import re
from typing import List, Optional, Dict

class SafetyGuardrails:
    def __init__(self):
        # Patrones que indican preguntas diagnósticas prohibidas
        self.diagnostic_patterns = [
            r"¿tengo.*?",
            r"¿es.*?(infarto|ictus|cáncer|enfermedad)",
            r"¿qué.*?(enfermedad|diagnóstico)",
            r"¿me.*?(muero|voy a morir)",
            r"¿estoy.*?(enfermo|grave)",
            r"¿será.*?(grave|serio|malo)",
            r"diagnóstica",
            r"diagnostica",
            r"qué tengo",
            r"qué me pasa",
            r"estoy enfermo",
            r"voy a morir"
        ]
        
        # Patrones que indican situaciones de emergencia inmediata
        self.emergency_patterns = [
            r"no respira",
            r"inconsciente",
            r"sin pulso",
            r"sangrado.*?(intenso|abundante|no para)",
            r"dolor.*?pecho.*?(intenso|opresivo)",
            r"convulsiones",
            r"cianosis",
            r"azul",
            r"morado",
            r"asfixia",
            r"atragantado",
            r"anafilaxia",
            r"shock"
        ]
        
        # Respuestas estándar para diferentes tipos de consultas prohibidas
        self.safety_responses = {
            "diagnostic": "No puedo realizar diagnósticos médicos. Si tienes síntomas preocupantes o dudas sobre tu salud, consulta con un profesional médico o llama al 112 si es una emergencia.",
            "emergency_immediate": "Esta situación requiere atención médica inmediata. LLAMA AL 112 AHORA y sigue las instrucciones que te proporcionen.",
            "general_safety": "Recuerda que esta aplicación es solo para primeros auxilios y no sustituye la atención médica profesional. Ante cualquier duda, consulta con un médico o llama al 112."
        }
    
    def check_query_safety(self, query: str) -> Dict[str, any]:
        """
        Verifica si una consulta es segura y apropiada.
        
        Returns:
            Dict con 'is_safe', 'violation_type', 'response' y 'should_escalate'
        """
        query_lower = query.lower()
        
        # Verificar patrones de emergencia inmediata
        for pattern in self.emergency_patterns:
            if re.search(pattern, query_lower):
                return {
                    "is_safe": False,
                    "violation_type": "emergency_immediate",
                    "response": self.safety_responses["emergency_immediate"],
                    "should_escalate": True,
                    "escalation_message": "EMERGENCIA DETECTADA: Llamar al 112 inmediatamente"
                }
        
        # Verificar patrones diagnósticos
        for pattern in self.diagnostic_patterns:
            if re.search(pattern, query_lower):
                return {
                    "is_safe": False,
                    "violation_type": "diagnostic",
                    "response": self.safety_responses["diagnostic"],
                    "should_escalate": False,
                    "escalation_message": None
                }
        
        # Consulta segura
        return {
            "is_safe": True,
            "violation_type": None,
            "response": None,
            "should_escalate": False,
            "escalation_message": None
        }
    
    def validate_protocol_response(self, response: str, protocol_type: str) -> Dict[str, any]:
        """
        Valida que una respuesta de protocolo incluya las advertencias de seguridad necesarias.
        """
        response_lower = response.lower()
        
        # Verificar que incluya disclaimer médico
        has_medical_disclaimer = any(phrase in response_lower for phrase in [
            "no sustituye", "atención médica", "profesional médico", "112"
        ])
        
        # Verificar advertencias específicas por tipo de protocolo
        required_warnings = self._get_required_warnings(protocol_type)
        missing_warnings = []
        
        for warning_key, warning_phrases in required_warnings.items():
            if not any(phrase in response_lower for phrase in warning_phrases):
                missing_warnings.append(warning_key)
        
        is_valid = has_medical_disclaimer and len(missing_warnings) == 0
        
        return {
            "is_valid": is_valid,
            "has_medical_disclaimer": has_medical_disclaimer,
            "missing_warnings": missing_warnings,
            "suggested_additions": self._get_suggested_additions(missing_warnings)
        }
    
    def _get_required_warnings(self, protocol_type: str) -> Dict[str, List[str]]:
        """Obtiene las advertencias requeridas para cada tipo de protocolo."""
        
        common_warnings = {
            "emergency_call": ["112", "emergencias", "llamar"]
        }
        
        specific_warnings = {
            "rcp": {
                **common_warnings,
                "training": ["entrenamiento", "curso", "capacitación"],
                "professional": ["profesional", "médico", "sanitario"]
            },
            "atragantamiento": {
                **common_warnings,
                "consciousness": ["conciencia", "inconsciente", "desmaya"]
            },
            "hemorragias": {
                **common_warnings,
                "severe_bleeding": ["sangrado intenso", "no para", "abundante"]
            },
            "quemaduras": {
                **common_warnings,
                "severe_burns": ["grave", "extensa", "profunda"]
            },
            "anafilaxia": {
                **common_warnings,
                "immediate": ["inmediatamente", "urgente", "rápido"]
            }
        }
        
        return specific_warnings.get(protocol_type, common_warnings)
    
    def _get_suggested_additions(self, missing_warnings: List[str]) -> List[str]:
        """Genera sugerencias para completar advertencias faltantes."""
        
        suggestions = {
            "emergency_call": "Recuerda llamar al 112 si la situación empeora o no mejora.",
            "training": "Es recomendable recibir entrenamiento en primeros auxilios.",
            "professional": "Esta guía no sustituye la atención médica profesional.",
            "consciousness": "Si la persona pierde la conciencia, llama al 112 inmediatamente.",
            "severe_bleeding": "Si el sangrado es intenso o no se controla, llama al 112.",
            "severe_burns": "Para quemaduras graves o extensas, busca atención médica inmediata.",
            "immediate": "En caso de anafilaxia, actúa inmediatamente y llama al 112."
        }
        
        return [suggestions.get(warning, "") for warning in missing_warnings if warning in suggestions]
    
    def add_safety_footer(self, response: str, protocol_type: str = "general") -> str:
        """Agrega un pie de página de seguridad a cualquier respuesta."""
        
        footer_templates = {
            "rcp": "\n\n⚠️ IMPORTANTE: Esta guía no sustituye el entrenamiento en RCP. Si no tienes experiencia, llama al 112 inmediatamente.",
            "emergency": "\n\n🚨 RECUERDA: Ante cualquier duda o si la situación empeora, llama al 112 sin demora.",
            "general": "\n\n💡 NOTA: Esta aplicación proporciona guías de primeros auxilios, pero no sustituye la atención médica profesional."
        }
        
        footer = footer_templates.get(protocol_type, footer_templates["general"])
        
        # Evitar duplicar el footer si ya existe
        if footer.strip() not in response:
            response += footer
        
        return response
    
    def check_user_feedback_safety(self, feedback: str) -> Dict[str, any]:
        """Verifica si el feedback del usuario indica una situación de emergencia."""
        
        emergency_indicators = [
            "no respira", "inconsciente", "azul", "morado", "convulsiones",
            "sangrado mucho", "no para de sangrar", "muy grave", "empeora mucho"
        ]
        
        feedback_lower = feedback.lower()
        
        for indicator in emergency_indicators:
            if indicator in feedback_lower:
                return {
                    "is_emergency": True,
                    "indicator": indicator,
                    "action": "immediate_112_call",
                    "message": f"Situación de emergencia detectada: {indicator}. Llama al 112 inmediatamente."
                }
        
        return {
            "is_emergency": False,
            "indicator": None,
            "action": "continue_protocol",
            "message": None
        }

