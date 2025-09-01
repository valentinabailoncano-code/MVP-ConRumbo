import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  Alert,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const ProtocolScreen = ({ route, navigation }) => {
  const { protocolType, detectedInjuries } = route.params || {};
  const [currentStep, setCurrentStep] = useState(0);
  const [protocol, setProtocol] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [userResponses, setUserResponses] = useState([]);

  useEffect(() => {
    loadProtocol();
  }, [protocolType]);

  const loadProtocol = async () => {
    setIsLoading(true);
    
    try {
      // Simular carga de protocolo (en una implementación real, esto vendría del backend)
      const mockProtocol = getMockProtocol(protocolType);
      setProtocol(mockProtocol);
    } catch (error) {
      console.error('Error cargando protocolo:', error);
      Alert.alert('Error', 'No se pudo cargar el protocolo');
    } finally {
      setIsLoading(false);
    }
  };

  const getMockProtocol = (type) => {
    const protocols = {
      rcp: {
        id: 'pa_rcp_adulto_v1',
        title: 'RCP Adulto',
        steps: [
          {
            id: 1,
            action: 'Verificar conciencia',
            instruction: 'Toque los hombros de la persona y grite: "¿Está bien?"',
            voice_cue: 'Toque los hombros y grite: ¿Está bien?',
            timer: false,
            critical: true
          },
          {
            id: 2,
            action: 'Llamar al 112',
            instruction: 'Llame inmediatamente al 112 y solicite un DEA si está disponible',
            voice_cue: 'Llame al 112 inmediatamente',
            timer: false,
            critical: true
          },
          {
            id: 3,
            action: 'Iniciar compresiones',
            instruction: 'Coloque las manos en el centro del pecho y comprima fuerte y rápido, 30 compresiones seguidas de 2 ventilaciones',
            voice_cue: 'Comprima fuerte y rápido en el centro del pecho',
            timer: true,
            timer_duration: 18,
            critical: true
          }
        ]
      },
      atragantamiento: {
        id: 'pa_asfixia_adulto_v1',
        title: 'Atragantamiento Adulto',
        steps: [
          {
            id: 1,
            action: 'Evaluar capacidad de toser',
            instruction: 'Pregunte: "¿Puede toser?" Si puede toser, anímelo a hacerlo fuerte',
            voice_cue: '¿Puede toser? Si puede, anímelo a toser fuerte',
            timer: false,
            critical: false
          },
          {
            id: 2,
            action: '5 golpes interescapulares',
            instruction: 'Incline a la persona hacia adelante y dé 5 golpes firmes entre los omóplatos',
            voice_cue: 'Incline hacia adelante y dé 5 golpes firmes entre los omóplatos',
            timer: true,
            timer_duration: 10,
            critical: true
          },
          {
            id: 3,
            action: '5 compresiones abdominales',
            instruction: 'Realice la maniobra de Heimlich: 5 compresiones hacia arriba en el abdomen',
            voice_cue: 'Maniobra de Heimlich: 5 compresiones hacia arriba en el abdomen',
            timer: true,
            timer_duration: 10,
            critical: true
          }
        ]
      },
      hemorragia: {
        id: 'pa_hemorragias_v1',
        title: 'Control de Hemorragias',
        steps: [
          {
            id: 1,
            action: 'Evaluar la hemorragia',
            instruction: 'Identifique la fuente y gravedad del sangrado. Use guantes si están disponibles',
            voice_cue: 'Identifique la fuente del sangrado y use protección',
            timer: false,
            critical: false
          },
          {
            id: 2,
            action: 'Presión directa',
            instruction: 'Aplique presión directa sobre la herida con un paño limpio o gasa',
            voice_cue: 'Aplique presión directa sobre la herida',
            timer: false,
            critical: true
          },
          {
            id: 3,
            action: 'Elevar la extremidad',
            instruction: 'Si es posible, eleve la extremidad afectada por encima del nivel del corazón',
            voice_cue: 'Eleve la extremidad por encima del corazón si es posible',
            timer: false,
            critical: false
          }
        ]
      }
    };

    return protocols[type] || protocols.rcp;
  };

  const handleNextStep = () => {
    if (!protocol) return;

    if (currentStep < protocol.steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      Alert.alert(
        'Protocolo Completado',
        'Has completado todos los pasos del protocolo. Recuerda llamar al 112 si no lo has hecho ya.',
        [
          { text: 'Llamar 112', onPress: () => Linking.openURL('tel:112') },
          { text: 'Finalizar', onPress: () => navigation.goBack() },
        ]
      );
    }
  };

  const handlePreviousStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleEmergencyCall = () => {
    Alert.alert(
      'Llamar al 112',
      '¿Deseas llamar al número de emergencias?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { 
          text: 'Llamar', 
          style: 'destructive',
          onPress: () => Linking.openURL('tel:112')
        },
      ]
    );
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#dc2626" />
        <Text style={styles.loadingText}>Cargando protocolo...</Text>
      </SafeAreaView>
    );
  }

  if (!protocol) {
    return (
      <SafeAreaView style={styles.errorContainer}>
        <Text style={styles.errorText}>Error cargando el protocolo</Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>Volver</Text>
        </TouchableOpacity>
      </SafeAreaView>
    );
  }

  const currentStepData = protocol.steps[currentStep];
  const progress = ((currentStep + 1) / protocol.steps.length) * 100;

  return (
    <SafeAreaView style={styles.container}>
      {/* Header con progreso */}
      <View style={styles.header}>
        <Text style={styles.protocolTitle}>{protocol.title}</Text>
        <Text style={styles.stepCounter}>
          Paso {currentStep + 1} de {protocol.steps.length}
        </Text>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${progress}%` }]} />
        </View>
      </View>

      {/* Información de detecciones (si las hay) */}
      {detectedInjuries && detectedInjuries.length > 0 && (
        <View style={styles.detectionsContainer}>
          <Text style={styles.detectionsTitle}>🔍 Lesiones detectadas:</Text>
          {detectedInjuries.map((injury, index) => (
            <Text key={index} style={styles.detectionItem}>
              • {injury.type} (confianza: {Math.round(injury.confidence * 100)}%)
            </Text>
          ))}
        </View>
      )}

      {/* Contenido del paso actual */}
      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        <View style={[
          styles.stepCard,
          currentStepData.critical && styles.criticalStep
        ]}>
          {/* Acción principal */}
          <Text style={styles.stepAction}>{currentStepData.action}</Text>
          
          {/* Instrucción detallada */}
          <Text style={styles.stepInstruction}>{currentStepData.instruction}</Text>
          
          {/* Guía de voz */}
          {currentStepData.voice_cue && (
            <View style={styles.voiceCueContainer}>
              <Text style={styles.voiceCueText}>
                🎤 "{currentStepData.voice_cue}"
              </Text>
            </View>
          )}

          {/* Timer si es necesario */}
          {currentStepData.timer && (
            <View style={styles.timerContainer}>
              <Text style={styles.timerText}>
                ⏱️ Duración recomendada: {currentStepData.timer_duration} segundos
              </Text>
            </View>
          )}

          {/* Indicador crítico */}
          {currentStepData.critical && (
            <View style={styles.criticalBadge}>
              <Text style={styles.criticalText}>⚠️ PASO CRÍTICO</Text>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Controles de navegación */}
      <View style={styles.controls}>
        <View style={styles.navigationButtons}>
          <TouchableOpacity
            style={[
              styles.navButton,
              styles.prevButton,
              currentStep === 0 && styles.disabledButton
            ]}
            onPress={handlePreviousStep}
            disabled={currentStep === 0}
          >
            <Text style={styles.navButtonText}>← Anterior</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navButton, styles.nextButton]}
            onPress={handleNextStep}
          >
            <Text style={styles.navButtonText}>
              {currentStep === protocol.steps.length - 1 ? 'Finalizar' : 'Siguiente →'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Botón de emergencia */}
        <TouchableOpacity
          style={styles.emergencyButton}
          onPress={handleEmergencyCall}
        >
          <Text style={styles.emergencyButtonText}>📞 LLAMAR 112</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f8f9fa',
  },
  errorText: {
    fontSize: 18,
    color: '#dc2626',
    textAlign: 'center',
    marginBottom: 20,
  },
  backButton: {
    backgroundColor: '#6b7280',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  header: {
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  protocolTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 4,
  },
  stepCounter: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 12,
  },
  progressBar: {
    height: 4,
    backgroundColor: '#e5e7eb',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#2563eb',
    borderRadius: 2,
  },
  detectionsContainer: {
    backgroundColor: '#fef3c7',
    padding: 12,
    margin: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#fbbf24',
  },
  detectionsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#92400e',
    marginBottom: 8,
  },
  detectionItem: {
    fontSize: 12,
    color: '#92400e',
    marginBottom: 4,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  stepCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  criticalStep: {
    borderLeftWidth: 4,
    borderLeftColor: '#dc2626',
  },
  stepAction: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 12,
  },
  stepInstruction: {
    fontSize: 16,
    color: '#374151',
    lineHeight: 24,
    marginBottom: 16,
  },
  voiceCueContainer: {
    backgroundColor: '#dbeafe',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#93c5fd',
  },
  voiceCueText: {
    fontSize: 14,
    color: '#1e40af',
    fontStyle: 'italic',
  },
  timerContainer: {
    backgroundColor: '#f3f4f6',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  timerText: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
  },
  criticalBadge: {
    backgroundColor: '#fee2e2',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderColor: '#fca5a5',
  },
  criticalText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#dc2626',
  },
  controls: {
    backgroundColor: '#fff',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  navigationButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  navButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginHorizontal: 4,
  },
  prevButton: {
    backgroundColor: '#6b7280',
  },
  nextButton: {
    backgroundColor: '#2563eb',
  },
  disabledButton: {
    backgroundColor: '#d1d5db',
  },
  navButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  emergencyButton: {
    backgroundColor: '#dc2626',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  emergencyButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default ProtocolScreen;

