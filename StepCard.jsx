import React, { useState, useEffect } from 'react';
import { ChevronRight, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import VoiceButton from './VoiceButton';

const StepCard = ({
  step,
  isActive = false,
  isCompleted = false,
  isEmergency = false,
  onNext = null,
  onUserResponse = null,
  showVoiceButton = true,
  className = ''
}) => {
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [isTimerActive, setIsTimerActive] = useState(false);

  useEffect(() => {
    if (isActive && step?.ui?.timer && step?.ui?.timer_duration) {
      setTimeRemaining(step.ui.timer_duration);
      setIsTimerActive(true);
    } else {
      setTimeRemaining(null);
      setIsTimerActive(false);
    }
  }, [isActive, step]);

  useEffect(() => {
    let interval = null;

    if (isTimerActive && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining(time => {
          if (time <= 1) {
            setIsTimerActive(false);
            // Auto-avanzar cuando el timer termine
            if (onNext) {
              setTimeout(onNext, 500);
            }
            return 0;
          }
          return time - 1;
        });
      }, 1000);
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isTimerActive, timeRemaining, onNext]);

  const handleVoiceResponse = (transcript) => {
    if (onUserResponse) {
      onUserResponse(transcript);
    }
  };

  const handleNextClick = () => {
    if (onNext) {
      onNext();
    }
  };

  const getCardClass = () => {
    let baseClass = 'step-card';
    
    if (isActive) {
      baseClass += ' active';
    }
    
    if (isCompleted) {
      baseClass += ' completed';
    }
    
    if (isEmergency) {
      baseClass += ' emergency';
    }
    
    return baseClass;
  };

  const getStatusIcon = () => {
    if (isCompleted) {
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    }
    
    if (isEmergency) {
      return <AlertTriangle className="h-5 w-5 text-red-600" />;
    }
    
    if (isActive) {
      return <div className="h-3 w-3 bg-blue-600 rounded-full animate-pulse" />;
    }
    
    return null;
  };

  if (!step) {
    return null;
  }

  return (
    <Card className={`${getCardClass()} ${className}`}>
      <CardContent className="p-6">
        {/* Header con estado */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <span className="text-sm font-medium text-muted-foreground">
              Paso {step.id}
            </span>
          </div>
          
          {timeRemaining !== null && (
            <div className="flex items-center space-x-2 text-sm">
              <Clock className="h-4 w-4" />
              <span className={`font-mono ${timeRemaining <= 5 ? 'text-red-600 font-bold' : ''}`}>
                {timeRemaining}s
              </span>
            </div>
          )}
        </div>

        {/* Acción principal */}
        {step.action && (
          <div className="mb-3">
            <h3 className="text-lg font-semibold text-foreground">
              {step.action}
            </h3>
          </div>
        )}

        {/* Instrucción detallada */}
        <div className="mb-4">
          <p className="text-base text-foreground leading-relaxed">
            {step.instruction}
          </p>
        </div>

        {/* Guía de voz */}
        {step.voice_cue && isActive && (
          <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200 italic">
              🎤 "{step.voice_cue}"
            </p>
          </div>
        )}

        {/* Ilustración */}
        {step.ui?.illustration && (
          <div className="mb-4 flex justify-center">
            <div className="w-32 h-32 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300 dark:border-gray-600">
              <span className="text-sm text-gray-500 dark:text-gray-400 text-center">
                Ilustración:<br />{step.ui.illustration}
              </span>
            </div>
          </div>
        )}

        {/* Timer visual */}
        {isTimerActive && timeRemaining !== null && (
          <div className="mb-4">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-1000 ease-linear"
                style={{ 
                  width: `${((step.ui.timer_duration - timeRemaining) / step.ui.timer_duration) * 100}%` 
                }}
              />
            </div>
          </div>
        )}

        {/* Controles */}
        {isActive && (
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {showVoiceButton && (
                <VoiceButton
                  onTranscript={handleVoiceResponse}
                  size="small"
                  mode="toggle"
                />
              )}
            </div>

            {step.ui?.next_button !== false && !isTimerActive && (
              <Button
                onClick={handleNextClick}
                className="flex items-center space-x-2"
              >
                <span>Siguiente</span>
                <ChevronRight className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}

        {/* Condiciones de salida */}
        {step.exit_conditions && step.exit_conditions.length > 0 && isActive && (
          <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <h4 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
              Señales de éxito:
            </h4>
            <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
              {step.exit_conditions.map((condition, index) => (
                <li key={index} className="flex items-center space-x-2">
                  <CheckCircle className="h-3 w-3 flex-shrink-0" />
                  <span>{condition}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Indicador de progreso para pasos completados */}
        {isCompleted && (
          <div className="mt-4 flex items-center space-x-2 text-green-600">
            <CheckCircle className="h-4 w-4" />
            <span className="text-sm font-medium">Paso completado</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default StepCard;

