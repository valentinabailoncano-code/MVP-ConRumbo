# Diseño de Arquitectura - ConRumbo MVP

## Visión General
La aplicación ConRumbo está diseñada como un sistema distribuido con tres componentes principales:

1. **Backend (FastAPI)**: API REST que maneja la lógica de negocio, RAG y funciones de triaje (el triaje es la etapa médica donde se describe el problema del paciente)
2. **Frontend Web (React PWA)**: Aplicación web progresiva para la interfaz principal
3. **Prototipo Móvil (Expo/React Native)**: Aplicación móvil con capacidades de AR para reconocimiento por cámara

## Arquitectura del Backend

### Estructura de Directorios
```
backend/
├── app.py                # Punto de entrada FastAPI
├── config.py             # Configuración de la aplicación
├── requirements.txt      # Dependencias Python
├── models/
│   ├── __init__.py
│   ├── protocol.py       # Modelos de datos para protocolos
│   ├── triage.py         # Modelos para triaje
│   └── response.py       # Modelos de respuesta
├── rag/
│   ├── __init__.py
│   ├── ingest.py         # Procesamiento e indexación de protocolos
│   ├── search.py         # Motor de búsqueda semántica y exact-match
│   ├── embeddings.py     # Generación de embeddings
│   └── index/            # Índices FAISS y metadatos
├── functions/
│   ├── __init__.py
│   ├── triage.py         # Lógica de triaje y evaluación de riesgo
│   ├── steps_player.py   # Reproductor de pasos de protocolos
│   ├── voice.py          # Helpers para STT/TTS (opcional)
│   └── safety.py         # Guardarraíles de seguridad
├── protocols/
│   ├── rcp_adulto.yaml
│   ├── atragantamiento_adulto.yaml
│   ├── hemorragias.yaml
│   ├── quemaduras.yaml
│   ├── anafilaxia.yaml
│   ├── convulsiones.yaml
│   └── ictus_fast.yaml
└── tests/
    ├── test_triage.py
    ├── test_rag.py
    └── test_safety.py
```
##### FastAPI is a high-performance web framework for building HTTP-based service APIs in Python 3.8+. It uses Pydantic and type hints to validate, serialize and deserialize data. FastAPI also also automatically generates OpenAI documentation for APIs is builtwith it.

### APIs Principales

#### 1. Endpoint de Triaje
```
POST /api/triage
Content-Type: application/json

{
  "intent": "atragantamiento",
  "edad": "adulto",
  "estado_conciencia": "consciente",
  "respiracion": "anormal",
  "sangrado": "no",
  "lugar": "casa",
  "hay_ayuda": "no",
  "dispone_DEA": "no"
}

Response:
{
  "risk": "alto",
  "recommend": ["llamar_112"],
  "next_flow": "pa_asfixia_adulto_v1",
  "immediate_action": "Llamar 112 si no respira o pierde conciencia"
}
```

#### 2. Endpoint de Siguiente Paso
```
POST /api/next_step
Content-Type: application/json

{
  "flow_id": "pa_asfixia_adulto_v1",
  "step_idx": 2,
  "user_feedback": "no funciona"
}

Response:
{
  "say": "Alterna 5 golpes y 5 compresiones abdominales...",
  "ui": {
    "timer": false,
    "illustrations": ["back_blows.png", "abdominal_thrusts.png"],
    "next_button": true
  },
  "voice_cues": ["Voy contigo. ¿Puede toser? Responde sí o no."],
  "safety_alert": null
}
```

#### 3. Endpoint de Búsqueda RAG
```
POST /api/search
Content-Type: application/json

{
  "query": "se está ahogando",
  "context": {
    "edad": "adulto",
    "lugar": "casa"
  }
}

Response:
{
  "results": [
    {
      "protocol_id": "pa_asfixia_adulto_v1",
      "title": "Atragantamiento (adulto)",
      "relevance_score": 0.95,
      "snippet": "Si no puede toser: 5 golpes interescapulares firmes..."
    }
  ]
}
```

### Componentes del RAG (retrival-augmented generation)

#### 1. Indexación de Protocolos
- **Embeddings**: Utilizando modelos de OpenAI para generar embeddings semánticos
- **Metadatos**: Edad, entorno, riesgo, materiales necesarios
- **Índice FAISS**: Para búsqueda semántica eficiente
- **Exact-match**: Diccionario de intents para coincidencias exactas

#### 2. Motor de Búsqueda
- **Búsqueda híbrida**: Combinación de búsqueda semántica y exact-match
- **Re-ranking**: Priorización basada en metadatos y contexto
- **Filtrado**: Por edad, disponibilidad de materiales, etc.

### Guardarraíles de Seguridad

