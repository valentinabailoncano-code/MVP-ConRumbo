# backend/core/embeddings.py
from __future__ import annotations
import os, hashlib
from typing import List, Sequence, Optional
import numpy as np

try:
    from openai import OpenAI
    HAVE_OPENAI = True
except Exception:
    OpenAI = None  # type: ignore
    HAVE_OPENAI = False

DEFAULT_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")  # 1536 dims en OpenAI
LOCAL_DIM = int(os.getenv("EMBED_LOCAL_DIM", "384"))  # dimensión fallback local


class EmbeddingGenerator:
    """
    Generador de embeddings con fallback:
    - Si hay OPENAI_API_KEY (y SDK disponible) -> usa OpenAI.
    - Si no hay clave -> usa un embedding local determinista (hash + normal).
    """

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.client = None
        self.mode = "local"  # "openai" | "local"

        # Intentar modo OpenAI si hay SDK y key
        key = api_key or os.getenv("OPENAI_API_KEY")
        if HAVE_OPENAI and key:
            kwargs = {"api_key": key}
            if base_url or os.getenv("OPENAI_API_BASE"):
                kwargs["base_url"] = base_url or os.getenv("OPENAI_API_BASE")
            try:
                self.client = OpenAI(**kwargs)  # type: ignore
                self.mode = "openai"
                print("[embeddings] Modo OpenAI activado.")
            except Exception as e:
                print(f"[embeddings] No se pudo inicializar OpenAI ({e}). Usando modo LOCAL.")
                self.client = None
                self.mode = "local"
        else:
            print("[embeddings] OPENAI_API_KEY ausente o SDK no disponible. Usando modo LOCAL.")

    @staticmethod
    def _clean_text(text: str) -> str:
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        return text.replace("\n", " ").strip()

    # ---------- Fallback local (determinista) ----------
    def _local_embed(self, text: str) -> List[float]:
        seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()[:8]
        seed = int.from_bytes(seed_bytes, "little")
        rng = np.random.default_rng(seed)
        v = rng.normal(size=LOCAL_DIM).astype(np.float32)
        n = np.linalg.norm(v)
        if n == 0.0:
            return [0.0] * LOCAL_DIM
        return list((v / n).astype(np.float32))

    def _local_batch(self, texts: Sequence[str]) -> List[List[float]]:
        return [self._local_embed(self._clean_text(t)) for t in texts]

    # ---------- API pública ----------
    def generate_embedding(self, text: str) -> List[float]:
        t = self._clean_text(text)
        if self.mode == "openai" and self.client:
            try:
                resp = self.client.embeddings.create(model=self.model, input=t)
                return list(resp.data[0].embedding)
            except Exception as e:
                print(f"[embeddings] Error OpenAI, usando local: {e}")
        return self._local_embed(t)

    def generate_embeddings_batch(self, texts: Sequence[str], chunk_size: int = 128) -> List[List[float]]:
        if self.mode == "openai" and self.client:
            try:
                out: List[List[float]] = []
                buf: List[str] = []
                for x in texts:
                    buf.append(self._clean_text(x))
                    if len(buf) >= chunk_size:
                        resp = self.client.embeddings.create(model=self.model, input=buf)
                        out.extend([list(d.embedding) for d in resp.data])
                        buf = []
                if buf:
                    resp = self.client.embeddings.create(model=self.model, input=buf)
                    out.extend([list(d.embedding) for d in resp.data])
                return out
            except Exception as e:
                print(f"[embeddings] Error batch OpenAI, usando local: {e}")
        return self._local_batch(texts)

    @staticmethod
    def cosine_similarity(e1: Sequence[float], e2: Sequence[float]) -> float:
        if not e1 or not e2:
            return 0.0
        v1 = np.asarray(e1, dtype=np.float32)
        v2 = np.asarray(e2, dtype=np.float32)
        n1 = np.linalg.norm(v1); n2 = np.linalg.norm(v2)
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        return float(np.dot(v1, v2) / (n1 * n2))


