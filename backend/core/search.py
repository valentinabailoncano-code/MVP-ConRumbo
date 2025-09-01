import os
import json
import yaml
from typing import List, Dict, Optional, Tuple
import faiss
import numpy as np
from src.rag.embeddings import EmbeddingGenerator
from src.models.protocol import Protocol, SearchResult

class RAGSearchEngine:
    def __init__(self, protocols_dir: str = "src/protocols"):
        self.protocols_dir = protocols_dir
        self.embedding_generator = EmbeddingGenerator()
        self.protocols: Dict[str, Protocol] = {}
        self.index = None
        self.protocol_ids = []
        self.exact_match_intents = {}
        
        # Cargar protocolos y construir índice
        self._load_protocols()
        self._build_index()
        self._build_intent_mapping()
    
    def _load_protocols(self):
        """Carga todos los protocolos desde archivos YAML."""
        if not os.path.exists(self.protocols_dir):
            print(f"Directorio de protocolos no encontrado: {self.protocols_dir}")
            return
        
        for filename in os.listdir(self.protocols_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                filepath = os.path.join(self.protocols_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        protocol_data = yaml.safe_load(file)
                        protocol = Protocol(**protocol_data)
                        self.protocols[protocol.id] = protocol
                        print(f"Protocolo cargado: {protocol.title}")
                except Exception as e:
                    print(f"Error cargando protocolo {filename}: {e}")
    
    def _build_index(self):
        """Construye el índice FAISS con embeddings de los protocolos."""
        if not self.protocols:
            print("No hay protocolos cargados para indexar")
            return
        
        # Preparar textos para embeddings
        texts = []
        protocol_ids = []
        
        for protocol_id, protocol in self.protocols.items():
            # Combinar título, instrucciones y voice_cues para crear texto indexable
            text_parts = [protocol.title]
            
            for step in protocol.steps:
                text_parts.extend([step.instruction, step.voice_cue])
            
            # Agregar red flags del triaje
            text_parts.extend(protocol.triage.red_flags)
            text_parts.append(protocol.triage.immediate_action)
            
            combined_text = " ".join(text_parts)
            texts.append(combined_text)
            protocol_ids.append(protocol_id)
        
        # Generar embeddings
        embeddings = self.embedding_generator.generate_embeddings_batch(texts)
        
        if not embeddings:
            print("Error generando embeddings")
            return
        
        # Crear índice FAISS
        dimension = len(embeddings[0])
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product para similitud coseno
        
        # Normalizar embeddings para usar inner product como similitud coseno
        embeddings_array = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_array)
        
        self.index.add(embeddings_array)
        self.protocol_ids = protocol_ids
        
        print(f"Índice FAISS construido con {len(embeddings)} protocolos")
    
    def _build_intent_mapping(self):
        """Construye mapeo de intents exactos a protocolos."""
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
            "dolor en el pecho": ["pa_dolor_toracico_v1"]
        }
    
    def search(self, query: str, context: Optional[Dict[str, str]] = None, top_k: int = 3) -> List[SearchResult]:
        """Realiza búsqueda híbrida (exact-match + semántica)."""
        results = []
        
        # 1. Intentar exact-match primero
        query_lower = query.lower()
        exact_matches = []
        
        for intent, protocol_ids in self.exact_match_intents.items():
            if intent in query_lower:
                exact_matches.extend(protocol_ids)
        
        # Filtrar por contexto si está disponible
        if context and "edad" in context:
            edad = context["edad"]
            exact_matches = [pid for pid in exact_matches if self._matches_age(pid, edad)]
        
        # Agregar resultados exact-match con alta relevancia
        for protocol_id in exact_matches[:top_k]:
            if protocol_id in self.protocols:
                protocol = self.protocols[protocol_id]
                results.append(SearchResult(
                    protocol_id=protocol_id,
                    title=protocol.title,
                    relevance_score=1.0,
                    snippet=protocol.triage.immediate_action
                ))
        
        # 2. Si no hay exact-matches suficientes, usar búsqueda semántica
        if len(results) < top_k and self.index is not None:
            semantic_results = self._semantic_search(query, top_k - len(results))
            
            # Evitar duplicados
            existing_ids = {r.protocol_id for r in results}
            for result in semantic_results:
                if result.protocol_id not in existing_ids:
                    results.append(result)
        
        return results[:top_k]
    
    def _semantic_search(self, query: str, top_k: int) -> List[SearchResult]:
        """Realiza búsqueda semántica usando FAISS."""
        if self.index is None:
            return []
        
        # Generar embedding de la consulta
        query_embedding = self.embedding_generator.generate_embedding(query)
        if not query_embedding:
            return []
        
        # Normalizar para similitud coseno
        query_vector = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vector)
        
        # Buscar en el índice
        scores, indices = self.index.search(query_vector, top_k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.protocol_ids):
                protocol_id = self.protocol_ids[idx]
                protocol = self.protocols[protocol_id]
                
                # Generar snippet relevante
                snippet = self._generate_snippet(protocol, query)
                
                results.append(SearchResult(
                    protocol_id=protocol_id,
                    title=protocol.title,
                    relevance_score=float(score),
                    snippet=snippet
                ))
        
        return results
    
    def _matches_age(self, protocol_id: str, edad: str) -> bool:
        """Verifica si un protocolo coincide con la edad especificada."""
        if protocol_id not in self.protocols:
            return False
        
        protocol = self.protocols[protocol_id]
        protocol_edad = protocol.metadata.edad.lower()
        edad_lower = edad.lower()
        
        # Mapeo de edades
        if edad_lower in ["adulto", "adult"]:
            return "adulto" in protocol_edad
        elif edad_lower in ["niño", "nino", "child"]:
            return "niño" in protocol_edad or "nino" in protocol_edad
        elif edad_lower in ["lactante", "bebé", "bebe", "infant"]:
            return "lactante" in protocol_edad
        
        return True  # Si no se especifica, incluir todos
    
    def _generate_snippet(self, protocol: Protocol, query: str) -> str:
        """Genera un snippet relevante del protocolo basado en la consulta."""
        # Por simplicidad, usar la acción inmediata del triaje
        if protocol.triage.immediate_action:
            return protocol.triage.immediate_action
        
        # Fallback al primer paso
        if protocol.steps:
            return protocol.steps[0].instruction
        
        return protocol.title
    
    def get_protocol(self, protocol_id: str) -> Optional[Protocol]:
        """Obtiene un protocolo por su ID."""
        return self.protocols.get(protocol_id)

