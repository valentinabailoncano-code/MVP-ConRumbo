from typing import Dict, List, Optional
from src.models.protocol import TriageRequest, TriageResponse
from src.rag.search import RAGSearchEngine

class TriageEngine:
    def __init__(self, rag_engine: RAGSearchEngine):
        self.rag_engine = rag_engine
        
        # Criterios de alto riesgo que requieren llamada inmediata al 112
        self.high_risk_criteria = {
            "estado_conciencia": ["inconsciente", "no responde"],
            "respiracion": ["ausente", "anormal", "no respira"],
            "sangrado": ["intenso", "no controlable", "arterial"],
            "signos_shock": ["cianosis", "palidez extrema", "pulso débil"],
            "dolor_toracico": ["opresivo", "irradiado", "intenso"],
            "signos_ictus": ["parálisis facial", "debilidad brazo", "habla alterada"]
        }
        
        # Mapeo de intents a protocolos específicos
        self.intent_protocol_mapping = {
            "parada_cardiorespiratoria": "pa_rcp_adulto_v1",
            "atragantamiento": "pa_asfixia_adulto_v1",
            "hemorragia": "pa_hemorragias_v1",
            "quemadura": "pa_quemaduras_v1",
            "anafilaxia": "pa_anafilaxia_v1",
            "convulsion": "pa_convulsiones_v1",
            "ictus_fast": "pa_ictus_fast_v1",
            "dolor_toracico": "pa_dolor_toracico_v1"
        }
    
    def evaluate_triage(self, request: TriageRequest) -> TriageResponse:
        """Evalúa el triaje y determina el nivel de riesgo y protocolo a seguir."""
        
        # 1. Evaluar criterios de alto riesgo
        risk_level, recommendations = self._assess_risk(request)
        
        # 2. Determinar protocolo apropiado
        protocol_id = self._determine_protocol(request)
        
        # 3. Obtener acción inmediata del protocolo
        immediate_action = self._get_immediate_action(protocol_id, request)
        
        return TriageResponse(
            risk=risk_level,
            recommend=recommendations,
            next_flow=protocol_id,
            immediate_action=immediate_action
        )
    
    def _assess_risk(self, request: TriageRequest) -> tuple[str, List[str]]:
        """Evalúa el nivel de riesgo basado en los criterios de entrada."""
        recommendations = []
        
        # Verificar criterios de alto riesgo
        high_risk_flags = []
        
        # Estado de conciencia
        if request.estado_conciencia.lower() in self.high_risk_criteria["estado_conciencia"]:
            high_risk_flags.append("estado_conciencia")
        
        # Respiración
        if request.respiracion and request.respiracion.lower() in self.high_risk_criteria["respiracion"]:
            high_risk_flags.append("respiracion")
        
        # Sangrado
        if request.sangrado and request.sangrado.lower() in self.high_risk_criteria["sangrado"]:
            high_risk_flags.append("sangrado")
        
        # Determinar nivel de riesgo
        if high_risk_flags:
            risk_level = "alto"
            recommendations.append("llamar_112")
            
            # Recomendaciones específicas según el tipo de emergencia
            if "respiracion" in high_risk_flags or "estado_conciencia" in high_risk_flags:
                recommendations.append("iniciar_rcp_si_necesario")
            
            if "sangrado" in high_risk_flags:
                recommendations.append("control_hemorragia")
                
        elif self._has_moderate_risk_factors(request):
            risk_level = "moderado"
            recommendations.append("seguir_protocolo")
            recommendations.append("considerar_112_si_empeora")
        else:
            risk_level = "bajo"
            recommendations.append("seguir_protocolo")
        
        return risk_level, recommendations
    
    def _has_moderate_risk_factors(self, request: TriageRequest) -> bool:
        """Verifica si hay factores de riesgo moderado."""
        moderate_factors = [
            request.sangrado and request.sangrado.lower() in ["moderado", "visible"],
            request.lugar and request.lugar.lower() in ["via_publica", "lugar_aislado"],
            request.hay_ayuda and request.hay_ayuda.lower() == "no"
        ]
        
        return any(moderate_factors)
    
    def _determine_protocol(self, request: TriageRequest) -> str:
        """Determina el protocolo apropiado basado en el intent y la edad."""
        base_protocol = self.intent_protocol_mapping.get(request.intent)
        
        if not base_protocol:
            # Usar búsqueda RAG como fallback
            search_results = self.rag_engine.search(
                query=request.intent,
                context={"edad": request.edad},
                top_k=1
            )
            
            if search_results:
                return search_results[0].protocol_id
            else:
                return "pa_general_v1"  # Protocolo por defecto
        
        # Adaptar protocolo según la edad
        if request.edad.lower() in ["niño", "nino"]:
            base_protocol = base_protocol.replace("_adulto_", "_nino_")
        elif request.edad.lower() == "lactante":
            base_protocol = base_protocol.replace("_adulto_", "_lactante_")
        
        return base_protocol
    
    def _get_immediate_action(self, protocol_id: str, request: TriageRequest) -> Optional[str]:
        """Obtiene la acción inmediata del protocolo seleccionado."""
        protocol = self.rag_engine.get_protocol(protocol_id)
        
        if protocol and protocol.triage.immediate_action:
            return protocol.triage.immediate_action
        
        # Acciones por defecto según el tipo de emergencia
        default_actions = {
            "pa_rcp_adulto_v1": "Si no respira o no tiene pulso, iniciar RCP inmediatamente y llamar al 112",
            "pa_asfixia_adulto_v1": "Si no puede toser o hablar, realizar maniobra de Heimlich y llamar al 112",
            "pa_hemorragias_v1": "Aplicar presión directa sobre la herida y elevar la extremidad si es posible",
            "pa_quemaduras_v1": "Enfriar con agua fría durante 10-20 minutos, no aplicar cremas",
            "pa_anafilaxia_v1": "Usar autoinyector de epinefrina si está disponible y llamar al 112 inmediatamente",
            "pa_convulsiones_v1": "Proteger la cabeza, no introducir objetos en la boca, cronometrar la duración",
            "pa_ictus_fast_v1": "Evaluar FAST (cara, brazos, habla, tiempo) y llamar al 112 inmediatamente",
            "pa_dolor_toracico_v1": "Sentar al paciente, aflojar ropa ajustada y llamar al 112"
        }
        
        return default_actions.get(protocol_id, "Seguir las instrucciones del protocolo y llamar al 112 si es necesario")

