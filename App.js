import React, { useState, useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, SafeAreaView, Alert } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

// Screens
import HomeScreen from './screens/HomeScreen';
import CameraScreen from './screens/CameraScreen';
import ProtocolScreen from './screens/ProtocolScreen';

// Configuración de navegación
const Stack = createStackNavigator();

export default function App() {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Inicialización de la app
    const initializeApp = async () => {
      try {
        // Aquí se pueden cargar configuraciones, verificar permisos, etc.
        console.log('ConRumbo Mobile iniciando...');
        setIsReady(true);
      } catch (error) {
        console.error('Error inicializando la app:', error);
        Alert.alert('Error', 'Error inicializando la aplicación');
      }
    };

    initializeApp();
  }, []);

  if (!isReady) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <Text style={styles.loadingText}>ConRumbo</Text>
        <Text style={styles.loadingSubtext}>Cargando...</Text>
      </SafeAreaView>
    );
  }

  return (
    <NavigationContainer>
      <SafeAreaView style={styles.container}>
        <StatusBar style="auto" />
        <Stack.Navigator
          initialRouteName="Home"
          screenOptions={{
            headerStyle: {
              backgroundColor: '#dc2626',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}
        >
          <Stack.Screen 
            name="Home" 
            component={HomeScreen}
            options={{ 
              title: 'ConRumbo',
              headerShown: false 
            }}
          />
          <Stack.Screen 
            name="Camera" 
            component={CameraScreen}
            options={{ 
              title: 'Reconocimiento',
              headerBackTitle: 'Volver'
            }}
          />
          <Stack.Screen 
            name="Protocol" 
            component={ProtocolScreen}
            options={{ 
              title: 'Protocolo',
              headerBackTitle: 'Volver'
            }}
          />
        </Stack.Navigator>
      </SafeAreaView>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#dc2626',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  loadingSubtext: {
    fontSize: 16,
    color: '#fff',
    opacity: 0.8,
  },
});

