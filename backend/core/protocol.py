from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class TriageCondition(BaseModel):
    condition: str
    next_step: Optional[int] = None

class StepUI(BaseModel):
    timer: bool = False
    timer_duration: Optional[int] = None
    illustration: Optional[str] = None
    next_button: bool = True

class ProtocolStep(BaseModel):
    id: int
    action: str
    instruction: str
    voice_cue: str
    ui: StepUI
    next_conditions: Optional[List[TriageCondition]] = None
    next_step: Optional[int] = None
    loop_condition: Optional[str] = None
    exit_conditions: Optional[List[str]] = None

class TriageData(BaseModel):
    red_flags: List[str]
    immediate_action: str

class ExitCriteria(BaseModel):
    success: List[str]
    emergency: List[str]

class ProtocolMetadata(BaseModel):
    edad: str
    entorno: List[str]
    materiales: List[str]
    riesgo: str
    tiempo_estimado: str

class Protocol(BaseModel):
    id: str
    title: str
    version: str
    sources: List[str]
    metadata: ProtocolMetadata
    triage: TriageData
    steps: List[ProtocolStep]
    exit_criteria: ExitCriteria
    emergency_action: str

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
    ui: Dict[str, Any]
    voice_cues: List[str]
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
    results: List[SearchResult]

