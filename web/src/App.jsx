import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Heart, Shield, Mic, Settings } from 'lucide-react';
import './App.css';

// Componentes
import EmergencyButton from './components/EmergencyButton';
import VoiceButton from './components/VoiceButton';
import MetronomeDisplay from './components/MetronomeDisplay';
import StepCard from './components/StepCard';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';

// Stores y utilidades
import { useAppStore, useTriageStore, useProtocolStore } from './lib/stores';
import { useSpeech } from './lib/speech';
import { offlineApiClient } from './lib/api';

// Páginas principales
const HomePage = () => {
  const { speak } = useSpeech();
  const { setTriage } = useTriageStore();
  const { setActiveProtocol } = useProtocolStore();
  const [isLoading, setIsLoading] = useState(false);

  const emergencyProtocols = [
    {
      id: 'pa_rcp_adulto_v1',
      title: 'RCP Adulto',
      description: 'Reanimación cardiopulmonar para adultos',
      icon: Heart,
      color: 'bg-red-500',
      urgent: true
    },
    {
      id: 'pa_asfixia_adulto_v1',
      title: 'Atragantamiento',
      description: 'Maniobra de Heimlich para adultos',
      icon: Shield,
      color: 'bg-orange-500',
      urgent: true
    }
  ];

  const handleProtocolSelect = async (protocolId) => {
    setIsLoading(true);
    
    try {
      // Simular triaje rápido para protocolo directo
      const triageData = {
        intent: protocolId.includes('rcp') ? 'parada_cardiorespiratoria' : 'atragantamiento',
        edad: 'adulto',
        estado_conciencia: 'inconsciente',
        respiracion: 'ausente'
      };

      const triageResponse = await offlineApiClient.submitTriage(triageData);
      setTriage(triageResponse);

      // Cargar protocolo
      const protocol = await offlineApiClient.getProtocol(protocolId);
      setActiveProtocol(protocol);

      // Anunciar inicio
      await speak(`Iniciando protocolo: ${protocol.title}`, { priority: 'urgent' });

      // Navegar a la vista de protocolo
      window.location.hash = '#/protocol';
      
    } catch (error) {
      console.error('Error cargando protocolo:', error);
      alert('Error cargando el protocolo. Usando modo offline.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceCommand = async (transcript) => {
    const command = transcript.toLowerCase();
    
    if (command.includes('rcp') || command.includes('no respira')) {
      await handleProtocolSelect('pa_rcp_adulto_v1');
    } else if (command.includes('atragantamiento') || command.includes('ahoga')) {
      await handleProtocolSelect('pa_asfixia_adulto_v1');
    } else {
      await speak('No entendí el comando. Puedes decir "RCP" o "atragantamiento"');
    }
  };

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            ConRumbo
          </h1>
          <p className="text-lg text-muted-foreground">
            Primeros auxilios paso a paso con guía de voz
          </p>
        </div>

        {/* Botón de emergencia principal */}
        <div className="flex justify-center mb-8">
          <EmergencyButton size="xl" pulsing={true} />
        </div>

        {/* Control de voz principal */}
        <div className="flex justify-center mb-8">
          <div className="text-center">
            <VoiceButton 
              size="xl"
              onTranscript={handleVoiceCommand}
              mode="toggle"
            />
            <p className="text-sm text-muted-foreground mt-2">
              Di "RCP" o "Atragantamiento" para comenzar
            </p>
          </div>
        </div>

        {/* Protocolos de emergencia */}
        <div className="grid md:grid-cols-2 gap-4 mb-8">
          {emergencyProtocols.map((protocol) => {
            const IconComponent = protocol.icon;
            return (
              <Card 
                key={protocol.id}
                className="cursor-pointer hover:shadow-lg transition-shadow border-2 hover:border-primary"
                onClick={() => handleProtocolSelect(protocol.id)}
              >
                <CardHeader>
                  <CardTitle className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${protocol.color} text-white`}>
                      <IconComponent className="h-6 w-6" />
                    </div>
                    <span>{protocol.title}</span>
                    {protocol.urgent && (
                      <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
                        URGENTE
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{protocol.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Información adicional */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
          <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">
            ℹ️ Información importante
          </h3>
          <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
            <li>• Esta aplicación proporciona guías de primeros auxilios</li>
            <li>• NO sustituye la atención médica profesional</li>
            <li>• En emergencias graves, llama al 112 inmediatamente</li>
            <li>• Funciona sin conexión para protocolos críticos</li>
          </ul>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 text-center">
              <div className="loading-spinner w-8 h-8 mx-auto mb-4"></div>
              <p>Cargando protocolo...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const ProtocolPage = () => {
  const { activeProtocol, currentStep, setCurrentStep } = useProtocolStore();
  const { speak } = useSpeech();
  const [stepResponse, setStepResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (activeProtocol && activeProtocol.steps && activeProtocol.steps.length > 0) {
      const step = activeProtocol.steps[currentStep];
      if (step && step.voice_cue) {
        speak(step.voice_cue);
      }
    }
  }, [currentStep, activeProtocol]);

  const handleNextStep = async () => {
    if (!activeProtocol || !activeProtocol.steps) return;

    setIsLoading(true);
    
    try {
      const nextStepData = {
        flow_id: activeProtocol.id,
        step_idx: currentStep,
        user_feedback: stepResponse
      };

      const response = await offlineApiClient.getNextStep(nextStepData);
      
      if (response.is_final) {
        await speak(response.say);
        alert('Protocolo completado. Recuerda llamar al 112 si es necesario.');
        window.location.hash = '#/';
      } else {
        setCurrentStep(currentStep + 1);
        setStepResponse(null);
        
        if (response.safety_alert) {
          await speak(response.safety_alert, { priority: 'urgent' });
        }
      }
      
    } catch (error) {
      console.error('Error obteniendo siguiente paso:', error);
      // Fallback: avanzar al siguiente paso
      if (currentStep < activeProtocol.steps.length - 1) {
        setCurrentStep(currentStep + 1);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleUserResponse = (transcript) => {
    setStepResponse(transcript);
    speak(`Entendido: ${transcript}`);
  };

  if (!activeProtocol) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg mb-4">No hay protocolo activo</p>
          <Button onClick={() => window.location.hash = '#/'}>
            Volver al inicio
          </Button>
        </div>
      </div>
    );
  }

  const currentStepData = activeProtocol.steps?.[currentStep];
  const isRCPProtocol = activeProtocol.id.includes('rcp');

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header del protocolo */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">{activeProtocol.title}</h1>
            <p className="text-muted-foreground">
              Paso {currentStep + 1} de {activeProtocol.steps?.length || 0}
            </p>
          </div>
          <EmergencyButton size="default" />
        </div>

        {/* Progreso */}
        <div className="mb-6">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ 
                width: `${((currentStep + 1) / (activeProtocol.steps?.length || 1)) * 100}%` 
              }}
            />
          </div>
        </div>

        {/* Metrónomo para RCP */}
        {isRCPProtocol && currentStep >= 2 && (
          <div className="mb-6">
            <MetronomeDisplay autoStart={true} />
          </div>
        )}

        {/* Paso actual */}
        {currentStepData && (
          <StepCard
            step={currentStepData}
            isActive={true}
            onNext={handleNextStep}
            onUserResponse={handleUserResponse}
            className="mb-6"
          />
        )}

        {/* Respuesta del usuario */}
        {stepResponse && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <p className="text-sm text-green-800 dark:text-green-200">
              <strong>Tu respuesta:</strong> {stepResponse}
            </p>
          </div>
        )}

        {/* Controles */}
        <div className="flex justify-between items-center">
          <Button 
            variant="outline"
            onClick={() => window.location.hash = '#/'}
          >
            Salir del protocolo
          </Button>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">
              {activeProtocol._offline && '📱 Modo offline'}
            </span>
          </div>
        </div>

        {/* Loading overlay */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4">
              <div className="loading-spinner w-6 h-6 mx-auto"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Componente principal de la aplicación
function App() {
  const { isOnline, setOnline } = useAppStore();

  useEffect(() => {
    // Registrar Service Worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('Service Worker registrado:', registration);
        })
        .catch((error) => {
          console.error('Error registrando Service Worker:', error);
        });
    }

    // Monitorear estado de conexión
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [setOnline]);

  return (
    <Router>
      <div className="App">
        {/* Indicador de estado de conexión */}
        {!isOnline && (
          <div className="fixed top-0 left-0 right-0 bg-yellow-500 text-white text-center py-2 z-50">
            📱 Modo offline - Protocolos críticos disponibles
          </div>
        )}

        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/protocol" element={<ProtocolPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
