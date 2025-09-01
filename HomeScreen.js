import React from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  Alert,
  Linking,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const { width } = Dimensions.get('window');

const HomeScreen = ({ navigation }) => {
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

  const handleCameraAccess = () => {
    navigation.navigate('Camera');
  };

  const handleProtocolSelect = (protocolType) => {
    navigation.navigate('Protocol', { protocolType });
  };

  const emergencyProtocols = [
    {
      id: 'rcp',
      title: 'RCP Adulto',
      description: 'Reanimación cardiopulmonar',
      color: '#dc2626',
      urgent: true,
    },
    {
      id: 'atragantamiento',
      title: 'Atragantamiento',
      description: 'Maniobra de Heimlich',
      color: '#ea580c',
      urgent: true,
    },
    {
      id: 'hemorragia',
      title: 'Hemorragias',
      description: 'Control de sangrado',
      color: '#b91c1c',
      urgent: true,
    },
    {
      id: 'quemaduras',
      title: 'Quemaduras',
      description: 'Tratamiento de quemaduras',
      color: '#f59e0b',
      urgent: false,
    },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>ConRumbo</Text>
          <Text style={styles.subtitle}>Primeros auxilios móvil</Text>
        </View>

        {/* Botón de emergencia principal */}
        <TouchableOpacity
          style={styles.emergencyButton}
          onPress={handleEmergencyCall}
          activeOpacity={0.8}
        >
          <Text style={styles.emergencyButtonText}>📞 LLAMAR 112</Text>
        </TouchableOpacity>

        {/* Botón de cámara para reconocimiento */}
        <TouchableOpacity
          style={styles.cameraButton}
          onPress={handleCameraAccess}
          activeOpacity={0.8}
        >
          <Text style={styles.cameraButtonText}>📷 Reconocimiento por Cámara</Text>
          <Text style={styles.cameraButtonSubtext}>
            Identifica lesiones y obtén protocolos específicos
          </Text>
        </TouchableOpacity>

        {/* Protocolos de emergencia */}
        <View style={styles.protocolsSection}>
          <Text style={styles.sectionTitle}>Protocolos de Emergencia</Text>
          <View style={styles.protocolsGrid}>
            {emergencyProtocols.map((protocol) => (
              <TouchableOpacity
                key={protocol.id}
                style={[
                  styles.protocolCard,
                  { backgroundColor: protocol.color },
                ]}
                onPress={() => handleProtocolSelect(protocol.id)}
                activeOpacity={0.8}
              >
                <Text style={styles.protocolTitle}>{protocol.title}</Text>
                <Text style={styles.protocolDescription}>
                  {protocol.description}
                </Text>
                {protocol.urgent && (
                  <View style={styles.urgentBadge}>
                    <Text style={styles.urgentText}>URGENTE</Text>
                  </View>
                )}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Información adicional */}
        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>ℹ️ Información importante</Text>
          <Text style={styles.infoText}>
            • Esta aplicación proporciona guías de primeros auxilios{'\n'}
            • NO sustituye la atención médica profesional{'\n'}
            • En emergencias graves, llama al 112 inmediatamente{'\n'}
            • Usa la cámara para identificar lesiones específicas
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollContent: {
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
  },
  emergencyButton: {
    backgroundColor: '#dc2626',
    paddingVertical: 20,
    paddingHorizontal: 30,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 20,
    shadowColor: '#dc2626',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  emergencyButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  cameraButton: {
    backgroundColor: '#2563eb',
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 30,
    shadowColor: '#2563eb',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 4,
  },
  cameraButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  cameraButtonSubtext: {
    color: '#dbeafe',
    fontSize: 14,
    textAlign: 'center',
  },
  protocolsSection: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 16,
  },
  protocolsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  protocolCard: {
    width: (width - 50) / 2,
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    minHeight: 100,
    justifyContent: 'space-between',
  },
  protocolTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  protocolDescription: {
    color: '#fff',
    fontSize: 12,
    opacity: 0.9,
    marginBottom: 8,
  },
  urgentBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
  },
  urgentText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  infoSection: {
    backgroundColor: '#dbeafe',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#93c5fd',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1e40af',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#1e40af',
    lineHeight: 20,
  },
});

export default HomeScreen;

