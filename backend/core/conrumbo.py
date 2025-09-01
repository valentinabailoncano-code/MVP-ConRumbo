# backend/core/conrumbo.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import yaml
import time

# --------- Protocol models (opcional) ---------
try:
    from .protocol import Protocol, load_all_protocols  # tu module pro
    HAVE_PROTOCOL_MODELS = True
except Exception:
    HAVE_PROTOCOL_MODELS = False
    Protocol = Any  # type: ignore

# --------- Motores (opcionales) ---------
try:
    from .triage import TriageEngine
except Exception:
    TriageEngine = None  # type: ignore

try:
    from .steps_player import StepsPlayer
except Exception:
    StepsPlayer = None  # type: ignore

try:
    from .safety import SafetyGuardrails
except Exception:
    SafetyGuardrails = None  # type: ignore

try:
    from .search import RAGSearchEngine
except Exception:
    RAGSearchEngine = None  # type: ignore

router = APIRouter()

# ---------- Modelos de petición ----------
class TriageRequest(BaseModel):
    intent: Optional[str] = None
    query: Optional[str] = None
    edad: Optional[str] = "adulto"
    estado_conciencia: Optional[str] = None
    respiracion: Optional[str] = None
    sangrado: Optional[str] = None
    lugar: Optional[str] = None
    hay_ayuda: Optional[bool] = None
    dispone_DEA: Optional[bool] = None
    context: Optional[Dict[str, Any]] = None

class NextStepRequest(BaseModel):
    protocol_id: str
    current_step: int
    user_response: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

# ---------- Carga de protocolos ----------
PROTOCOLS_DIR = Path(__file__).resolve().parents[1] / "rag" / "protocols"
PROTOCOLS: Dict[str, Any] = {}
_last_load_time = 0.0

def _simple_load_protocols() -> Dict[str, Dict[str, Any]]:
    protocols: Dict[str, Dict[str, Any]] = {}
    for yf in sorted(PROTOCOLS_DIR.glob("*.yaml")):
        try:
            data = yaml.safe_load(yf.read_text(encoding="utf-8"))
            pid = data.get("id") or yf.stem
            protocols[pid] = data
            print(f"[OK] Protocolo cargado (simple): {pid}")
        except Exception as e:
            print(f"[ERR] Cargando {yf.name}: {e}")
    return protocols

def load_protocols(force: bool = False) -> Dict[str, Any]:
    global PROTOCOLS, _last_load_time
    if force or not PROTOCOLS:
        if not PROTOCOLS_DIR.exists():
            print(f"[WARN] Carpeta de protocolos no encontrada: {PROTOCOLS_DIR}")
            PROTOCOLS = {}
            return PROTOCOLS
        if HAVE_PROTOCOL_MODELS:
            PROTOCOLS = load_all_protocols(PROTOCOLS_DIR)  # dict[str, Protocol]
            print(f"[INFO] Protocol models ON. {len(PROTOCOLS)} cargados.")
        else:
            PROTOCOLS = _simple_load_protocols()
            print(f"[INFO] Protocol models OFF. {len(PROTOCOLS)} cargados.")
        _last_load_time = time.time()
    return PROTOCOLS

# Carga inicial
load_protocols()

# ---------- Instancias opcionales ----------
rag_engine = RAGSearchEngine() if RAGSearchEngine else None
triage_engine = TriageEngine(rag_engine) if TriageEngine else None
steps_player = StepsPlayer(rag_engine) if StepsPlayer else None
safety_guardrails = SafetyGuardrails() if SafetyGuardrails else None

# ---------- Helpers ----------
def _get_steps_and_meta(proto: Any):
    """
    Devuelve (steps_normalizados, ui_top_level_dict, voice_cues_list)
    - Si hay modelos pydantic, convierte a dicts serializables.
    - Normaliza steps simples a objetos con 'instruction'.
    """
    if HAVE_PROTOCOL_MODELS and not isinstance(proto, dict):
        # pydantic Protocol
        steps = []
        for i, s in enumerate(proto.steps):
            steps.append({
                "id": getattr(s, "id", i),
                "instruction": getattr(s, "instruction", None) or getattr(s, "action", "") or "",
                "voice_cue": getattr(s, "voice_cue", None),
                "ui": (s.ui.model_dump() if getattr(s, "ui", None) else {}),
            })
        top_ui = proto.ui.model_dump() if getattr(proto, "ui", None) else {}
        voice_cues = list(getattr(proto, "voice_cues", []) or [])
        return steps, top_ui, voice_cues

    # dict plano
    steps_raw = proto.get("steps", [])
    top_ui = proto.get("ui", {}) or {}
    voice_cues = list(proto.get("voice_cues", []) or [])

    steps: List[Dict[str, Any]] = []
    for i, s in enumerate(steps_raw):
        if isinstance(s, str):
            steps.append({"id": i, "instruction": s, "ui": {}})
        elif isinstance(s, dict):
            s = {**s}
            if "id" not in s:
                s["id"] = i
            if "instruction" not in s:
                s["instruction"] = s.get("action", "") or ""
            if "ui" not in s:
                s["ui"] = {}
            steps.append(s)
    return steps, top_ui, voice_cues

