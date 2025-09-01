# backend/core/search.py
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import numpy as np
import yaml

# FAISS opcional (fallback a NumPy si no está disponible)
try:
    import faiss  # type: ignore
    HAVE_FAISS = True
except Exception:
    faiss = None  # type: ignore
    HAVE_FAISS = False

from .embeddings import EmbeddingGenerator
from .protocol import Protocol, SearchResult, load_all_protocols


class RAGSearchEngine:
    def __init__(self, protocols_dir: Optional[str] = None):
        # backend/core/search.py -> subir a backend/ y entrar a rag/protocols
        self.protocols_dir = Path(protocols_dir) if protocols_dir else Path(__file__).resolve().parents[1] / "rag" / "protocols"
        self.embedding_generator = EmbeddingGenerator()

        # Datos
        self.protocols: Dict[str, Protocol] = {}
        self.protocol_ids: List[str] = []

        # Índices
        self.index = None                    # FAISS
        self._embeddings: Optional[np.ndarray] = None  # Fallback NumPy (embeddings normalizados)

        # Intents
        self.exact_match_intents: Dict[str, List[str]] = {}

        # Inicialización
        self._load_protocols()
        self._build_index()
        self._build_intent_mapping()

    # -------------------------
    # Carga de protocolos
    # -------------------------
    def _load_protocols(self) -> None:
        """Carga todos los protocolos (Pydantic Protocol) desde YAML."""
        if not self.protocols_dir.exists():
            print(f"[RAG] Directorio de protocolos no encontrado: {self.protocols_dir}")
            self.protocols = {}
            return

        self.protocols = load_all_protocols(self.protocols_dir)  # Dict[str, Protocol]
        print(f"[RAG] Protocolos cargados: {len(self.protocols)}")

    # -------------------------
    # Construcción de índice
    # -------------------------
    def _text_from_protocol(self, p: Protocol) -> str:
        """Concatena campos útiles del protocolo para embedding."""
        parts: List[str] = [p.title or ""]

        # steps: pueden tener .instruction y/o .voice_cue
        for s in (p.steps or []):
            instr = getattr(s, "instruction", None) or getattr(s, "action", None) or ""
            if instr:
                parts.append(instr)
            vcue = getattr(s, "voice_cue", None) or ""
            if vcue:
                parts.append(vcue)

        # triage
        if p.triage:
            parts.extend([t for t in (p.triage.red_flags or []) if t])
            if p.triage.immediate_action:
                parts.append(p.triage.immediate_action)

        # voice_cues top-level
        vcl = getattr(p, "voice_cues", None) or []
        parts.extend([v for v in vcl if v])

        return " ".join(parts)

    def _build_index(self) -> None:
        """Construye el índice de búsqueda (FAISS o fallback NumPy)."""
        if not self.protocols:
            print("[RAG] No hay protocolos cargados para indexar")
            return

        texts: List[str] = []
        self.protocol_ids = []
        for pid, proto in self.protocols.items():
            texts.append(self._text_from_protocol(proto))
            self.protocol_ids.append(pid)

        # Embeddings
        embeds = self.embedding_generator.generate_embeddings_batch(texts)
        if not embeds:
            print("[RAG] Error generando embeddings")
            return

        emb = np.asarray(embeds, dtype=np.float32)
        # Normalizar L2 para usar producto punto como coseno
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        emb = emb / norms

        if HAVE_FAISS:
            dim = emb.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(emb)
            self._embeddings = None
            print(f"[RAG] Índice FAISS construido con {emb.shape[0]} protocolos (dim={dim})")
        else:
            self._embeddings = emb
            self.index = None
            print(f"[RAG] FAISS no disponible. Usando fallback NumPy con {emb.shape[0]} protocolos.")

    def _build_intent_mapping(self) -> None:
        """Mapeo de intents exactos a protocolos."""
        self.exact_match_intents = {
            "rcp": ["pa_rcp_adulto_v1", "pa_rcp_nino_v1", "pa_rcp_lactante_v1"],
            "parada cardiorespiratoria": ["pa_rcp_adulto_v1", "pa_rcp_nino_v1"],
            "no respira": ["pa_rcp_adulto_v1", "pa_rcp_nino_v1"],
            "atragantamiento": ["pa_asfixia_adulto_v1", "pa_asfixia_nino_v1"],
            "se está ahogando": ["pa_asfixia_adulto_v1", "pa_asfixia_nino_v1"],
            "asfixia": ["pa_asfixia_adulto_v1", "pa_asfixia_nino_v1"],
            "hemorragia": ["pa_hemorragias_v1"],
            "sangrado": ["pa_hemorragias_v1"],
            "herida": ["pa_hemorragias_v1"],
            "quemadura": ["pa_quemaduras_v1"],
            "quemado": ["pa_quemaduras_v1"],
            "anafilaxia": ["pa_anafilaxia_v1"],
            "alergia severa": ["pa_anafilaxia_v1"],
            "convulsiones": ["pa_convulsiones_v1"],
            "convulsión": ["pa_convulsiones_v1"],
            "ictus": ["pa_ictus_fast_v1"],
            "derrame cerebral": ["pa_ictus_fast_v1"],
            "dolor torácico": ["pa_dolor_toracico_v1"],
            "dolor en el pecho": ["pa_dolor_toracico_v1"],
        }

    # -------------------------
    # Búsqueda pública
    # -------------------------
    def search(self, query: str, context: Optional[Dict[str, str]] = None, top_k: int = 3) -> List[SearchResult]:
        """Búsqueda híbrida: exact-match + semántica."""
        results: List[SearchResult] = []

        # 1) Exact-match por intents
        query_lower = (query or "").lower()
        exact_matches: List[str] = []
        for intent, pids in self.exact_match_intents.items():
            if intent in query_lower:
                exact_matches.extend(pids)

        # Filtrar por edad si viene en contexto
        if context and "edad" in context and exact_matches:
            edad = context["edad"]
            exact_matches = [pid for pid in exact_matches if self._matches_age(pid, edad)]

        # Añadir exactos con score alto
        for pid in exact_matches[:top_k]:
            proto = self.protocols.get(pid)
            if proto:
                results.append(SearchResult(
                    protocol_id=pid,
                    title=proto.title,
                    relevance_score=1.0,
                    snippet=self._generate_snippet(proto, query)
                ))

        # 2) Semántica si faltan resultados
        remaining = top_k - len(results)
        if remaining > 0:
            sem = self._semantic_search(query, remaining)
            exist = {r.protocol_id for r in results}
            for r in sem:
                if r.protocol_id not in exist:
                    results.append(r)

        return results[:top_k]

    def _semantic_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Búsqueda semántica con FAISS o fallback NumPy."""
        if top_k <= 0:
            return []
        if self.index is None and self._embeddings is None:
            return []

        q_emb = self.embedding_generator.generate_embedding(query)
        if not q_emb:
            return []

        q = np.asarray(q_emb, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0.0:
            return []
        q = q / q_norm

        if HAVE_FAISS and self.index is not None:
            q_vec = q.reshape(1, -1).astype(np.float32)
            scores, indices = self.index.search(q_vec, top_k)
            idxs = indices[0]
            scs = scores[0]
        else:
            # Fallback: producto punto con todos los embeddings normalizados
            emb = self._embeddings  # (N, D)
            sims = emb @ q.reshape(-1, 1)  # (N,1)
            scs = sims.ravel()
            idxs = np.argsort(-scs)[:top_k]

        results: List[SearchResult] = []
        for score, idx in zip(scs[:top_k], idxs[:top_k]):
            if 0 <= int(idx) < len(self.protocol_ids):
                pid = self.protocol_ids[int(idx)]
                proto = self.protocols.get(pid)
                if proto:
                    results.append(SearchResult(
                        protocol_id=pid,
                        title=proto.title,
                        relevance_score=float(score),
                        snippet=self._generate_snippet(proto, query)
                    ))
        return results

    # -------------------------
    # Utilidades
    # -------------------------
    def _matches_age(self, protocol_id: str, edad: str) -> bool:
        """Verifica si un protocolo coincide con la edad especificada."""
        proto = self.protocols.get(protocol_id)
        if not proto or not proto.metadata or not proto.metadata.edad:
            return True
        protocol_edad = (proto.metadata.edad or "").lower()
        edad_lower = (edad or "").lower()

        if edad_lower in {"adulto", "adult"}:
            return "adulto" in protocol_edad
        if edad_lower in {"niño", "nino", "child"}:
            return ("niño" in protocol_edad) or ("nino" in protocol_edad)
        if edad_lower in {"lactante", "bebé", "bebe", "infant"}:
            return "lactante" in protocol_edad
        return True

    def _generate_snippet(self, protocol: Protocol, query: str) -> str:
        """Snippet simple y útil."""
        if protocol.triage and protocol.triage.immediate_action:
            return protocol.triage.immediate_action
        if protocol.steps:
            first = protocol.steps[0]
            return getattr(first, "instruction", None) or getattr(first, "action", None) or protocol.title
        return protocol.title

    def get_protocol(self, protocol_id: str) -> Optional[Protocol]:
        return self.protocols.get(protocol_id)
