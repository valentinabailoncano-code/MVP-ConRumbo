# Script de Demostración - ConRumbo MVP

**Duración total:** 10-15 minutos  
**Audiencia:** Stakeholders técnicos y no técnicos  
**Objetivo:** Demostrar funcionalidades clave del MVP

---

## Preparación Previa (2 minutos)

### Verificar Servicios
```bash
# Backend
curl http://localhost:8000/api/conrumbo/health
# Debe responder: {"status":"healthy","protocols_loaded":4}

# Frontend
curl -I http://localhost:5173
# Debe responder: HTTP/1.1 200 OK
```

### URLs de Acceso
- **Web App**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Mobile**: Expo QR code

### Dispositivos Necesarios
- Ordenador con navegador web
- Dispositivo móvil con Expo Go (opcional)
- Conexión a internet (para mostrar modo offline)

---

## Demo 1: Web App PWA - Protocolo RCP (5 minutos)

### Introducción (30 segundos)
> "ConRumbo es una aplicación de primeros auxilios que combina protocolos médicos validados con tecnología de voz e IA. Vamos a ver cómo funciona en una emergencia real."

### Paso 1: Acceso Inicial (30 segundos)
1. Abrir http://localhost:5173
2. **Mostrar**: Interfaz limpia y accesible
3. **Destacar**: Botón 112 prominente y siempre visible
4. **Explicar**: "En una emergencia, lo primero que ves es cómo llamar ayuda profesional"

### Paso 2: Activación por Voz (1 minuto)
1. Hacer clic en el botón azul del micrófono
2. **Mostrar**: Botón se pone rojo y parpadea
3. Decir claramente: **"RCP"**
4. **Resultado**: Se abre automáticamente el protocolo de RCP
5. **Explicar**: "El control de voz permite navegación manos libres, crucial cuando tienes las manos ocupadas"

### Paso 3: Navegación del Protocolo (2 minutos)
1. **Paso 1 - Verificación**: 
   - Leer instrucción: "Toque los hombros firmemente..."
   - **Mostrar**: Temporizador de 10 segundos
   - **Destacar**: Instrucciones claras y específicas

2. **Paso 2 - Llamar 112**:
   - **Mostrar**: Instrucción de llamada
   - **Destacar**: Duración de 30 segundos para la llamada
   - Hacer clic en "Siguiente"

3. **Paso 5 - Compresiones**:
   - **Mostrar**: Metrónomo visual aparece
   - **Destacar**: Sonido a 110 BPM
   - **Explicar**: "El metrónomo ayuda a mantener el ritmo correcto de compresiones"

### Paso 4: Características PWA (1 minuto)
1. **Modo Offline**:
   - Desconectar WiFi/datos
   - **Mostrar**: Aplicación sigue funcionando
   - **Explicar**: "Los protocolos críticos funcionan sin internet"

2. **Instalación**:
   - Mostrar opción "Instalar app" en navegador
   - **Explicar**: "Se puede instalar como app nativa"

---

## Demo 2: Prototipo Móvil - Reconocimiento por Cámara (3 minutos)

### Introducción (30 segundos)
> "El prototipo móvil añade reconocimiento por cámara para identificar lesiones y sugerir protocolos apropiados."

### Paso 1: Acceso Móvil (30 segundos)
1. Abrir Expo Go en dispositivo móvil
2. Escanear código QR
3. **Mostrar**: App se abre automáticamente
4. **Destacar**: Interfaz optimizada para móvil

### Paso 2: Reconocimiento por Cámara (1.5 minutos)
1. Tocar "📷 Reconocimiento por Cámara"
2. **Mostrar**: Vista de cámara en tiempo real
3. **Destacar**: Guías visuales de posicionamiento
4. Apuntar cámara hacia objeto (simular lesión)
5. Tocar "Analizar"
6. **Mostrar**: Proceso de análisis (2 segundos)
7. **Resultado**: Detección simulada (ej: "Hemorragia - 85% confianza")

### Paso 3: Protocolo Sugerido (30 segundos)
1. **Mostrar**: Navegación automática al protocolo
2. **Destacar**: Información de lesión detectada
3. **Mostrar**: Progreso visual del protocolo
4. **Explicar**: "La IA mapea lesiones a protocolos específicos"

### Paso 4: Interfaz Móvil (30 segundos)
1. **Mostrar**: Navegación optimizada para una mano
2. **Destacar**: Botón 112 siempre accesible
3. **Mostrar**: Pasos críticos destacados visualmente

---

