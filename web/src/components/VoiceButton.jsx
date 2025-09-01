import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { Button } from './ui/button';
import { useSpeech } from '../lib/speech';

const VoiceButton = ({ 
  onTranscript = null,
  onSpeechStart = null,
  onSpeechEnd = null,
  className = '',
  size = 'default',
  mode = 'toggle' // 'toggle', 'push-to-talk', 'speak-only'
}) => {
  const {
    isListening,
    isSpeaking,
    isSupported,
    voiceEnabled,
    toggleVoice,
    startListening,
    stopListening,
    stopSpeaking,
    error
  } = useSpeech();

  const [isPressed, setIsPressed] = useState(false);

  useEffect(() => {
    // Escuchar resultados de voz
    const handleSpeechResult = (event) => {
      if (onTranscript) {
        onTranscript(event.detail.transcript);
      }
    };

    window.addEventListener('speechResult', handleSpeechResult);
    return () => window.removeEventListener('speechResult', handleSpeechResult);
  }, [onTranscript]);

  useEffect(() => {
    if (isSpeaking && onSpeechStart) {
      onSpeechStart();
    } else if (!isSpeaking && onSpeechEnd) {
      onSpeechEnd();
    }
  }, [isSpeaking, onSpeechStart, onSpeechEnd]);

  const handleClick = async () => {
    if (!isSupported) {
      alert('Tu navegador no soporta reconocimiento de voz');
      return;
    }

    if (!voiceEnabled) {
      toggleVoice();
      return;
    }

    if (mode === 'speak-only') {
      if (isSpeaking) {
        stopSpeaking();
      }
      return;
    }

    if (mode === 'toggle') {
      if (isListening) {
        stopListening();
      } else {
        try {
          await startListening(10000); // 10 segundos timeout
        } catch (error) {
          console.error('Error iniciando reconocimiento:', error);
        }
      }
    }
  };

  const handleMouseDown = async () => {
    if (mode === 'push-to-talk' && voiceEnabled && !isListening) {
      setIsPressed(true);
      try {
        await startListening(30000); // 30 segundos para push-to-talk
      } catch (error) {
        console.error('Error en push-to-talk:', error);
      }
    }
  };

  const handleMouseUp = () => {
    if (mode === 'push-to-talk' && isPressed) {
      setIsPressed(false);
      stopListening();
    }
  };

  const getIcon = () => {
    if (!voiceEnabled) {
      return <VolumeX className="h-5 w-5" />;
    }

    if (mode === 'speak-only') {
      return isSpeaking ? <Volume2 className="h-5 w-5" /> : <VolumeX className="h-5 w-5" />;
    }

    return isListening ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />;
  };

  const getButtonClass = () => {
    let baseClass = 'voice-button';
    
    if (isListening || isPressed) {
      baseClass += ' listening';
    } else if (isSpeaking) {
      baseClass += ' speaking';
    }

    return baseClass;
  };

  const getAriaLabel = () => {
    if (!voiceEnabled) {
      return 'Activar voz';
    }

    if (mode === 'speak-only') {
      return isSpeaking ? 'Detener síntesis de voz' : 'Síntesis de voz inactiva';
    }

    if (mode === 'push-to-talk') {
      return 'Mantener presionado para hablar';
    }

    return isListening ? 'Detener reconocimiento de voz' : 'Iniciar reconocimiento de voz';
  };

  const sizeClasses = {
    small: 'p-2',
    default: 'p-4',
    large: 'p-6',
    xl: 'p-8'
  };

  if (!isSupported) {
    return (
      <Button
        disabled
        className={`${getButtonClass()} opacity-50 ${sizeClasses[size]} ${className}`}
        aria-label="Reconocimiento de voz no soportado"
      >
        <MicOff className="h-5 w-5" />
      </Button>
    );
  }

  return (
    <div className="relative">
      <Button
        onClick={handleClick}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp} // Para casos donde el mouse sale del botón
        className={`${getButtonClass()} ${sizeClasses[size]} ${className}`}
        aria-label={getAriaLabel()}
        aria-pressed={isListening || isPressed}
      >
        {getIcon()}
      </Button>

      {/* Indicador de estado */}
      {(isListening || isSpeaking || error) && (
        <div className="absolute -top-2 -right-2">
          <div className={`
            w-3 h-3 rounded-full
            ${isListening ? 'bg-red-500 animate-pulse' : ''}
            ${isSpeaking ? 'bg-green-500 animate-pulse' : ''}
            ${error ? 'bg-yellow-500' : ''}
          `} />
        </div>
      )}

      {/* Tooltip para push-to-talk */}
      {mode === 'push-to-talk' && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity">
          Mantener presionado
        </div>
      )}

      {/* Mensaje de error */}
      {error && (
        <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-1 bg-red-100 text-red-800 text-xs rounded border border-red-200 whitespace-nowrap">
          {error}
        </div>
      )}
    </div>
  );
};

export default VoiceButton;

