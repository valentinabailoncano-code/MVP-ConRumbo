# backend/core/safety.py
from __future__ import annotations
import re
from typing import List, Optional, Dict, Any


class SafetyGuardrails:
    """
    Guardarraíles de seguridad para ConRumbo.
    - Detecta consultas diagnósticas (no permitidas).
    - Detecta emergencias que requieren escalar a 112.
    - Añade/valida avisos de seguridad en respuestas.
    - Ofrece un método `check(payload)` compatible con conrumbo.py
      (acepta dict con posibles campos: query, intent, user_response, etc.).
    """

    def __init__(self, emergency_number: str = "112"):
        self.emergency_number = emergency_number

        # Patrones diagnósticos (no permitidos)
        diag_raw = [
            r"¿\s*tengo\b.*",
            r"¿\s*es\b.*\b(infarto|ictus|cáncer|enfermedad)\b",
            r"¿\s*qué\b.*\b(enfermedad|diagnóstico)\b",
            r"¿\s*me\b.*\b(muero|voy a morir)\b",
            r"¿\s*estoy\b.*\b(enfermo|grave)\b",
            r"¿\s*será\b.*\b(grave|serio|malo)\b",
            r"\bdiagnó?stic[ao]s?\b",
            r"\bqué\s+tengo\b",
            r"\bqué\s+me\s+pasa\b",
            r"\bestoy\s+enfermo\b",
            r"\bvoy\s+a\s+morir\b",
        ]

        # Patrones de emergencia inmediata
        emerg_raw = [
            r"\bno\s+respira\b",
            r"\binconsciente\b",
            r"\bsin\s+pulso\b",
            r"\bsangrado\b.*\b(intenso|abundante|no\s+para)\b",
            r"\bdolor\b.*\bpecho\b.*\b(intenso|opresivo)\b",
            r"\bconvulsiones?\b",
            r"\bcianosis\b",
            r"\bazul\b",
            r"\bmorado\b",
            r"\basfixia\b",
            r"\batragantad[oa]\b",
            r"\banafilaxia\b",
            r"\bshock\b",
            r"\bparada\s+cardio(respiratoria|vascular)\b",
        ]

        flags = re.IGNORECASE | re.UNICODE
        self._diagnostic_patterns = [re.compile(p, flags) for p in diag_raw]
        self._emergency_patterns = [re.compile(p, flags) for p in emerg_raw]

        # Respuestas estandarizadas
        self.safety_responses = {
            "diagnostic": (
                "No puedo realizar diagnósticos médicos. Si tienes síntomas preocupantes o dudas "
                f"sobre tu salud, consulta con un profesional médico o llama al {self.emergency_number} si es una emergencia."
            ),
            "emergency_immediate": (
                f"Esta situación requiere atención médica inmediata. LLAMA AL {self.emergency_number} AHORA "
                "y sigue las instrucciones que te proporcionen."
            ),
            "general_safety": (
                "Recuerda que esta aplicación es solo para primeros auxilios y no sustituye la atención médica profesional. "
                f"Ante cualquier duda, consulta con un médico o llama al {self.emergency_number}."
            ),
        }

    # ---------- API de alto nivel (compatibilidad con conrumbo.py) ----------
    def check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifica seguridad a partir de un payload (dict). Busca texto en:
        - payload['query'], payload['user_response'], payload['intent'] (si son strings)
        Devuelve un dict con: allowed, violation_type, response, should_escalate, escalation_message.
        """
        texts: List[str] = []
        for key in ("query", "user_response", "intent"):
            val = payload.get(key)
            if isinstance(val, str) and val.strip():
                texts.append(val.strip())

        # Si no hay texto, no bloquea (pero recuerda disclaimer general)
        if not texts:
            return {
                "allowed": True,
                "violation_type": None,
                "response": None,
                "should_escalate": False,
                "escalation_message": None,
            }

        # Evalúa cada texto; si alguno dispara emergencia → escalar
        # si alguno dispara diagnóstico → bloquear pero sin escalar
        emergency_hit = None
        diagnostic_hit = None

        for t in texts:
            qres = self.check_query_safety(t)
            if not qres["is_safe"]:
                if qres["violation_type"] == "emergency_immediate":
                    emergency_hit = qres
                    break  # prioridad máxima
                elif qres["violation_type"] == "diagnostic":
                    diagnostic_hit = qres

        if emergency_hit:
            return {
                "allowed": False,
                "violation_type": "emergency_immediate",
                "response": self.safety_responses["emergency_immediate"],
                "should_escalate": True,
                "escalation_message": f"EMERGENCIA DETECTADA: Llamar al {self.emergency_number} inmediatamente",
            }

        if diagnostic_hit:
            return {
                "allowed": False,
                "violation_type": "diagnostic",
                "response": self.safety_responses["diagnostic"],
                "should_escalate": False,
                "escalation_message": None,
            }

        # Seguro
        return {
            "allowed": True,
            "violation_type": None,
            "response": None,
            "should_escalate": False,
            "escalation_message": None,
        }

    # ---------- API clásica (mejorada) ----------
    def check_query_safety(self, query: str) -> Dict[str, Any]:
        """
        Verifica si una consulta es segura y apropiada.
        Returns:
            Dict con 'is_safe', 'violation_type', 'response' y 'should_escalate'
        """
        q = (query or "").lower()

        for pat in self._emergency_patterns:
            if pat.search(q):
                return {
                    "is_safe": False,
                    "violation_type": "emergency_immediate",
                    "response": self.safety_responses["emergency_immediate"],
                    "should_escalate": True,
                    "escalation_message": f"EMERGENCIA DETECTADA: Llamar al {self.emergency_number} inmediatamente",
                }

        for pat in self._diagnostic_patterns:
            if pat.search(q):
                return {
                    "is_safe": False,
                    "violation_type": "diagnostic",
                    "response": self.safety_responses["diagnostic"],
                    "should_escalate": False,
                    "escalation_message": None,
                }

        return {
            "is_safe": True,
            "violation_type": None,
            "response": None,
            "should_escalate": False,
            "escalation_message": None,
        }

    def validate_protocol_response(self, response: str, protocol_type: str) -> Dict[str, Any]:
        """
        Valida que una respuesta de protocolo incluya las advertencias de seguridad necesarias.
        """
        text = (response or "").lower()

        # Debe mencionar descargo/112
        has_medical_disclaimer = any(
            p in text for p in ["no sustituye", "atención médica", "profesional médico", str(self.emergency_number)]
        )

        required_warnings = self._get_required_warnings(protocol_type)
        missing_warnings: List[str] = []

        for warning_key, warning_phrases in required_warnings.items():
            if not any(phrase in text for phrase in warning_phrases):
                missing_warnings.append(warning_key)

        is_valid = has_medical_disclaimer and len(missing_warnings) == 0

        return {
            "is_valid": is_valid,
            "has_medical_disclaimer": has_medical_disclaimer,
            "missing_warnings": missing_warnings,
            "suggested_additions": self._get_suggested_additions(missing_warnings),
        }

    def add_safety_footer(self, response: str, protocol_type: str = "general") -> str:
        """Agrega un pie de seguridad a cualquier respuesta (evita duplicados)."""

        footer_templates = {
            "rcp": (
                f"\n\n⚠️ IMPORTANTE: Esta guía no sustituye el entrenamiento en RCP. "
                f"Si no tienes experiencia, llama al {self.emergency_number} inmediatamente."
            ),
            "emergency": (
                f"\n\n🚨 RECUERDA: Ante cualquier duda o si la situación empeora, "
                f"llama al {self.emergency_number} sin demora."
            ),
            "general": (
                "\n\n💡 NOTA: Esta aplicación proporciona guías de primeros auxilios, "
                "pero no sustituye la atención médica profesional."
            ),
        }

        footer = footer_templates.get(protocol_type, footer_templates["general"])
        if footer.strip() not in (response or ""):
            return (response or "") + footer
        return response

    def check_user_feedback_safety(self, feedback: str) -> Dict[str, Any]:
        """
        Verifica si el feedback del usuario indica una emergencia.
        Devuelve un dict homogéneo con is_emergency y acción sugerida.
        """
        indicators = [
            "no respira",
            "inconsciente",
            "azul",
            "morado",
            "convulsiones",
            "sangrado mucho",
            "no para de sangrar",
            "muy grave",
            "empeora mucho",
        ]
        f = (feedback or "").lower()
        for ind in indicators:
            if ind in f:
                return {
                    "is_emergency": True,
                    "indicator": ind,
                    "action": "immediate_112_call",
                    "message": f"Situación de emergencia detectada: {ind}. Llama al {self.emergency_number} inmediatamente.",
                }

        return {
            "is_emergency": False,
            "indicator": None,
            "action": "continue_protocol",
            "message": None,
        }

    # ---------- helpers internos ----------
    def _get_required_warnings(self, protocol_type: str) -> Dict[str, List[str]]:
        """Advertencias requeridas según protocolo."""
        common = {
            "emergency_call": [str(self.emergency_number), "emergencias", "llamar"],
        }

        specific = {
            "rcp": {
                **common,
                "training": ["entrenamiento", "curso", "capacitación"],
                "professional": ["profesional", "médico", "sanitario"],
            },
            "atragantamiento": {
                **common,
                "consciousness": ["conciencia", "inconsciente", "desmaya"],
            },
            "hemorragias": {
                **common,
                "severe_bleeding": ["sangrado intenso", "no para", "abundante"],
            },
            "quemaduras": {
                **common,
                "severe_burns": ["grave", "extensa", "profunda"],
            },
            "anafilaxia": {
                **common,
                "immediate": ["inmediatamente", "urgente", "rápido"],
            },
        }

        return specific.get(protocol_type, common)

    def _get_suggested_additions(self, missing: List[str]) -> List[str]:
        """Genera sugerencias legibles para completar avisos faltantes."""
        suggestions = {
            "emergency_call": f"Recuerda llamar al {self.emergency_number} si la situación empeora o no mejora.",
            "training": "Es recomendable recibir entrenamiento en primeros auxilios.",
            "professional": "Esta guía no sustituye la atención médica profesional.",
            "consciousness": "Si la persona pierde la conciencia, llama al 112 inmediatamente.",
            "severe_bleeding": "Si el sangrado es intenso o no se controla, llama al 112.",
            "severe_burns": "Para quemaduras graves o extensas, busca atención médica inmediata.",
            "immediate": "En caso de anafilaxia, actúa inmediatamente y llama al 112.",
        }
        return [suggestions[k] for k in missing if k in suggestions]
