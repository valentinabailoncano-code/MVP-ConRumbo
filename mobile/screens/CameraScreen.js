import React, { useState, useEffect, useRef } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  Alert,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { Camera } from 'expo-camera';
import { SafeAreaView } from 'react-native-safe-area-context';

const { width, height } = Dimensions.get('window');

const CameraScreen = ({ navigation }) => {
  const [hasPermission, setHasPermission] = useState(null);
  const [type, setType] = useState(Camera.Constants.Type.back);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [detectedInjuries, setDetectedInjuries] = useState([]);
  const [overlayPoints, setOverlayPoints] = useState([]);
  const cameraRef = useRef(null);

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  const analyzeImage = async () => {
    if (!cameraRef.current) return;

    setIsAnalyzing(true);
    
    try {
      // Tomar foto
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.7,
        base64: false,
      });

      // Simular análisis de IA (en una implementación real, esto se enviaría a un servicio de ML)
      await simulateInjuryDetection(photo);
      
    } catch (error) {
      console.error('Error analizando imagen:', error);
      Alert.alert('Error', 'No se pudo analizar la imagen');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const simulateInjuryDetection = async (photo) => {
    // Simular tiempo de procesamiento
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Simular detección de lesiones
    const mockDetections = [
      {
        type: 'hemorragia',
        confidence: 0.85,
        location: { x: 0.3, y: 0.4 },
        severity: 'moderada',
        protocol: 'pa_hemorragias_v1'
      },
      {
        type: 'contusion',
        confidence: 0.72,
        location: { x: 0.6, y: 0.3 },
        severity: 'leve',
        protocol: 'pa_contusiones_v1'
      }
    ];

    setDetectedInjuries(mockDetections);
    
    // Crear puntos de overlay
    const points = mockDetections.map((detection, index) => ({
      id: index,
      x: detection.location.x * width,
      y: detection.location.y * height * 0.7, // Ajustar por la UI
      type: detection.type,
      confidence: detection.confidence
    }));
    
    setOverlayPoints(points);

    // Mostrar resultados
    if (mockDetections.length > 0) {
      const injuryTypes = mockDetections.map(d => d.type).join(', ');
      Alert.alert(
        'Lesiones Detectadas',
        `Se detectaron: ${injuryTypes}\n\n¿Deseas ver el protocolo recomendado?`,
        [
          { text: 'Cancelar', style: 'cancel' },
          { 
            text: 'Ver Protocolo', 
            onPress: () => {
              const primaryInjury = mockDetections[0];
              navigation.navigate('Protocol', { 
                protocolType: primaryInjury.type,
                detectedInjuries: mockDetections 
              });
            }
          },
        ]
      );
    } else {
      Alert.alert('Sin Detecciones', 'No se detectaron lesiones visibles en la imagen.');
    }
  };

  const resetDetection = () => {
    setDetectedInjuries([]);
    setOverlayPoints([]);
  };

  if (hasPermission === null) {
    return (
      <View style={styles.permissionContainer}>
        <ActivityIndicator size="large" color="#dc2626" />
        <Text style={styles.permissionText}>Solicitando permisos de cámara...</Text>
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>
          No se puede acceder a la cámara. Por favor, habilita los permisos en la configuración.
        </Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>Volver</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.cameraContainer}>
        <Camera
          ref={cameraRef}
          style={styles.camera}
          type={type}
          ratio="16:9"
        >
          {/* Overlay de detecciones */}
          {overlayPoints.map((point) => (
            <View
              key={point.id}
              style={[
                styles.detectionPoint,
                {
                  left: point.x - 15,
                  top: point.y - 15,
                  backgroundColor: point.type === 'hemorragia' ? '#dc2626' : '#f59e0b',
                }
              ]}
            >
              <Text style={styles.detectionText}>
                {Math.round(point.confidence * 100)}%
              </Text>
            </View>
          ))}

          {/* Guías de posicionamiento */}
          <View style={styles.guidesContainer}>
            <View style={styles.centerGuide} />
            <Text style={styles.guideText}>
              Posiciona la lesión en el centro de la pantalla
            </Text>
          </View>
        </Camera>
      </View>

      {/* Controles */}
      <View style={styles.controlsContainer}>
        {/* Información de detecciones */}
        {detectedInjuries.length > 0 && (
          <View style={styles.detectionsInfo}>
            <Text style={styles.detectionsTitle}>
              Lesiones detectadas: {detectedInjuries.length}
            </Text>
            {detectedInjuries.map((injury, index) => (
              <Text key={index} style={styles.detectionItem}>
                • {injury.type} ({Math.round(injury.confidence * 100)}% confianza)
              </Text>
            ))}
          </View>
        )}

        {/* Botones de acción */}
        <View style={styles.buttonsContainer}>
          <TouchableOpacity
            style={[styles.actionButton, styles.analyzeButton]}
            onPress={analyzeImage}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.actionButtonText}>📷 Analizar</Text>
            )}
          </TouchableOpacity>

          {detectedInjuries.length > 0 && (
            <TouchableOpacity
              style={[styles.actionButton, styles.resetButton]}
              onPress={resetDetection}
            >
              <Text style={styles.actionButtonText}>🔄 Nuevo Análisis</Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            style={[styles.actionButton, styles.flipButton]}
            onPress={() => {
              setType(
                type === Camera.Constants.Type.back
                  ? Camera.Constants.Type.front
                  : Camera.Constants.Type.back
              );
            }}
          >
            <Text style={styles.actionButtonText}>🔄 Voltear</Text>
          </TouchableOpacity>
        </View>

        {/* Instrucciones */}
        <View style={styles.instructionsContainer}>
          <Text style={styles.instructionsTitle}>Instrucciones:</Text>
          <Text style={styles.instructionsText}>
            1. Apunta la cámara hacia la lesión{'\n'}
            2. Asegúrate de que haya buena iluminación{'\n'}
            3. Mantén la cámara estable{'\n'}
            4. Presiona "Analizar" para detectar lesiones
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f8f9fa',
  },
  permissionText: {
    fontSize: 16,
    textAlign: 'center',
    color: '#374151',
    marginTop: 16,
  },
  backButton: {
    backgroundColor: '#dc2626',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    marginTop: 20,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  cameraContainer: {
    flex: 1,
    position: 'relative',
  },
  camera: {
    flex: 1,
  },
  detectionPoint: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#fff',
  },
  detectionText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  guidesContainer: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -50 }, { translateY: -50 }],
    alignItems: 'center',
  },
  centerGuide: {
    width: 100,
    height: 100,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    borderRadius: 50,
    borderStyle: 'dashed',
  },
  guideText: {
    color: '#fff',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 4,
  },
  controlsContainer: {
    backgroundColor: '#fff',
    padding: 16,
    maxHeight: height * 0.4,
  },
  detectionsInfo: {
    backgroundColor: '#f3f4f6',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  detectionsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 8,
  },
  detectionItem: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
  },
  buttonsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  actionButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  analyzeButton: {
    backgroundColor: '#dc2626',
  },
  resetButton: {
    backgroundColor: '#6b7280',
  },
  flipButton: {
    backgroundColor: '#2563eb',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  instructionsContainer: {
    backgroundColor: '#dbeafe',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#93c5fd',
  },
  instructionsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1e40af',
    marginBottom: 8,
  },
  instructionsText: {
    fontSize: 12,
    color: '#1e40af',
    lineHeight: 16,
  },
});

export default CameraScreen;

