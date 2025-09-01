# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
import yaml

# --------- Carga de protocolos YAML ----------
PROTOCOLS_DIR = Path(__file__).resolve().parent / "rag" / "protocols"
def load_protocols():
    protocols = {}
    for yf in PROTOCOLS_DIR.glob("*.yaml"):
        with open(yf, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            pid = data.get("id") or yf.stem
            protocols[pid] = data
    return protocols

PROTOCOLS = load_protocols()

# --------- App FastAPI ----------
app = FastAPI(title="ConRumbo MVP API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class TriageIn(BaseModel):
    intent: str
    edad: Optional[str] = "adulto"
    estado_conciencia: Optional[str] = None
    respiracion: Optional[str] = None
    sangrado: Optional[str] = None

class TriageOut(BaseModel):
    risk: str
    recommend: List[str]
    next_flow: str

class NextStepIn(BaseModel):
    flow_id: str
    step_idx: int = 0
    user_feedback: Optional[str] = None

class NextStepOut(BaseModel):
    say: str
    step_idx: int
    remaining: int
    ui: Dict[str, Any] = {}

@app.get("/health")
def health():
    return {"status": "ok", "protocols": len(PROTOCOLS)}

@app.get("/api/protocols")
def list_protocols():
    return [{"id": p["id"], "title": p.get("title")} for p in PROTOCOLS.values()]

@app.post("/api/triage", response_model=TriageOut)
def triage(inp: TriageIn):
    mapping = {"atragantamiento": "pa_asfixia_adulto_v1", "rcp": "pa_rcp_adulto_v1"}
    flow = mapping.get(inp.intent)
    if not flow or flow not in PROTOCOLS:
        raise HTTPException(404, f"No flow for intent '{inp.intent}'")
    risk = "alto" if (inp.respiracion in {"anormal", "ausente"} or inp.intent == "rcp") else "medio"
    recommend = ["llamar_112"] if risk == "alto" else []
    return TriageOut(risk=risk, recommend=recommend, next_flow=flow)

@app.post("/api/next_step", response_model=NextStepOut)
def next_step(inp: NextStepIn):
    proto = PROTOCOLS.get(inp.flow_id)
    if not proto:
        raise HTTPException(404, "Flow not found")
    steps = proto.get("steps", [])
    if inp.step_idx < 0 or inp.step_idx >= len(steps):
        raise HTTPException(400, "Invalid step index")
    ui = proto.get("ui", {})
    remaining = max(0, len(steps) - (inp.step_idx + 1))
    return NextStepOut(say=steps[inp.step_idx], step_idx=inp.step_idx, remaining=remaining, ui=ui)
