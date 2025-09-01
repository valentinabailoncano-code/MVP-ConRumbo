import { useMetronomeStore } from './stores';

class MetronomeManager {
  constructor() {
    this.audioContext = null;
    this.oscillator = null;
    this.gainNode = null;
    this.intervalId = null;
    this.isInitialized = false;
  }

  async init() {
    if (this.isInitialized) return;

    try {
      // Crear contexto de audio
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      
      // Crear nodo de ganancia para controlar volumen
      this.gainNode = this.audioContext.createGain();
      this.gainNode.connect(this.audioContext.destination);
      this.gainNode.gain.value = 0.3; // Volumen moderado

      useMetronomeStore.getState().setAudioContext(this.audioContext);
      this.isInitialized = true;
      
      console.log('Metrónomo inicializado');
    } catch (error) {
      console.error('Error inicializando metrónomo:', error);
      throw error;
    }
  }

  async start() {
    if (!this.isInitialized) {
      await this.init();
    }

    const store = useMetronomeStore.getState();
    
    if (store.isActive) {
      console.log('Metrónomo ya está activo');
      return;
    }

    // Reanudar contexto de audio si está suspendido
    if (this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
    }

    store.setActive(true);
    store.reset();

    const interval = 60000 / store.bpm; // Intervalo en ms

    this.intervalId = setInterval(() => {
      this.playBeat();
      this.updateCycle();
    }, interval);

    console.log(`Metrónomo iniciado a ${store.bpm} BPM`);
  }

  stop() {
    const store = useMetronomeStore.getState();
    
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    store.stop();
    console.log('Metrónomo detenido');
  }

  playBeat() {
    if (!this.audioContext || !this.gainNode) return;

    const store = useMetronomeStore.getState();
    
    try {
      // Crear oscilador para el sonido
      const oscillator = this.audioContext.createOscillator();
      const beatGain = this.audioContext.createGain();

      oscillator.connect(beatGain);
      beatGain.connect(this.gainNode);

      // Configurar frecuencia según el tipo de beat
      if (store.isCompressionPhase) {
        // Sonido más agudo para compresiones
        oscillator.frequency.setValueAtTime(800, this.audioContext.currentTime);
        beatGain.gain.setValueAtTime(0.4, this.audioContext.currentTime);
      } else {
        // Sonido más grave para ventilaciones
        oscillator.frequency.setValueAtTime(400, this.audioContext.currentTime);
        beatGain.gain.setValueAtTime(0.6, this.audioContext.currentTime);
      }

      oscillator.type = 'sine';

      // Envelope para el sonido
      const now = this.audioContext.currentTime;
      beatGain.gain.setValueAtTime(0, now);
      beatGain.gain.linearRampToValueAtTime(beatGain.gain.value, now + 0.01);
      beatGain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);

      oscillator.start(now);
      oscillator.stop(now + 0.1);

      // Vibración en dispositivos móviles
      if ('vibrate' in navigator) {
        if (store.isCompressionPhase) {
          navigator.vibrate(50); // Vibración corta para compresiones
        } else {
          navigator.vibrate([100, 50, 100]); // Patrón para ventilaciones
        }
      }

    } catch (error) {
      console.error('Error reproduciendo beat:', error);
    }
  }

  updateCycle() {
    const store = useMetronomeStore.getState();
    
    store.incrementBeat();

    if (store.isCompressionPhase) {
      store.incrementCompression();
      
      // Después de 30 compresiones, cambiar a ventilaciones
      if (store.compressionCount >= 30) {
        store.setCompressionPhase(false);
        
        // Anuncio de voz para ventilaciones
        this.announcePhase('ventilaciones');
      }
    } else {
      store.incrementVentilation();
      
      // Después de 2 ventilaciones, volver a compresiones
      if (store.ventilationCount >= 2) {
        store.setCompressionPhase(true);
        
        // Anuncio de voz para compresiones
        this.announcePhase('compresiones');
      }
    }

    // Anunciar cambio de reanimador cada 2 minutos (aproximadamente 5 ciclos)
    if (store.cycleCount > 0 && store.cycleCount % 5 === 0 && store.compressionCount === 0) {
      this.announcePhase('cambio_reanimador');
    }
  }

  announcePhase(phase) {
    // Importar speechManager dinámicamente para evitar dependencias circulares
    import('./speech.js').then(({ speechManager }) => {
      const messages = {
        'compresiones': '30 compresiones',
        'ventilaciones': '2 ventilaciones',
        'cambio_reanimador': 'Cambio de reanimador'
      };

      const message = messages[phase];
      if (message && speechManager) {
        speechManager.announce(message, 'urgent').catch(console.error);
      }
    }).catch(console.error);
  }

  setBpm(newBpm) {
    const store = useMetronomeStore.getState();
    const clampedBpm = Math.max(100, Math.min(120, newBpm));
    
    store.setBpm(clampedBpm);

    // Si está activo, reiniciar con nuevo BPM
    if (store.isActive) {
      this.stop();
      setTimeout(() => this.start(), 100);
    }
  }

  // Método para sincronizar con instructor externo
  sync() {
    const store = useMetronomeStore.getState();
    
    if (!store.isActive) return;

    // Reiniciar el ciclo actual
    store.setCurrentBeat(0);
    store.setCompressionCount(0);
    store.setVentilationCount(0);
    store.setCompressionPhase(true);

    console.log('Metrónomo sincronizado');
  }

  // Obtener estado actual
  getStatus() {
    const store = useMetronomeStore.getState();
    
    return {
      isActive: store.isActive,
      bpm: store.bpm,
      currentBeat: store.currentBeat,
      cycleCount: store.cycleCount,
      compressionCount: store.compressionCount,
      ventilationCount: store.ventilationCount,
      isCompressionPhase: store.isCompressionPhase,
      nextPhase: store.isCompressionPhase ? 
        `${30 - store.compressionCount} compresiones restantes` :
        `${2 - store.ventilationCount} ventilaciones restantes`
    };
  }

  // Limpiar recursos
  cleanup() {
    this.stop();
    
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    
    this.gainNode = null;
    this.isInitialized = false;
  }
}

// Instancia singleton
export const metronomeManager = new MetronomeManager();

// Hook personalizado para usar el metrónomo
export const useMetronome = () => {
  const metronomeStore = useMetronomeStore();

  return {
    ...metronomeStore,
    start: metronomeManager.start.bind(metronomeManager),
    stop: metronomeManager.stop.bind(metronomeManager),
    setBpm: metronomeManager.setBpm.bind(metronomeManager),
    sync: metronomeManager.sync.bind(metronomeManager),
    getStatus: metronomeManager.getStatus.bind(metronomeManager),
    cleanup: metronomeManager.cleanup.bind(metronomeManager)
  };
};

