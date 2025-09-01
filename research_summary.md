
# Resumen de Investigación de Tecnologías

## Backend: FastAPI

**Ventajas:**
*   **Rendimiento:** Muy rápido, basado en Starlette para web y Pydantic para validación de datos.
*   **Desarrollo rápido:** Código moderno, tipado y asíncrono, lo que acelera el desarrollo.
*   **Documentación automática:** Genera automáticamente documentación interactiva (OpenAPI/Swagger UI, ReDoc).
*   **Validación de datos:** Integración con Pydantic para validación y serialización de datos.
*   **Soporte asíncrono:** Ideal para aplicaciones de E/S intensiva como APIs.
*   **Seguridad:** Soporte integrado para OAuth2 y otras características de seguridad.

**Casos de uso:**
*   Construcción de APIs RESTful de alto rendimiento.
*   Microservicios.
*   Aplicaciones web en tiempo real (con WebSockets).

**Alternativas consideradas:**
*   Flask: Más ligero y flexible, pero requiere más configuración para características como la validación de datos y la documentación automática.
*   Django: Framework más completo con ORM y admin, pero puede ser excesivo para una API pura y tiene una curva de aprendizaje más pronunciada para asincronía.

**Decisión:** FastAPI es la elección óptima para el backend debido a su rendimiento, facilidad de uso, documentación automática y soporte asíncrono, lo que se alinea perfectamente con los requisitos del proyecto (RAG, funciones de triaje, baja latencia).

## Frontend: React + PWA

**Ventajas:**
*   **Popularidad y ecosistema:** Gran comunidad, abundancia de librerías y herramientas.
*   **Componentes reutilizables:** Facilita el desarrollo modular y el mantenimiento.
*   **Rendimiento:** Virtual DOM para actualizaciones eficientes de la UI.
*   **PWA (Progressive Web App):** Permite que la aplicación web funcione como una aplicación nativa, con capacidades offline, notificaciones push y la posibilidad de ser instalada en el dispositivo.
*   **Experiencia de usuario:** Ofrece una experiencia similar a la de una aplicación nativa, con tiempos de carga rápidos y capacidad de respuesta.

**Casos de uso:**
*   Aplicaciones web interactivas y dinámicas.
*   Aplicaciones de una sola página (SPA).
*   Aplicaciones que requieren capacidades offline y una experiencia de usuario mejorada.

**Alternativas consideradas:**
*   Angular: Framework completo con una curva de aprendizaje más pronunciada.
*   Vue.js: Más ligero que Angular, pero con una comunidad más pequeña que React.
*   Streamlit: Ideal para prototipado rápido y visualización de datos, pero no tan adecuado para una PWA interactiva y compleja como la requerida.

**Decisión:** React + PWA es la elección ideal para el frontend. Permite construir una aplicación web robusta, con una excelente experiencia de usuario y las capacidades offline necesarias para los flujos críticos.

## Prototipo Móvil: Expo/React Native

**Ventajas:**
*   **Desarrollo multiplataforma:** Permite escribir código una vez y desplegarlo en iOS y Android.
*   **Rapidez de desarrollo:** Hot-reloading, componentes pre-construidos y un ecosistema rico aceleran el desarrollo.
*   **Expo:** Simplifica el flujo de trabajo de React Native, maneja la configuración de herramientas, compilación y despliegue. Ofrece APIs para acceder a características del dispositivo.
*   **Acceso a módulos nativos:** Permite integrar código nativo cuando sea necesario (como para ARCore/ARKit).

**Casos de uso:**
*   Aplicaciones móviles que requieren acceso a características nativas del dispositivo (cámara, sensores).
*   Prototipos rápidos y MVPs.
*   Aplicaciones que necesitan una experiencia de usuario nativa.

**Alternativas consideradas:**
*   Desarrollo nativo (Swift/Kotlin): Ofrece el máximo rendimiento y acceso a todas las APIs del dispositivo, pero requiere bases de código separadas para iOS y Android, lo que aumenta el tiempo y costo de desarrollo.

**Decisión:** Expo/React Native es la mejor opción para el prototipo móvil. Permite un desarrollo rápido y multiplataforma, y Expo facilita la integración de las capacidades de AR necesarias (ARCore/ARKit) a través de módulos nativos.

## Reconocimiento con Cámara: ARCore Depth API y MediaPipe Pose Landmarker (Android), ARKit Body Tracking (iOS)

**ARCore Depth API (Android):**
*   **Características:** Permite a la cámara del dispositivo entender el tamaño y la forma de los objetos reales en una escena, creando mapas de profundidad. Puede generar mapas de profundidad a partir de una sola cámara RGB (depth-from-motion).
*   **Casos de uso:** Mejora el realismo de la RA, oclusión de objetos virtuales, mediciones más precisas, reconstrucción 3D de objetos y escenas.
*   **Limitaciones:** No todos los dispositivos ARCore-compatibles soportan la Depth API debido a limitaciones de procesamiento. El procesamiento de profundidad puede ser intensivo en recursos.

**MediaPipe Pose Landmarker:**
*   **Características:** Detecta 33 puntos clave (landmarks) del cuerpo humano en imágenes o videos, incluyendo coordenadas 2D y 3D. Permite identificar ubicaciones clave del cuerpo como cabeza, torso, extremidades.
*   **Casos de uso:** Estimación de pose humana, seguimiento de movimiento, aplicaciones de fitness, realidad aumentada.
*   **Limitaciones:** La visibilidad de los landmarks puede no ser siempre precisa. La afinación del modelo no es tan sencilla como en otras soluciones de MediaPipe.

**ARKit Body Tracking (iOS):**
*   **Características:** Proporciona seguimiento del esqueleto 3D del cuerpo humano en tiempo real, permitiendo anclar contenido virtual a partes específicas del cuerpo.
*   **Casos de uso:** Experiencias de RA inmersivas, aplicaciones de fitness, efectos visuales.

**Decisión:** La combinación de ARCore Depth API y MediaPipe Pose Landmarker para Android, y ARKit Body Tracking para iOS, es la estrategia correcta. Esto permite aprovechar las capacidades específicas de cada plataforma para el reconocimiento de persona, esqueleto y marcador de lesión, con procesamiento on-device para garantizar la privacidad.

