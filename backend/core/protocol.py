# backend/core/protocol.py
from __future__ import annotations
from typing import List, Dict, Optional, Any, Sequence, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
import yaml
from pathlib import Path

# -----------------------
# Modelos base (Pydantic)
# -----------------------

class TriageCondition(BaseModel):
    condition: str
    next_step: Optional[int] = None
    model_config = ConfigDict(extra="ignore")

class StepUI(BaseModel):
    # UI a nivel de paso
    timer: bool = False
    timer_duration: Optional[int] = None
    illustration: Optional[str] = None
    next_button: bool = True
    # Extra útiles (p.ej. metrónomo para RCP)
    metronome_bpm: Optional[int] = None
    model_config = ConfigDict(extra="ignore")

class ProtocolStep(BaseModel):
    id: int
    action: Optional[str] = None
    instruction: Optional[str] = None
    voice_cue: Optional[str] = None
    ui: StepUI = Field(default_factory=StepUI)
    next_conditions: Optional[List[TriageCondition]] = None
    next_step: Optional[int] = None
    loop_condition: Optional[str] = None
    exit_conditions: Optional[List[str]] = None
    model_config = ConfigDict(extra="ignore")

class TriageData(BaseModel):
    red_flags: List[str] = []
    immediate_action: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class ExitCriteria(BaseModel):
    success: List[str] = []
    emergency: List[str] = []
    model_config = ConfigDict(extra="ignore")

class ProtocolMetadata(BaseModel):
    edad: Optional[str] = "adulto"
    entorno: List[str] = []
    materiales: List[str] = []
    riesgo: Optional[str] = "medio"
    tiempo_estimado: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class Protocol(BaseModel):
    id: str
    title: str
    version: Optional[str] = "v1"
    sources: List[str] = []
    metadata: ProtocolMetadata = Field(default_factory=ProtocolMetadata)
    triage: Optional[TriageData] = None

    # Acepta pasos simples (strings) o ricos (objetos)
    steps: List[ProtocolStep]

    # Criterios de salida (opcional)
    exit_criteria: Optional[ExitCriteria] = None

    # Acción de emergencia general (p.ej. "Llama al 112")
    emergency_action: Optional[str] = None

    # Campos opcionales top-level para ayudas de voz/UI
    voice_cues: Optional[List[str]] = None
    ui: Optional[StepUI] = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("steps", mode="before")
    @classmethod
    def coerce_steps(cls, v: Any) -> Any:
        """
        Convierte:
          - ['Frase 1', 'Frase 2'] -> [{'id':0,'instruction':'Frase 1'}, ...]
          - [{'instruction':'...'}] sin 'id' -> asigna ids secuenciales.
        """
        if isinstance(v, list) and all(isinstance(x, str) for x in v):
            return [{"id": i, "instruction": s} for i, s in enumerate(v)]
        if isinstance(v, list) and all(isinstance(x, dict) for x in v):
            out = []
            for i, d in enumerate(v):
                if "id" not in d:
                    d = {**d, "id": i}
                out.append(d)
            return out
        return v

# -----------------------
# Modelos API (opcionales)
# -----------------------

class TriageRequest(BaseModel):
    intent: str
    edad: str
    estado_conciencia: str
    respiracion: Optional[str] = None
    sangrado: Optional[str] = None
    lugar: Optional[str] = None
    hay_ayuda: Optional[str] = None
    dispone_DEA: Optional[str] = None

class TriageResponse(BaseModel):
    risk: str
    recommend: List[str]
    next_flow: str
    immediate_action: Optional[str] = None

class NextStepRequest(BaseModel):
    flow_id: str
    step_idx: int
    user_feedback: Optional[str] = None

class NextStepResponse(BaseModel):
    say: str
    ui: Dict[str, Any] = Field(default_factory=dict)
    voice_cues: List[str] = Field(default_factory=list)
    safety_alert: Optional[str] = None
    is_final: bool = False

class SearchRequest(BaseModel):
    query: str
    context: Optional[Dict[str, str]] = None

class SearchResult(BaseModel):
    protocol_id: str
    title: str
    relevance_score: float
    snippet: str

class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(default_factory=list)

# -----------------------
# Helpers de carga YAML
# -----------------------

def protocol_from_yaml_text(text: str) -> Protocol:
    data = yaml.safe_load(text)
    return Protocol.model_validate(data)

def protocol_from_yaml_file(path: Path) -> Protocol:
    return protocol_from_yaml_text(path.read_text(encoding="utf-8"))

def load_all_protocols(dirpath: Path) -> Dict[str, Protocol]:
    dirpath = Path(dirpath)
    out: Dict[str, Protocol] = {}
    if not dirpath.exists():
        return out
    for yf in sorted(dirpath.glob("*.yaml")):
        try:
            proto = protocol_from_yaml_file(yf)
            out[proto.id] = proto
        except Exception as e:
            print(f"[protocol] Error en {yf.name}: {e}")
    return out