# ---------- Endpoints ----------
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ConRumbo API",
        "version": "1.0.0",
        "protocols_loaded": len(PROTOCOLS),
        "protocol_models": HAVE_PROTOCOL_MODELS,
    }

@router.post("/triage")
async def submit_triage(req: TriageRequest):
    try:
        # Safety (si tienes guardarraíles)
        safety = {"allowed": True, "message": "Consulta permitida"}
        if safety_guardrails:
            safety = safety_guardrails.check(req.model_dump())

        # Usa tu motor si existe; si no, mapping básico
        if triage_engine:
            result = triage_engine.run(req.model_dump())
        else:
            mapping = {
                "rcp": "pa_rcp_adulto_v1",
                "parada_cardiorespiratoria": "pa_rcp_adulto_v1",
                "atragantamiento": "pa_asfixia_adulto_v1",
                "asfixia": "pa_asfixia_adulto_v1",
            }
            flow = None
            if req.intent and req.intent in mapping:
                flow = mapping[req.intent]
            elif req.query:
                q = req.query.lower()
                for k, v in mapping.items():
                    if k in q:
                        flow = v
                        break
            if not flow:
                flow = next(iter(PROTOCOLS.keys()), None)

            risk = "alto" if (req.intent == "rcp" or req.respiracion in {"anormal", "ausente"}) else "medio"
            result = {
                "protocol_id": flow,
                "confidence": 0.7 if flow else 0.0,
                "risk_level": risk,
                "immediate_action": "Llama al 112 y comienza RCP" if flow == "pa_rcp_adulto_v1" else None,
                "escalate_to_emergency": (risk == "alto"),
            }

        return {"success": True, "result": result, "safety_check": safety}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/next_step")
async def get_next_step(req: NextStepRequest):
    try:
        if req.protocol_id not in PROTOCOLS:
            raise HTTPException(status_code=404, detail="Protocolo no encontrado")

        proto = PROTOCOLS[req.protocol_id]
        steps, top_ui, voice_cues = _get_steps_and_meta(proto)
        total = len(steps)

        if req.current_step < 0 or req.current_step >= total:
            return {"success": True, "result": {
                "step": None,
                "step_number": total,
                "total_steps": total,
                "is_final": True,
                "message": "Protocolo completado",
            }}

        step = steps[req.current_step]
        say_text = step.get("instruction", "") or step.get("action", "")
        ui = {**(top_ui or {}), **(step.get("ui") or {})}
        vcu: List[str] = []
        if "voice_cue" in step and step["voice_cue"]:
            vcu.append(step["voice_cue"])
        if voice_cues:
            vcu.extend(voice_cues)

        return {"success": True, "result": {
            "step": say_text,
            "step_number": req.current_step + 1,
            "total_steps": total,
            "is_final": (req.current_step + 1) >= total,
            "ui": ui,
            "voice_cues": vcu,
        }}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/protocol/{protocol_id}")
async def get_protocol(protocol_id: str):
    if protocol_id not in PROTOCOLS:
        raise HTTPException(status_code=404, detail="Protocolo no encontrado")
    proto = PROTOCOLS[protocol_id]
    if HAVE_PROTOCOL_MODELS and not isinstance(proto, dict):
        return {"success": True, "protocol": proto.model_dump()}
    return {"success": True, "protocol": proto}

@router.get("/protocols")
async def list_protocols():
    items = []
    for pid, proto in PROTOCOLS.items():
        if HAVE_PROTOCOL_MODELS and not isinstance(proto, dict):
            title = proto.title
            category = getattr(proto, "category", "")
            priority = getattr(getattr(proto, "metadata", None), "riesgo", "") if getattr(proto, "metadata", None) else ""
            target = ""
        else:
            title = proto.get("title", "")
            category = proto.get("category", "")
            priority = proto.get("priority", "") or proto.get("metadata", {}).get("riesgo", "")
            target = proto.get("target_audience", "")
        items.append({
            "id": pid, "title": title, "category": category,
            "priority": priority, "target_audience": target
        })
    return {"success": True, "protocols": items}

@router.post("/search")
async def search_knowledge(req: SearchRequest):
    try:
        q = (req.query or "").lower().strip()
        results: List[Dict[str, Any]] = []
        if not q:
            return {"success": True, "results": results}

        for pid, proto in PROTOCOLS.items():
            # Título
            title = proto.title if HAVE_PROTOCOL_MODELS and not isinstance(proto, dict) else proto.get("title", "")
            haystack = (title or "").lower()

            # Texto de pasos
            steps, _, _ = _get_steps_and_meta(proto)
            for s in steps:
                txt = s.get("instruction") or s.get("action") or ""
                if txt:
                    haystack += " " + txt.lower()

            if q in haystack:
                results.append({"protocol_id": pid, "title": title, "relevance": 1.0})

        results.sort(key=lambda x: x["relevance"], reverse=True)
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/reset")
async def reset_session():
    return {"success": True, "message": "Sesión reiniciada"}

@router.get("/session/status")
async def get_session_status():
    return {"success": True, "session": {"active": True, "protocols_available": len(PROTOCOLS)}}

@router.post("/reload")
async def reload_protocols():
    load_protocols(force=True)
    return {"success": True, "reloaded": True, "protocols_loaded": len(PROTOCOLS)}