#### 1. Detección de Preguntas Diagnósticas
- Patrones de texto que indican solicitudes de diagnóstico
- Respuesta automática: "No puedo diagnosticar. Si tienes síntomas preocupantes, llama al 112"

#### 2. Escalación Automática
- Criterios de alto riesgo que activan llamada inmediata al 112 ( teniendo en cuenta que la app/web no sustitutye a un médico profesional)
- Mensajes de seguridad obligatorios en flujos críticos

## Arquitectura del Frontend Web

### Estructura de Directorios
```
web/
├── public/
│   ├── manifest.json    # Configuración PWA
│   ├── sw.js            # Service Worker
│   └── icons/           # Iconos de la aplicación
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button112.jsx
│   │   │   ├── VoiceButton.jsx
│   │   │   └── StepCard.jsx
│   │   ├── rcp/
│   │   │   ├── RCPMetronome.jsx
│   │   │   └── RCPTimer.jsx
│   │   └── ui/
│   │       ├── Layout.jsx
│   │       └── Navigation.jsx
│   ├── features/
│   │   ├── triage/
│   │   │   ├── TriageForm.jsx
│   │   │   └── TriageResults.jsx
│   │   ├── protocols/
│   │   │   ├── ProtocolPlayer.jsx
│   │   │   └── StepByStep.jsx
│   │   └── voice/
│   │       ├── SpeechRecognition.jsx
│   │       └── TextToSpeech.jsx
│   ├── services/
│   │   ├── api.js        # Cliente API
│   │   ├── speech.js     # Web Speech API
│   │   └── offline.js    # Gestión de contenido offline
│   ├── store/
│   │   ├── index.js      # Configuración Zustand
│   │   ├── triageStore.js
│   │   └── protocolStore.js
│   ├── utils/
│   │   ├── constants.js
│   │   └── helpers.js
│   └── App.jsx
├── package.json
└── vite.config.js
```

### Características PWA

#### 1. Service Worker
- Cache de protocolos críticos (RCP, atragantamiento)
- Estrategia cache-first para contenido estático
- Network-first para APIs con fallback a cache

#### 2. Manifest
- Configuración para instalación en dispositivo
- Iconos adaptativos para diferentes tamaños
- Modo standalone para experiencia de app nativa

#### 3. Capacidades Offline
- Protocolos críticos disponibles sin conexión
- Fallback textual si TTS/STT no están disponibles
- Indicadores de estado de conexión

### Gestión de Estado

#### 1. Zustand Stores
- **triageStore**: Estado del proceso de triaje
- **protocolStore**: Protocolo activo y progreso de pasos
- **voiceStore**: Estado de reconocimiento y síntesis de voz

#### 2. Persistencia
- LocalStorage para configuraciones de usuario
- IndexedDB para protocolos cacheados

### Integración de Voz

#### 1. Web Speech API
- **SpeechRecognition**: Para entrada de voz del usuario
- **SpeechSynthesis**: Para guía por voz
- Fallbacks para navegadores no compatibles

#### 2. Metrónomo RCP
- **WebAudio API**: Para sonido preciso de 100-120 BPM
- **Vibration API**: Para feedback háptico (móviles)
- Temporizador visual sincronizado

## Arquitectura del Prototipo Móvil

### Estructura de Directorios
```
mobile/
├── App.js
├── app.json             # Configuración Expo
├── package.json
├── src/
│   ├── components/
│   │   ├── ARCamera.jsx
│   │   ├── PoseDetector.jsx
│   │   └── LesionMarker.jsx
│   ├── screens/
│   │   ├── HomeScreen.jsx
│   │   ├── CameraScreen.jsx
│   │   └── ProtocolScreen.jsx
│   ├── services/
│   │   ├── arcore.js     # Integración ARCore (Android)
│   │   ├── arkit.js      # Integración ARKit (iOS)
│   │   └── mediapipe.js  # MediaPipe Pose
│   └── utils/
│       ├── permissions.js
│       └── privacy.js
├── ios/
│   └── native-modules/   # Módulos nativos iOS
└── android/
    └── native-modules/   # Módulos nativos Android
```

### Capacidades AR

#### 1. Detección de Persona
- **MediaPipe Pose**: 33 landmarks del cuerpo humano
- **ARCore/ARKit**: Seguimiento de esqueleto 3D
- Procesamiento en tiempo real on-device

#### 2. Marcador de Lesión
- Toque en pantalla para marcar ubicación de lesión
- Anclaje del marcador al esqueleto detectado
- Persistencia del marcador durante la sesión

#### 3. Overlays Educativos
- Flechas y zonas para guía visual
- Instrucciones contextuales basadas en el protocolo activo
- Adaptación a la pose detectada

