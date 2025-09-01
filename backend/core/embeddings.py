# backend/core/embeddings.py
from __future__ import annotations
import os
from typing import List, Sequence
import numpy as np
from openai import OpenAI

DEFAULT_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")  # 1536 dims

class EmbeddingGenerator:
    """
    Pequeño wrapper para generar embeddings y calcular similitudes.
    - Usa variables de entorno: OPENAI_API_KEY (obligatoria) y OPENAI_API_BASE (opcional).
    - Maneja lote (batch) y normaliza errores.
    """

    def __init__(self, model: str | None = None, api_key: str | None = None, base_url: str | None = None):
        self.model = model or DEFAULT_MODEL

        # El SDK ya lee OPENAI_API_KEY/OPENAI_API_BASE de env si no se pasan.
        kwargs = {}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url

        self.client = OpenAI(**kwargs)

    @staticmethod
    def _clean_text(text: str) -> str:
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        # OpenAI recomienda quitar saltos de línea redundantes para embeddings
        return text.replace("\n", " ").strip()

    def generate_embedding(self, text: str) -> List[float]:
        """Genera un embedding (list[float]) para un texto."""
        try:
            txt = self._clean_text(text)
            resp = self.client.embeddings.create(model=self.model, input=txt)
            return list(resp.data[0].embedding)
        except Exception as e:
            print(f"[embeddings] Error generando embedding: {e}")
            return []

    def generate_embeddings_batch(self, texts: Sequence[str], chunk_size: int = 128) -> List[List[float]]:
        """
        Genera embeddings para una lista de textos.
        Hace chunking por si hay listas muy largas.
        """
        all_embeds: List[List[float]] = []
        try:
            buf: List[str] = []
            for t in texts:
                buf.append(self._clean_text(t))
                if len(buf) >= chunk_size:
                    resp = self.client.embeddings.create(model=self.model, input=buf)
                    all_embeds.extend([list(d.embedding) for d in resp.data])
                    buf = []
            if buf:
                resp = self.client.embeddings.create(model=self.model, input=buf)
                all_embeds.extend([list(d.embedding) for d in resp.data])
            return all_embeds
        except Exception as e:
            print(f"[embeddings] Error en lote: {e}")
            return all_embeds  # devuelve lo que haya podido generar

    @staticmethod
    def cosine_similarity(embedding1: Sequence[float], embedding2: Sequence[float]) -> float:
        """Similitud coseno entre dos embeddings."""
        if not embedding1 or not embedding2:
            return 0.0
        v1 = np.asarray(embedding1, dtype=float)
        v2 = np.asarray(embedding2, dtype=float)
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        return float(np.dot(v1, v2) / (n1 * n2))

