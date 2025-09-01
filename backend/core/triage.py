# backend/core/triage.py
from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any

from .protocol import TriageRequest, TriageResponse
from .search import RAGSearchEngine


class TriageEngine:
    def __init__(self, rag_engine: RAGSearchEngine):
        self.rag_engine = rag_engine

        # Criterios de alto riesgo que requieren 112 inmediato
        self.high_risk_criteria: Dict[str, List[str]] = {
            "estado_conciencia": ["inconsciente", "no responde"],
            "respiracion": ["ausente", "anormal", "no respira"],
            "sangrado": ["intenso", "no controlable", "arterial"],
            "signos_shock": ["cianosis", "palidez extrema", "pulso débil"],
            "dolor_toracico": ["opresivo", "irradiado", "intenso"],
            "signos_ictus": ["parálisis facial", "debilidad brazo", "habla alterada"],
        }

        # Mapeo de intents a protocolos
        self.intent_protocol_mapping: Dict[str, str] = {
            "parada_cardiorespiratoria": "pa_rcp_adulto_v1",
            "rcp": "pa_rcp_adulto_v1",
            "atragantamiento": "pa_asfixia_adulto_v1",
            "asfixia": "pa_asfixia_adulto_v1",
            "hemorragia": "pa_hemorragias_v1",
            "quemadura": "pa_quemaduras_v1",
            "anafilaxia": "pa_anafilaxia_v1",
            "convulsion": "pa_convulsiones_v1",
            "convulsiones": "pa_convulsiones_v1",
            "ictus_fast": "pa_ictus_fast_v1",
            "ictus": "pa_ictus_fast_v1",
            "dolor_toracico": "pa_dolor_toracico_v1",
        }

    # ---------- API de alto nivel para conrumbo.py ----------
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Puente para conrumbo.py: recibe un dict (p.ej. req.model_dump()),
        construye TriageRequest y devuelve un resultado tipo:
        {
          "protocol_id": str, "confidence": float, "risk_level": str,
          "immediate_action": Optional[str], "escalate_to_emergency": bool
        }
        """
        # Normaliza campos y defaults seguros
        intent = (payload.get("intent") or payload.get("query") or "").strip().lower()
        edad = (payload.get("edad") or "adulto").strip().lower()
        estado_conciencia = (payload.get("estado_conciencia") or "desconocido").strip().lower()
        respiracion = (payload.get("respiracion") or None)
        respiracion = respiracion.strip().lower() if isinstance(respiracion, str) else respiracion
        sangrado = (payload.get("sangrado") or None)
        sangrado = sangrado.strip().lower() if isinstance(sangrado, str) else sangrado
        lugar = (payload.get("lugar") or None)
        lugar = lugar.strip().lower() if isinstance(lugar, str) else lugar
        hay_ayuda = payload.get("hay_ayuda")
        if isinstance(hay_ayuda, str):
            hay_ayuda = hay_ayuda.strip().lower()
        dispone_dea = payload.get("dispone_DEA")
        if isinstance(dispone_dea, str):
            dispone_dea = dispone_dea.strip().lower()

        req = TriageRequest(
            intent=intent or "desconocido",
            edad=edad or "adulto",
            estado_conciencia=estado_conciencia or "desconocido",
            respiracion=respiracion,
            sangrado=sangrado,
            lugar=lugar,
            hay_ayuda=str(hay_ayuda) if isinstance(hay_ayuda, bool) else hay_ayuda,
            dispone_DEA=str(dispone_dea) if isinstance(dispone_dea, bool) else dispone_dea,
        )

        triage = self.evaluate_triage(req)

        # Confianza heurística
        confidence = 0.9 if intent in self.intent_protocol_mapping else 0.7
        if triage.next_flow in (None, "", "pa_general_v1"):
            confidence = 0.5

        return {
            "protocol_id": triage.next_flow,
            "confidence": confidence,
            "risk_level": triage.risk,
            "immediate_action": triage.immediate_action,
            "escalate_to_emergency": (triage.risk == "alto"),
        }

    # ---------- Lógica principal ----------
    def evaluate_triage(self, request: TriageRequest) -> TriageResponse:
        """Evalúa el triaje y determina el nivel de riesgo y protocolo a seguir."""
        risk_level, recommendations = self._assess_risk(request)
        protocol_id = self._determine_protocol(request)
        immediate_action = self._get_immediate_action(protocol_id, request)

        return TriageResponse(
            risk=risk_level,
            recommend=recommendations,
            next_flow=protocol_id,
            immediate_action=immediate_action,
        )

    # ---------- Helpers internos ----------
    def _assess_risk(self, request: TriageRequest) -> Tuple[str, List[str]]:
        """Evalúa nivel de riesgo basado en criterios de entrada."""
        recommendations: List[str] = []
        high_risk_flags: List[str] = []

        # Estado de conciencia
        est = (request.estado_conciencia or "").lower()
        if est in self.high_risk_criteria["estado_conciencia"]:
            high_risk_flags.append("estado_conciencia")

        # Respiración
        if request.respiracion:
            resp = (request.respiracion or "").lower()
            if resp in self.high_risk_criteria["respiracion"]:
                high_risk_flags.append("respiracion")

        # Sangrado
        if request.sangrado:
            sang = (request.sangrado or "").lower()
            if sang in self.high_risk_criteria["sangrado"]:
                high_risk_flags.append("sangrado")

        # Nivel de riesgo y recomendaciones
        if high_risk_flags:
            risk_level = "alto"
            recommendations.append("llamar_112")
            if "respiracion" in high_risk_flags or "estado_conciencia" in high_risk_flags:
                recommendations.append("iniciar_rcp_si_necesario")
            if "sangrado" in high_risk_flags:
                recommendations.append("control_hemorragia")
        elif self._has_moderate_risk_factors(request):
            risk_level = "moderado"
            recommendations += ["seguir_protocolo", "considerar_112_si_empeora"]
        else:
            risk_level = "bajo"
            recommendations.append("seguir_protocolo")

        return risk_level, recommendations

    def _has_moderate_risk_factors(self, request: TriageRequest) -> bool:
        """Verifica factores de riesgo moderado."""
        sangrado_moderado = (request.sangrado or "").lower() in {"moderado", "visible"}
        lugar_riesgoso = (request.lugar or "").lower() in {"via_publica", "lugar_aislado"}
        hay_ayuda_no = (request.hay_ayuda or "").lower() == "no"
        return any([sangrado_moderado, lugar_riesgoso, hay_ayuda_no])

    def _determine_protocol(self, request: TriageRequest) -> str:
        """Determina el protocolo apropiado por intent/edad; si no, usa RAG como fallback."""
        intent = (request.intent or "").lower().strip()
        base_protocol = self.intent_protocol_mapping.get(intent)

        if not base_protocol:
            # Fallback: búsqueda RAG (usa intent como query)
            results = self.rag_engine.search(query=intent, context={"edad": request.edad}, top_k=1)
            if results:
                return results[0].protocol_id
            # Último recurso
            return "pa_general_v1"

        # Adaptar por edad
        edad = (request.edad or "").lower()
        if "adulto" in base_protocol:
            if edad in {"niño", "nino"}:
                base_protocol = base_protocol.replace("_adulto_", "_nino_")
            elif edad == "lactante":
                base_protocol = base_protocol.replace("_adulto_", "_lactante_")

        return base_protocol

    def _get_immediate_action(self, protocol_id: str, request: TriageRequest) -> Optional[str]:
        """Obtiene acción inmediata del protocolo (o default)."""
        protocol = self.rag_engine.get_protocol(protocol_id)
        if protocol and getattr(protocol, "triage", None) and getattr(protocol.triage, "immediate_action", None):
            return protocol.triage.immediate_action

        defaults = {
            "pa_rcp_adulto_v1": "Si no respira o no tiene pulso, iniciar RCP inmediatamente y llamar al 112",
            "pa_asfixia_adulto_v1": "Si no puede toser o hablar, realizar maniobra de Heimlich y llamar al 112",
            "pa_hemorragias_v1": "Aplicar presión directa sobre la herida y elevar la extremidad si es posible",
            "pa_quemaduras_v1": "Enfriar con agua fría durante 10-20 minutos, no aplicar cremas",
            "pa_anafilaxia_v1": "Usar autoinyector de epinefrina si está disponible y llamar al 112 inmediatamente",
            "pa_convulsiones_v1": "Proteger la cabeza, no introducir objetos en la boca, cronometrar la duración",
            "pa_ictus_fast_v1": "Evaluar FAST (cara, brazos, habla, tiempo) y llamar al 112 inmediatamente",
            "pa_dolor_toracico_v1": "Sentar al paciente, aflojar ropa ajustada y llamar al 112",
        }
        return defaults.get(protocol_id, "Seguir las instrucciones del protocolo y llamar al 112 si es necesario")
