from typing import Dict, List, Optional, Any
from src.models.protocol import NextStepRequest, NextStepResponse, Protocol
from src.rag.search import RAGSearchEngine

class StepsPlayer:
    def __init__(self, rag_engine: RAGSearchEngine):
        self.rag_engine = rag_engine
        self.active_sessions: Dict[str, Dict] = {}  # Sesiones activas por usuario
    
    def get_next_step(self, request: NextStepRequest, session_id: str = "default") -> NextStepResponse:
        """Obtiene el siguiente paso del protocolo."""
        
        # Obtener protocolo
        protocol = self.rag_engine.get_protocol(request.flow_id)
        if not protocol:
            return NextStepResponse(
                say="Error: Protocolo no encontrado",
                ui={"error": True},
                voice_cues=["Error en el sistema"],
                safety_alert="Error del sistema. Llama al 112 si necesitas ayuda médica inmediata.",
                is_final=True
            )
        
        # Inicializar o actualizar sesión
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "protocol_id": request.flow_id,
                "current_step": 0,
                "step_history": [],
                "user_responses": []
            }
        
        session = self.active_sessions[session_id]
        
        # Actualizar historial con feedback del usuario
        if request.user_feedback:
            session["user_responses"].append({
                "step": request.step_idx,
                "feedback": request.user_feedback
            })
        
        # Determinar siguiente paso
        next_step_idx = self._determine_next_step(protocol, request.step_idx, request.user_feedback)
        
        if next_step_idx is None or next_step_idx >= len(protocol.steps):
            # Protocolo completado o error
            return self._handle_protocol_completion(protocol, session)
        
        # Obtener paso actual
        current_step = protocol.steps[next_step_idx]
        session["current_step"] = next_step_idx
        session["step_history"].append(next_step_idx)
        
        # Verificar criterios de seguridad
        safety_alert = self._check_safety_criteria(protocol, current_step, request.user_feedback)
        
        # Construir respuesta
        response = NextStepResponse(
            say=current_step.instruction,
            ui=self._build_ui_response(current_step, protocol),
            voice_cues=[current_step.voice_cue],
            safety_alert=safety_alert,
            is_final=False
        )
        
        return response
    
    def _determine_next_step(self, protocol: Protocol, current_step_idx: int, user_feedback: Optional[str]) -> Optional[int]:
        """Determina el siguiente paso basado en las condiciones del protocolo."""
        
        if current_step_idx < 0 or current_step_idx >= len(protocol.steps):
            return 0  # Comenzar desde el primer paso
        
        current_step = protocol.steps[current_step_idx]
        
        # Verificar condiciones de salida de emergencia
        if user_feedback and self._check_emergency_exit(user_feedback, protocol):
            return None  # Terminar protocolo por emergencia
        
        # Verificar condiciones de siguiente paso
        if current_step.next_conditions and user_feedback:
            for condition in current_step.next_conditions:
                if self._evaluate_condition(condition.condition, user_feedback):
                    return condition.next_step
        
        # Verificar condición de bucle
        if current_step.loop_condition and user_feedback:
            if self._evaluate_condition(current_step.loop_condition, user_feedback):
                # Continuar en bucle (alternar entre pasos)
                if current_step.next_step is not None:
                    return current_step.next_step
        
        # Paso siguiente por defecto
        if current_step.next_step is not None:
            return current_step.next_step
        else:
            return current_step_idx + 1
    
    def _evaluate_condition(self, condition: str, user_feedback: str) -> bool:
        """Evalúa si una condición se cumple basada en el feedback del usuario."""
        condition_lower = condition.lower()
        feedback_lower = user_feedback.lower()
        
        # Mapeo de condiciones comunes
        condition_mappings = {
            "puede_toser": ["sí", "si", "puede", "tose"],
            "no_puede_toser": ["no", "no puede", "no tose"],
            "objeto_expulsado": ["salió", "expulsado", "fuera", "mejor"],
            "objeto_no_expulsado": ["no salió", "sigue", "no mejora"],
            "empeora_estado": ["peor", "empeora", "cianosis", "inconsciente"],
            "mejora": ["mejor", "mejora", "respira", "consciente"],
            "no_mejora": ["igual", "no mejora", "sigue igual"]
        }
        
        if condition_lower in condition_mappings:
            keywords = condition_mappings[condition_lower]
            return any(keyword in feedback_lower for keyword in keywords)
        
        # Evaluación directa si no hay mapeo específico
        return condition_lower in feedback_lower
    
    def _check_emergency_exit(self, user_feedback: str, protocol: Protocol) -> bool:
        """Verifica si el feedback indica una situación de emergencia."""
        emergency_keywords = [
            "inconsciente", "no respira", "cianosis", "azul", "morado",
            "convulsiones", "sangrado intenso", "shock", "colapso"
        ]
        
        feedback_lower = user_feedback.lower()
        return any(keyword in feedback_lower for keyword in emergency_keywords)
    
    def _check_safety_criteria(self, protocol: Protocol, current_step, user_feedback: Optional[str]) -> Optional[str]:
        """Verifica criterios de seguridad y genera alertas si es necesario."""
        
        # Verificar red flags del protocolo
        if user_feedback:
            feedback_lower = user_feedback.lower()
            for red_flag in protocol.triage.red_flags:
                if any(word in feedback_lower for word in red_flag.lower().split()):
                    return f"ALERTA: {red_flag}. {protocol.emergency_action}"
        
        # Alertas específicas por tipo de paso
        if "rcp" in current_step.action.lower():
            return "Recuerda: Si estás solo/a, activa manos libres y llama al 112 antes de continuar."
        
        if "golpes" in current_step.action.lower() or "compresiones" in current_step.action.lower():
            return "Importante: Si la persona pierde la conciencia, inicia RCP inmediatamente."
        
        return None
    
    def _build_ui_response(self, step, protocol: Protocol) -> Dict[str, Any]:
        """Construye la respuesta de UI para el paso actual."""
        ui_response = {
            "step_id": step.id,
            "action": step.action,
            "timer": step.ui.timer,
            "next_button": step.ui.next_button,
            "protocol_title": protocol.title
        }
        
        if step.ui.timer_duration:
            ui_response["timer_duration"] = step.ui.timer_duration
        
        if step.ui.illustration:
            ui_response["illustration"] = step.ui.illustration
        
        # Agregar botón de emergencia siempre visible
        ui_response["emergency_button"] = {
            "text": "LLAMAR 112",
            "visible": True,
            "urgent": True
        }
        
        return ui_response
    
    def _handle_protocol_completion(self, protocol: Protocol, session: Dict) -> NextStepResponse:
        """Maneja la finalización del protocolo."""
        
        # Limpiar sesión
        session_id = None
        for sid, sess in self.active_sessions.items():
            if sess == session:
                session_id = sid
                break
        
        if session_id:
            del self.active_sessions[session_id]
        
        # Mensaje de finalización
        completion_message = f"Protocolo {protocol.title} completado. "
        
        # Verificar criterios de éxito
        if protocol.exit_criteria.success:
            completion_message += f"Signos de éxito: {', '.join(protocol.exit_criteria.success)}. "
        
        completion_message += "Si la situación no mejora o empeora, llama al 112 inmediatamente."
        
        return NextStepResponse(
            say=completion_message,
            ui={
                "completed": True,
                "protocol_title": protocol.title,
                "emergency_button": {
                    "text": "LLAMAR 112",
                    "visible": True,
                    "urgent": True
                }
            },
            voice_cues=[completion_message],
            safety_alert=protocol.emergency_action,
            is_final=True
        )
    
    def reset_session(self, session_id: str = "default"):
        """Reinicia una sesión activa."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def get_session_status(self, session_id: str = "default") -> Optional[Dict]:
        """Obtiene el estado de una sesión activa."""
        return self.active_sessions.get(session_id)