### Privacidad y Seguridad
- Procesamiento completamente on-device
- No almacenamiento de frames de video
- Datos anónimos y efímeros
- Consentimiento explícito para uso de cámara

## Base de Datos de Protocolos

### Formato YAML
```yaml
id: pa_asfixia_adulto_v1
title: Atragantamiento (adulto)
version: "1.0"
sources: 
  - ERC_2021_FirstAid
  - WHO_CFar_2025
metadata:
  edad: adulto
  entorno: [casa, via_publica]
  materiales: []
  riesgo: alto
  tiempo_estimado: "2-5 minutos"
triage:
  red_flags:
    - "No puede hablar o respirar"
    - "Cianosis evidente"
    - "Pérdida de conciencia"
  immediate_action: "Llamar 112 si no respira o pierde conciencia"
steps:
  - id: 1
    action: "Evaluar capacidad de tos"
    instruction: "Pídale que tosa si puede."
    voice_cue: "¿Puede toser? Responde sí o no."
    ui:
      timer: false
      illustration: "cough_assessment.png"
    next_conditions:
      - condition: "puede_toser"
        next_step: 2
      - condition: "no_puede_toser"
        next_step: 3
  - id: 2
    action: "Fomentar tos"
    instruction: "Anime a toser fuertemente."
    voice_cue: "Siga tosiendo fuerte."
    ui:
      timer: false
    exit_conditions:
      - "objeto_expulsado"
      - "empeora_estado"
  - id: 3
    action: "Golpes interescapulares"
    instruction: "5 golpes interescapulares firmes."
    voice_cue: "Voy a guiarte. 5 golpes firmes entre los omóplatos."
    ui:
      timer: true
      timer_duration: 10
      illustration: "back_blows.png"
    next_step: 4
  - id: 4
    action: "Compresiones abdominales"
    instruction: "5 compresiones abdominales (maniobra de Heimlich)."
    voice_cue: "Ahora 5 compresiones en el abdomen, justo debajo del esternón."
    ui:
      timer: true
      timer_duration: 10
      illustration: "abdominal_thrusts.png"
    next_step: 3
    loop_condition: "objeto_no_expulsado"
exit_criteria:
  success:
    - "objeto_expulsado"
    - "respiracion_normal"
  emergency:
    - "perdida_conciencia"
    - "cianosis_severa"
    - "no_mejora_tras_ciclos"
emergency_action: "Iniciar RCP si pierde conciencia. Llamar 112 inmediatamente."
```

### Metadatos para RAG
- **Embeddings**: Generados a partir del título, instrucciones y voice_cues
- **Tags**: Extraídos de metadatos para filtrado
- **Intents**: Mapeo de frases comunes a protocolos específicos

## Integración y Flujo de Datos

### 1. Flujo de Triaje
```
Usuario → Frontend → API Triage → RAG Search → Protocolo Seleccionado → Frontend
```

### 2. Flujo de Protocolo
```
Frontend → API Next Step → Protocolo Engine → Respuesta con Instrucciones → Frontend → TTS
```

### 3. Flujo de Voz
```
Usuario (Voz) → STT → Frontend → API → RAG → Respuesta → TTS → Usuario
```

### 4. Flujo AR (Móvil)
```
Cámara → Pose Detection → Marcador de Lesión → Overlay Educativo → Protocolo Contextual
```

## Consideraciones de Rendimiento

### Backend
- **Caché**: Redis para respuestas frecuentes de RAG
- **Async**: FastAPI asíncrono para manejo concurrente
- **Optimización**: Índices FAISS optimizados para búsqueda rápida

### Frontend
- **Code Splitting**: Carga lazy de protocolos no críticos
- **Service Worker**: Cache inteligente para recursos estáticos
- **Optimización**: Debounce en búsquedas, throttling en eventos de voz

### Móvil
- **On-device**: Procesamiento local para privacidad y latencia
- **Optimización**: Reducción de resolución para AR en dispositivos de gama baja
- **Batería**: Gestión eficiente de recursos de cámara y procesamiento

## Seguridad y Cumplimiento

### GDPR
- Minimización de datos: Solo se procesan datos necesarios
- Consentimiento: Explícito para cámara y analítica
- Anonimización: Logs sin PII
- Derecho al olvido: Datos efímeros en sesiones AR

### Seguridad Médica
- Disclaimers obligatorios en flujos críticos
- Escalación automática a servicios de emergencia
- Validación de fuentes médicas en protocolos
- Auditoría de respuestas del sistema

Esta arquitectura proporciona una base sólida para el desarrollo del MVP de ConRumbo, asegurando escalabilidad, seguridad y una excelente experiencia de usuario tanto en web como en móvil.