## Demo 3: Backend y API (2 minutos)

### Introducción (30 segundos)
> "El backend inteligente proporciona los servicios de IA y gestión de protocolos."

### Paso 1: Documentación API (1 minuto)
1. Abrir http://localhost:8000/docs
2. **Mostrar**: Documentación Swagger automática
3. **Destacar**: Endpoints principales:
   - `/health` - Estado del sistema
   - `/protocols` - Lista de protocolos
   - `/triage` - Evaluación inteligente
4. **Ejecutar**: Health check en vivo
5. **Mostrar**: Respuesta JSON con 4 protocolos cargados

### Paso 2: Protocolos Médicos (30 segundos)
1. **Ejecutar**: GET `/protocols`
2. **Mostrar**: Lista de 4 protocolos implementados
3. **Destacar**: Metadatos médicos (categoría, prioridad, audiencia)
4. **Explicar**: "Protocolos basados en guías ERC 2021 y AHA 2020"

---

## Demo 4: Integración Completa (2 minutos)

### Flujo End-to-End (1.5 minutos)
1. **Web App**: Usuario dice "Atragantamiento"
2. **Backend**: Procesa comando y devuelve protocolo
3. **Frontend**: Muestra protocolo de Heimlich
4. **Navegación**: Paso a paso con temporizadores
5. **Móvil**: Mismo protocolo accesible desde app móvil

### Características de Seguridad (30 segundos)
1. **Mostrar**: Disclaimers médicos en toda la app
2. **Destacar**: Botón 112 siempre prominente
3. **Explicar**: "Guardarraíles de seguridad previenen mal uso"
4. **Mencionar**: "No proporciona diagnósticos, solo primeros auxilios"

---

## Preguntas y Respuestas (3 minutos)

### Preguntas Frecuentes Anticipadas

**P: ¿Es seguro usar sin formación médica?**
R: Está diseñado para ciudadanos, pero recomendamos formación básica. Siempre incluye instrucciones para llamar al 112.

**P: ¿Qué tan preciso es el reconocimiento por cámara?**
R: En el MVP es simulado para demostración. La versión real usaría modelos de computer vision entrenados con datos médicos.

**P: ¿Funciona en todas las emergencias?**
R: Cubre las 4 emergencias más comunes. El roadmap incluye más protocolos y situaciones.

**P: ¿Qué pasa si cometo un error?**
R: La Ley del Buen Samaritano protege a quien ayuda de buena fe. Es mejor actuar que no hacer nada.

**P: ¿Cuándo estará disponible para el público?**
R: Este es un MVP técnico. Necesita validación clínica y certificación médica antes del lanzamiento público.

---

## Cierre y Próximos Pasos (1 minuto)

### Resumen de Valor
> "ConRumbo demuestra cómo la tecnología puede democratizar el conocimiento médico crítico. Combina protocolos validados, IA y interfaces intuitivas para ayudar a ciudadanos en emergencias."

### Logros del MVP
- ✅ Web App PWA completamente funcional
- ✅ Prototipo móvil con reconocimiento simulado
- ✅ Backend inteligente con sistema RAG
- ✅ 4 protocolos médicos validados
- ✅ Documentación técnica y de usuario completa

### Próximos Pasos
1. **Validación clínica** con profesionales médicos
2. **IA real** para reconocimiento de lesiones
3. **Más protocolos** para cobertura completa
4. **Certificación médica** para uso público

### Contacto
- **Documentación**: Ver archivos README en cada componente
- **Código fuente**: Disponible en `/home/ubuntu/conrumbo/`
- **Soporte**: Contactar al equipo de desarrollo

---

## Notas para el Presentador

### Consejos de Presentación
- **Mantener ritmo**: No más de 15 minutos total
- **Enfocarse en valor**: Cómo ayuda en emergencias reales
- **Ser honesto**: Mencionar limitaciones y estado MVP
- **Interactivo**: Permitir preguntas durante la demo

### Backup Plans
- **Sin internet**: Demostrar modo offline
- **Problemas técnicos**: Usar screenshots preparados
- **Sin móvil**: Mostrar solo web app
- **API caída**: Explicar arquitectura con documentación

### Mensajes Clave
1. **Democratización**: Acceso a conocimiento médico crítico
2. **Tecnología al servicio**: IA, voz y móvil para emergencias
3. **Seguridad**: Guardarraíles y derivación a profesionales
4. **Escalabilidad**: Base sólida para desarrollo futuro

---

**¡Buena suerte con la demostración!**

