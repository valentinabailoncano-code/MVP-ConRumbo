# Documentación Técnica del Prototipo Móvil - ConRumbo

**Versión:** 1.0.0  
**Fecha:** 31 de Agosto, 2024

---

## 1. Introducción

El prototipo móvil de ConRumbo es una aplicación nativa desarrollada con React Native y Expo que demuestra las capacidades avanzadas de reconocimiento por cámara y navegación optimizada para emergencias. Esta versión MVP incluye simulación de IA para reconocimiento de lesiones y protocolos interactivos adaptados para dispositivos móviles.

### Características Principales

- **Reconocimiento por Cámara:** Simulación de detección de lesiones con IA.
- **Navegación Nativa:** Interfaz optimizada para uso con una mano.
- **Protocolos Interactivos:** Guías paso a paso con progreso visual.
- **Acceso de Emergencia:** Botón 112 siempre accesible.
- **Offline Ready:** Funcionalidad básica sin conexión.

## 2. Arquitectura

La aplicación sigue el patrón de navegación por pantallas con React Navigation y gestión de estado local con React hooks.

```
+------------------+
|     App.js       |
| (Navigation Root)|
+--------+---------+
         |
+--------v---------+
|    Screens/      |
| - HomeScreen     |
| - CameraScreen   |
| - ProtocolScreen |
+--------+---------+
         |
+--------v---------+
|   Components/    |
| - EmergencyButton|
| - CameraView     |
| - ProtocolStep   |
+--------+---------+
         |
+--------v---------+
|    Services/     |
| - CameraService  |
| - AIService      |
| - ProtocolService|
+------------------+
```

### Stack Tecnológico

- **React Native:** Framework para desarrollo nativo.
- **Expo:** Plataforma de desarrollo y despliegue.
- **React Navigation:** Navegación entre pantallas.
- **Expo Camera:** API de cámara nativa.
- **AsyncStorage:** Persistencia local de datos.
- **React Native Reanimated:** Animaciones fluidas.

## 3. Instalación y Desarrollo

### Prerrequisitos
- Node.js 18+
- Expo CLI
- Dispositivo móvil con Expo Go o emulador

### Comandos

```bash
# Instalar dependencias
npm install --legacy-peer-deps

# Iniciar servidor de desarrollo
npm start

# Ejecutar en Android
npm run android

# Ejecutar en iOS
npm run ios
```

## 4. Funcionalidades de Reconocimiento

### Simulación de IA
El prototipo incluye una simulación de reconocimiento de lesiones que:
- Simula tiempo de procesamiento realista (2 segundos)
- Genera detecciones mock con diferentes tipos de lesiones
- Proporciona niveles de confianza
- Mapea lesiones a protocolos específicos

### Tipos de Lesiones Simuladas
- **Hemorragias**: Sangrado visible, mapea a protocolo de control de hemorragias
- **Contusiones**: Moretones y golpes, mapea a protocolo de contusiones
- **Quemaduras**: Lesiones por calor, mapea a protocolo de quemaduras

## 5. Protocolos Implementados

### RCP Adulto
- Verificación de conciencia
- Llamada al 112
- Compresiones torácicas

### Atragantamiento
- Evaluación de capacidad de toser
- Golpes interescapulares
- Maniobra de Heimlich

## 6. Consideraciones de Seguridad

- **Disclaimers claros**: La app no sustituye atención médica profesional
- **Acceso rápido al 112**: Botón de emergencia siempre visible
- **Protocolos validados**: Basados en guías médicas estándar
- **Interfaz de emergencia**: Diseño optimizado para situaciones de estrés

## 7. Limitaciones del Prototipo

- **Reconocimiento simulado**: No incluye IA real de visión por computadora
- **Protocolos básicos**: Implementación simplificada de protocolos médicos
- **Sin persistencia**: No guarda historial de sesiones
- **Sin conectividad**: Funciona completamente offline

## 8. Próximos Pasos

1. **Integración de IA real**: Implementar modelos de visión por computadora
2. **Más protocolos**: Ampliar la base de conocimiento médico
3. **Conectividad**: Sincronización con backend y web app
4. **Persistencia**: Guardar historial y configuraciones
5. **Accesibilidad**: Mejoras para usuarios con discapacidades

Este prototipo demuestra el potencial de combinar tecnologías móviles nativas con inteligencia artificial para crear herramientas de primeros auxilios accesibles y efectivas.

