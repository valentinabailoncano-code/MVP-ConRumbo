# backend/core/steps_player.py
from __future__ import annotations
from typing import Dict, List, Optional, Any

from .protocol import Protocol, NextStepRequest as FlowNextStepRequest, NextStepResponse as FlowNextStepResponse
from .search import RAGSearchEngine


class StepsPlayer:
    def __init__(self, rag_engine: RAGSearchEngine):
        self.rag_engine = rag_engine
        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # Sesiones activas por usuario

    def get_next_step(self, request: FlowNextStepRequest, session_id: str = "default") -> FlowNextStepResponse:
        """
        Obtiene el siguiente paso del protocolo.

        Acepta request con:
        - (flow_id, step_idx)   # formato antiguo
        - (protocol_id, current_step)  # formato nuevo
        """
        # --- Adaptación de nombres de campos ---
        flow_id = getattr(request, "flow_id", None) or getattr(request, "protocol_id", None)
        step_idx = getattr(request, "step_idx", None)
        if step_idx is None:
            step_idx = getattr(request, "current_step", 0)

        user_feedback: Optional[str] = getattr(request, "user_feedback", None)

        # --- Obtener protocolo ---
        protocol = self.rag_engine.get_protocol(flow_id) if flow_id else None
        if not protocol:
            return FlowNextStepResponse(
                say="Error: Protocolo no encontrado",
                ui={"error": True},
                voice_cues=["Error en el sistema"],
                safety_alert="Error del sistema. Llama al 112 si necesitas ayuda médica inmediata.",
                is_final=True,
            )

        # --- Inicializar o actualizar sesión ---
        sess = self.active_sessions.setdefault(
            session_id,
            {"protocol_id": flow_id, "current_step": 0, "step_history": [], "user_responses": []},
        )

        if user_feedback:
            sess["user_responses"].append({"step": step_idx, "feedback": user_feedback})

        # --- Determinar siguiente paso ---
        next_step_idx = self._determine_next_step(protocol, step_idx, user_feedback)

        if next_step_idx is None or next_step_idx >= len(protocol.steps or []):
            # Protocolo completado o fin por emergencia
            return self._handle_protocol_completion(protocol, sess)

        # --- Paso actual ---
        current_step = protocol.steps[next_step_idx]
        sess["current_step"] = next_step_idx
        sess["step_history"].append(next_step_idx)

        # --- Seguridad / alertas ---
        safety_alert = self._check_safety_criteria(protocol, current_step, user_feedback)

        # --- Construir respuesta ---
        say_text = (getattr(current_step, "instruction", None) or
                    getattr(current_step, "action", None) or
                    "")
        ui_payload = self._build_ui_response(current_step, protocol)

        voice = getattr(current_step, "voice_cue", None)
        voice_list: List[str] = [voice] if voice else []

        return FlowNextStepResponse(
            say=say_text,
            ui=ui_payload,
            voice_cues=voice_list,
            safety_alert=safety_alert,
            is_final=False,
        )

    # -------------------- helpers internos --------------------

    def _determine_next_step(
        self, protocol: Protocol, current_step_idx: int, user_feedback: Optional[str]
    ) -> Optional[int]:
        """Determina el siguiente paso basado en las condiciones del protocolo."""
        steps = protocol.steps or []

        if current_step_idx is None or current_step_idx < 0 or current_step_idx >= len(steps):
            return 0  # Comenzar desde el primer paso

        current_step = steps[current_step_idx]

        # Salida por emergencia en feedback
        if user_feedback and self._check_emergency_exit(user_feedback, protocol):
            return None  # Terminar protocolo por emergencia

        # Condiciones de transición (si el YAML rico las define)
        next_conditions = getattr(current_step, "next_conditions", None)
        if next_conditions and user_feedback:
            for condition in next_conditions:
                cond_expr = getattr(condition, "condition", "") or ""
                if self._evaluate_condition(cond_expr, user_feedback):
                    return getattr(condition, "next_step", None)

        # Condición de bucle
        loop_cond = getattr(current_step, "loop_condition", None)
        if loop_cond and user_feedback:
            if self._evaluate_condition(loop_cond, user_feedback):
                nxt = getattr(current_step, "next_step", None)
                if nxt is not None:
                    return nxt

        # Paso siguiente por defecto
        nxt = getattr(current_step, "next_step", None)
        return nxt if nxt is not None else current_step_idx + 1

    def _evaluate_condition(self, condition: str, user_feedback: str) -> bool:
        """Evalúa si una condición se cumple basada en el feedback del usuario."""
        condition_lower = (condition or "").lower()
        feedback_lower = (user_feedback or "").lower()

        condition_mappings = {
            "puede_toser": ["sí", "si", "puede", "tose"],
            "no_puede_toser": ["no", "no puede", "no tose"],
            "objeto_expulsado": ["salió", "expulsado", "fuera", "mejor"],
            "objeto_no_expulsado": ["no salió", "sigue", "no mejora"],
            "empeora_estado": ["peor", "empeora", "cianosis", "inconsciente"],
            "mejora": ["mejor", "mejora", "respira", "consciente"],
            "no_mejora": ["igual", "no mejora", "sigue igual"],
        }

        if condition_lower in condition_mappings:
            keywords = condition_mappings[condition_lower]
            return any(k in feedback_lower for k in keywords)

        return condition_lower and condition_lower in feedback_lower

    def _check_emergency_exit(self, user_feedback: str, protocol: Protocol) -> bool:
        """Verifica si el feedback indica una situación de emergencia."""
        emergency_keywords = [
            "inconsciente", "no respira", "cianosis", "azul", "morado",
            "convulsiones", "sangrado intenso", "shock", "colapso",
        ]
        feedback_lower = (user_feedback or "").lower()
        return any(k in feedback_lower for k in emergency_keywords)

    def _check_safety_criteria(self, protocol: Protocol, current_step: Any, user_feedback: Optional[str]) -> Optional[str]:
        """Verifica criterios de seguridad y genera alertas si es necesario."""
        # Red flags del protocolo (si existen)
        if user_feedback and getattr(protocol, "triage", None) and getattr(protocol.triage, "red_flags", None):
            feedback_lower = user_feedback.lower()
            for red_flag in protocol.triage.red_flags:
                rf = (red_flag or "").lower()
                if rf and all(word in feedback_lower for word in rf.split()):
                    return f"ALERTA: {red_flag}. {getattr(protocol, 'emergency_action', 'Llama al 112')}"

        # Alertas contextuales por texto del paso
        txt = f"{getattr(current_step, 'action', '')} {getattr(current_step, 'instruction', '')}".lower()
        if "rcp" in txt:
            return "Recuerda: Si estás solo/a, activa manos libres y llama al 112 antes de continuar."
        if "golpes" in txt or "compresiones" in txt:
            return "Importante: Si la persona pierde la conciencia, inicia RCP inmediatamente."

        return None

    def _build_ui_response(self, step: Any, protocol: Protocol) -> Dict[str, Any]:
        """Construye la respuesta de UI para el paso actual."""
        ui = getattr(step, "ui", None)
        ui_response: Dict[str, Any] = {
            "step_id": getattr(step, "id", None),
            "action": getattr(step, "action", None),
            "instruction": getattr(step, "instruction", None),
            "timer": getattr(ui, "timer", False) if ui else False,
            "next_button": getattr(ui, "next_button", True) if ui else True,
            "protocol_title": getattr(protocol, "title", ""),
            "emergency_button": {"text": "LLAMAR 112", "visible": True, "urgent": True},
        }

        if ui:
            if getattr(ui, "timer_duration", None) is not None:
                ui_response["timer_duration"] = ui.timer_duration
            if getattr(ui, "illustration", None):
                ui_response["illustration"] = ui.illustration
            if getattr(ui, "metronome_bpm", None) is not None:
                ui_response["metronome_bpm"] = ui.metronome_bpm

        return ui_response

    def _handle_protocol_completion(self, protocol: Protocol, session: Dict[str, Any]) -> FlowNextStepResponse:
        """Maneja la finalización del protocolo y limpia la sesión."""
        # Limpiar sesión
        sid_to_remove = None
        for sid, sess in self.active_sessions.items():
            if sess is session:
                sid_to_remove = sid
                break
        if sid_to_remove:
            del self.active_sessions[sid_to_remove]

        # Mensaje final
        completion_message = f"Protocolo {getattr(protocol, 'title', '')} completado. "
        if getattr(protocol, "exit_criteria", None) and getattr(protocol.exit_criteria, "success", None):
            success_list = [s for s in protocol.exit_criteria.success if s]
            if success_list:
                completion_message += f"Signos de éxito: {', '.join(success_list)}. "
        completion_message += "Si la situación no mejora o empeora, llama al 112 inmediatamente."

        return FlowNextStepResponse(
            say=completion_message,
            ui={
                "completed": True,
                "protocol_title": getattr(protocol, "title", ""),
                "emergency_button": {"text": "LLAMAR 112", "visible": True, "urgent": True},
            },
            voice_cues=[completion_message],
            safety_alert=getattr(protocol, "emergency_action", None),
            is_final=True,
        )

    # -------------------- gestión de sesión --------------------

    def reset_session(self, session_id: str = "default") -> None:
        """Reinicia una sesión activa."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    def get_session_status(self, session_id: str = "default") -> Optional[Dict[str, Any]]:
        """Obtiene el estado de una sesión activa."""
        return self.active_sessions.get(session_id)

