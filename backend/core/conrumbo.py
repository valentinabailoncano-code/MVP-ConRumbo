# backend/core/conrumbo.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from pathlib import Path
import yaml

# 👇 Importa los módulos del paquete 'core' (importes relativos correctos)
from .triage import TriageEngine
from .steps_player import StepsPlayer
from .safety import SafetyGuardrails
from .search import RAGSearchEngine

router = APIRouter()

# ---------- Modelos ----------
class TriageRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class NextStepRequest(BaseModel):
    protocol_id: str
    current_step: int
    user_response: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

# ---------- Inicialización ----------
rag_engine = RAGSearchEngine()
triage_engine = TriageEngine(rag_engine)
steps_player = StepsPlayer(rag_engine)
safety_guardrails = SafetyGuardrails()

def load_protocols() -> Dict[str, Dict[str, Any]]:
    """Carga YAML desde backend/rag/protocols"""
    protocols: Dict[str, Dict[str, Any]] = {}
    # conrumbo.py está en backend/core -> subimos a backend y entramos a rag/protocols
    protocols_dir = Path(__file__).resolve().parents[1] / "rag" / "protocols"
    if not protocols_dir.exists():
        print(f"[WARN] Carpeta de protocolos no encontrada: {protocols_dir}")
        return protocols

    for yf in sorted(protocols_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(yf.read_text(encoding="utf-8"))
            pid = data.get("id") or yf.stem
            protocols[pid] = data
            print(f"[OK] Protocolo cargado: {pid}")
        except Exception as e:
            print(f"[ERR] Error cargando {yf.name}: {e}")
    return protocols

PROTOCOLS = load_protocols()
print(f"[INFO] Protocolos cargados: {list(PROTOCOLS.keys())}")

# ---------- Endpoints ----------
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ConRumbo API",
        "version": "1.0.0",
        "protocols_loaded": len(PROTOCOLS),
    }

@router.post("/triage")
async def submit_triage(request: TriageRequest):
    try:
        # Guardarraíles (stub)
        safety_check = {"allowed": True, "message": "Consulta permitida"}

        # Triaje simplificado (sustituye por triage_engine cuando lo tengas listo)
        result = {
            "protocol_id": "pa_rcp_adulto_v1",
            "confidence": 0.85,
            "risk_level": "alto",
            "immediate_action": "Inicia RCP ahora",
            "escalate_to_emergency": True,
        }
        return {"success": True, "result": result, "safety_check": safety_check}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/next_step")
async def get_next_step(request: NextStepRequest):
    try:
        if request.protocol_id not in PROTOCOLS:
            raise HTTPException(status_code=404, detail="Protocolo no encontrado")

        steps: List[str] = PROTOCOLS[request.protocol_id].get("steps", [])
        if request.current_step < len(steps):
            next_step = steps[request.current_step]
            result = {
                "step": next_step,
                "step_number": request.current_step + 1,
                "total_steps": len(steps),
                "is_final": (request.current_step + 1) >= len(steps),
            }
        else:
            result = {
                "step": None,
                "step_number": len(steps),
                "total_steps": len(steps),
                "is_final": True,
                "message": "Protocolo completado",
            }
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/protocol/{protocol_id}")
async def get_protocol(protocol_id: str):
    if protocol_id not in PROTOCOLS:
        raise HTTPException(status_code=404, detail="Protocolo no encontrado")
    return {"success": True, "protocol": PROTOCOLS[protocol_id]}

@router.get("/protocols")
async def list_protocols():
    items = []
    for pid, proto in PROTOCOLS.items():
        items.append({
            "id": pid,
            "title": proto.get("title", ""),
            "category": proto.get("category", ""),
            "priority": proto.get("priority", ""),
            "target_audience": proto.get("target_audience", "")
        })
    return {"success": True, "protocols": items}

@router.post("/search")
async def search_knowledge(request: SearchRequest):
    try:
        results = []
        for pid, proto in PROTOCOLS.items():
            if request.query.lower() in proto.get("title", "").lower():
                results.append({"protocol_id": pid, "title": proto.get("title", ""), "relevance": 0.8})
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/reset")
async def reset_session():
    return {"success": True, "message": "Sesión reiniciada"}

@router.get("/session/status")
async def get_session_status():
    return {"success": True, "session": {"active": True, "protocols_available": len(PROTOCOLS)}}
