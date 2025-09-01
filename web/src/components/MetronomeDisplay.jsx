import React, { useEffect } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { useMetronome } from '../lib/metronome';

const MetronomeDisplay = ({ 
  className = '',
  showControls = true,
  autoStart = false 
}) => {
  const {
    isActive,
    bpm,
    currentBeat,
    cycleCount,
    compressionCount,
    ventilationCount,
    isCompressionPhase,
    start,
    stop,
    setBpm,
    sync,
    getStatus
  } = useMetronome();

  useEffect(() => {
    if (autoStart && !isActive) {
      start();
    }

    // Cleanup al desmontar
    return () => {
      if (isActive) {
        stop();
      }
    };
  }, [autoStart]);

  const handleStartStop = async () => {
    if (isActive) {
      stop();
    } else {
      try {
        await start();
      } catch (error) {
        console.error('Error iniciando metrónomo:', error);
        alert('Error iniciando el metrónomo. Verifica los permisos de audio.');
      }
    }
  };

  const handleBpmChange = (newBpm) => {
    setBpm(newBpm);
  };

  const handleSync = () => {
    sync();
  };

  const getPhaseText = () => {
    if (isCompressionPhase) {
      return `Compresiones: ${compressionCount}/30`;
    } else {
      return `Ventilaciones: ${ventilationCount}/2`;
    }
  };

  const getNextPhaseText = () => {
    if (isCompressionPhase) {
      const remaining = 30 - compressionCount;
      return `${remaining} compresiones restantes`;
    } else {
      const remaining = 2 - ventilationCount;
      return `${remaining} ventilaciones restantes`;
    }
  };

  return (
    <Card className={`metronome-display ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Metrónomo RCP</span>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-normal">
              {bpm} BPM
            </span>
            {isActive && (
              <div className="status-indicator online">
                Activo
              </div>
            )}
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Beat visual */}
        <div className="flex justify-center">
          <div className={`
            metronome-beat
            ${isActive ? 'active' : ''}
            ${isCompressionPhase ? 'compression' : 'ventilation'}
          `}>
            {isActive ? currentBeat % 4 + 1 : '●'}
          </div>
        </div>

        {/* Información del ciclo */}
        {isActive && (
          <div className="text-center space-y-2">
            <div className="text-lg font-semibold">
              {getPhaseText()}
            </div>
            <div className="text-sm text-muted-foreground">
              {getNextPhaseText()}
            </div>
            <div className="text-xs text-muted-foreground">
              Ciclo: {cycleCount}
            </div>
          </div>
        )}

        {/* Controles */}
        {showControls && (
          <div className="space-y-4">
            {/* Control de BPM */}
            <div className="flex items-center justify-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBpmChange(bpm - 5)}
                disabled={bpm <= 100}
              >
                -5
              </Button>
              <span className="min-w-[60px] text-center font-mono">
                {bpm} BPM
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBpmChange(bpm + 5)}
                disabled={bpm >= 120}
              >
                +5
              </Button>
            </div>

            {/* Botones de control */}
            <div className="flex justify-center space-x-2">
              <Button
                onClick={handleStartStop}
                variant={isActive ? "destructive" : "default"}
                className="flex items-center space-x-2"
              >
                {isActive ? (
                  <>
                    <Pause className="h-4 w-4" />
                    <span>Detener</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    <span>Iniciar</span>
                  </>
                )}
              </Button>

              {isActive && (
                <Button
                  onClick={handleSync}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  <RotateCcw className="h-4 w-4" />
                  <span>Sincronizar</span>
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Instrucciones */}
        {!isActive && (
          <div className="text-center text-sm text-muted-foreground">
            <p>Metrónomo para RCP a 100-120 compresiones por minuto</p>
            <p className="mt-1">Ritmo 30:2 (30 compresiones, 2 ventilaciones)</p>
          </div>
        )}

        {/* Indicador de cambio de reanimador */}
        {isActive && cycleCount > 0 && cycleCount % 5 === 0 && compressionCount === 0 && (
          <div className="bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-lg p-3 text-center">
            <div className="text-yellow-800 dark:text-yellow-200 font-semibold">
              ⚠️ Cambio de reanimador recomendado
            </div>
            <div className="text-yellow-700 dark:text-yellow-300 text-sm mt-1">
              Han pasado aproximadamente 2 minutos
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default MetronomeDisplay;

