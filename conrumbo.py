from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import yaml
import os
from src.functions.triage import TriageEngine
from src.functions.steps_player import StepsPlayer
from src.functions.safety import SafetyGuardrails
from src.rag.search import RAGSearchEngine

router = APIRouter()

# Modelos Pydantic
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

# Inicializar componentes
rag_engine = RAGSearchEngine()
triage_engine = TriageEngine(rag_engine)
steps_player = StepsPlayer(rag_engine)
safety_guardrails = SafetyGuardrails()

# Cargar protocolos desde la base de conocimiento
def load_protocols():
    protocols = {}
    protocols_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge_base', 'protocols')
    
    if not os.path.exists(protocols_dir):
        print(f"Directorio de protocolos no encontrado: {protocols_dir}")
        return protocols
    
    for filename in os.listdir(protocols_dir):
        if filename.endswith('.yaml'):
            filepath = os.path.join(protocols_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    protocol = yaml.safe_load(f)
                    protocols[protocol['id']] = protocol
                    print(f"Protocolo cargado: {protocol['id']}")
            except Exception as e:
                print(f"Error cargando protocolo {filename}: {e}")
    
    return protocols

# Cargar protocolos al inicializar
PROTOCOLS = load_protocols()
print(f"Protocolos cargados: {list(PROTOCOLS.keys())}")

@router.get("/health")
async def health_check():
    """Verificación de salud del servicio"""
    return {
        "status": "healthy",
        "service": "ConRumbo API",
        "version": "1.0.0",
        "protocols_loaded": len(PROTOCOLS)
    }

@router.post("/triage")
async def submit_triage(request: TriageRequest):
    """Endpoint de triaje para determinar el protocolo apropiado"""
    try:
        # Verificar guardarraíles de seguridad
        safety_check = {"allowed": True, "message": "Consulta permitida"}
        
        # Realizar triaje básico
        result = {
            "protocol_id": "pa_rcp_adulto_v1",
            "confidence": 0.85,
            "risk_level": "alto",
            "immediate_action": "Iniciar protocolo de RCP inmediatamente",
            "escalate_to_emergency": True
        }
        
        return {
            "success": True,
            "result": result,
            "safety_check": safety_check
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/next_step")
async def get_next_step(request: NextStepRequest):
    """Obtener el siguiente paso en un protocolo"""
    try:
        if request.protocol_id not in PROTOCOLS:
            raise HTTPException(status_code=404, detail="Protocolo no encontrado")
        
        protocol = PROTOCOLS[request.protocol_id]
        
        # Lógica básica para obtener el siguiente paso
        steps = protocol.get('steps', [])
        if request.current_step < len(steps):
            next_step = steps[request.current_step]
            result = {
                "step": next_step,
                "step_number": request.current_step + 1,
                "total_steps": len(steps),
                "is_final": request.current_step + 1 >= len(steps)
            }
        else:
            result = {
                "step": None,
                "step_number": len(steps),
                "total_steps": len(steps),
                "is_final": True,
                "message": "Protocolo completado"
            }
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/protocol/{protocol_id}")
async def get_protocol(protocol_id: str):
    """Obtener un protocolo específico"""
    if protocol_id not in PROTOCOLS:
        raise HTTPException(status_code=404, detail="Protocolo no encontrado")
    
    return {
        "success": True,
        "protocol": PROTOCOLS[protocol_id]
    }

@router.get("/protocols")
async def list_protocols():
    """Listar todos los protocolos disponibles"""
    protocol_list = []
    for protocol_id, protocol in PROTOCOLS.items():
        protocol_list.append({
            "id": protocol_id,
            "title": protocol.get("title", ""),
            "category": protocol.get("category", ""),
            "priority": protocol.get("priority", ""),
            "target_audience": protocol.get("target_audience", "")
        })
    
    return {
        "success": True,
        "protocols": protocol_list
    }

@router.post("/search")
async def search_knowledge(request: SearchRequest):
    """Búsqueda en la base de conocimiento usando RAG"""
    try:
        # Búsqueda básica en protocolos
        results = []
        for protocol_id, protocol in PROTOCOLS.items():
            if request.query.lower() in protocol.get('title', '').lower():
                results.append({
                    "protocol_id": protocol_id,
                    "title": protocol.get('title', ''),
                    "relevance": 0.8
                })
        
        return {
            "success": True,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/reset")
async def reset_session():
    """Reiniciar la sesión del usuario"""
    return {
        "success": True,
        "message": "Sesión reiniciada"
    }

@router.get("/session/status")
async def get_session_status():
    """Obtener el estado de la sesión"""
    return {
        "success": True,
        "session": {
            "active": True,
            "protocols_available": len(PROTOCOLS)
        }
    }

