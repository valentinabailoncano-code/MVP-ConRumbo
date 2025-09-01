import { useVoiceStore } from './stores';

class SpeechManager {
  constructor() {
    this.synthesis = null;
    this.recognition = null;
    this.isInitialized = false;
    this.currentUtterance = null;
    this.recognitionTimeout = null;
    
    this.init();
  }

  init() {
    // Verificar soporte del navegador
    const hasWebSpeech = 'speechSynthesis' in window && 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
    
    if (!hasWebSpeech) {
      console.warn('Web Speech API no soportada');
      useVoiceStore.getState().setSupported(false);
      return;
    }

    // Inicializar síntesis de voz
    this.synthesis = window.speechSynthesis;
    
    // Inicializar reconocimiento de voz
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    
    this.setupRecognition();
    this.loadVoices();
    
    useVoiceStore.getState().setSupported(true);
    this.isInitialized = true;
  }

  setupRecognition() {
    if (!this.recognition) return;

    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = 'es-ES';
    this.recognition.maxAlternatives = 1;

    this.recognition.onstart = () => {
      console.log('Reconocimiento de voz iniciado');
      useVoiceStore.getState().setListening(true);
      useVoiceStore.getState().setError(null);
    };

    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      console.log('Transcripción:', transcript);
      useVoiceStore.getState().setLastTranscript(transcript);
      
      // Disparar evento personalizado con la transcripción
      window.dispatchEvent(new CustomEvent('speechResult', { 
        detail: { transcript } 
      }));
    };

    this.recognition.onerror = (event) => {
      console.error('Error en reconocimiento de voz:', event.error);
      useVoiceStore.getState().setError(`Error de reconocimiento: ${event.error}`);
      useVoiceStore.getState().setListening(false);
    };

    this.recognition.onend = () => {
      console.log('Reconocimiento de voz terminado');
      useVoiceStore.getState().setListening(false);
      
      if (this.recognitionTimeout) {
        clearTimeout(this.recognitionTimeout);
        this.recognitionTimeout = null;
      }
    };
  }

  loadVoices() {
    if (!this.synthesis) return;

    const updateVoices = () => {
      const voices = this.synthesis.getVoices();
      const spanishVoices = voices.filter(voice => 
        voice.lang.startsWith('es') || voice.lang.includes('ES')
      );
      
      useVoiceStore.getState().setAvailableVoices(spanishVoices);
      
      // Seleccionar voz por defecto si no hay una seleccionada
      const currentVoice = useVoiceStore.getState().selectedVoice;
      if (!currentVoice && spanishVoices.length > 0) {
        // Preferir voces locales
        const localVoice = spanishVoices.find(voice => voice.localService) || spanishVoices[0];
        useVoiceStore.getState().setSelectedVoice(localVoice);
      }
    };

    // Las voces pueden no estar disponibles inmediatamente
    if (this.synthesis.getVoices().length > 0) {
      updateVoices();
    } else {
      this.synthesis.onvoiceschanged = updateVoices;
    }
  }

  speak(text, options = {}) {
    if (!this.synthesis || !this.isInitialized) {
      console.warn('Síntesis de voz no disponible');
      return Promise.reject(new Error('Síntesis de voz no disponible'));
    }

    const voiceStore = useVoiceStore.getState();
    
    if (!voiceStore.voiceEnabled) {
      console.log('Voz deshabilitada por el usuario');
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      // Cancelar síntesis anterior
      this.stopSpeaking();

      const utterance = new SpeechSynthesisUtterance(text);
      
      // Configurar voz
      if (voiceStore.selectedVoice) {
        utterance.voice = voiceStore.selectedVoice;
      }
      
      utterance.rate = options.rate || voiceStore.speechRate;
      utterance.pitch = options.pitch || voiceStore.speechPitch;
      utterance.volume = options.volume || 1.0;

      utterance.onstart = () => {
        console.log('Síntesis iniciada:', text);
        voiceStore.setSpeaking(true);
        voiceStore.setError(null);
      };

      utterance.onend = () => {
        console.log('Síntesis terminada');
        voiceStore.setSpeaking(false);
        this.currentUtterance = null;
        resolve();
      };

      utterance.onerror = (event) => {
        console.error('Error en síntesis:', event.error);
        voiceStore.setError(`Error de síntesis: ${event.error}`);
        voiceStore.setSpeaking(false);
        this.currentUtterance = null;
        reject(new Error(event.error));
      };

      this.currentUtterance = utterance;
      this.synthesis.speak(utterance);
    });
  }

  stopSpeaking() {
    if (this.synthesis) {
      this.synthesis.cancel();
      useVoiceStore.getState().setSpeaking(false);
      this.currentUtterance = null;
    }
  }

  startListening(timeout = 10000) {
    if (!this.recognition || !this.isInitialized) {
      console.warn('Reconocimiento de voz no disponible');
      return Promise.reject(new Error('Reconocimiento de voz no disponible'));
    }

    const voiceStore = useVoiceStore.getState();
    
    if (!voiceStore.voiceEnabled) {
      console.log('Voz deshabilitada por el usuario');
      return Promise.reject(new Error('Voz deshabilitada'));
    }

    return new Promise((resolve, reject) => {
      // Configurar timeout
      this.recognitionTimeout = setTimeout(() => {
        this.stopListening();
        reject(new Error('Timeout de reconocimiento'));
      }, timeout);

      // Escuchar resultado
      const handleResult = (event) => {
        window.removeEventListener('speechResult', handleResult);
        if (this.recognitionTimeout) {
          clearTimeout(this.recognitionTimeout);
          this.recognitionTimeout = null;
        }
        resolve(event.detail.transcript);
      };

      window.addEventListener('speechResult', handleResult);

      try {
        this.recognition.start();
      } catch (error) {
        window.removeEventListener('speechResult', handleResult);
        if (this.recognitionTimeout) {
          clearTimeout(this.recognitionTimeout);
          this.recognitionTimeout = null;
        }
        reject(error);
      }
    });
  }

  stopListening() {
    if (this.recognition) {
      this.recognition.stop();
      useVoiceStore.getState().setListening(false);
      
      if (this.recognitionTimeout) {
        clearTimeout(this.recognitionTimeout);
        this.recognitionTimeout = null;
      }
    }
  }

  // Método para conversación interactiva
  async askAndListen(question, timeout = 10000) {
    try {
      // Hablar la pregunta
      await this.speak(question);
      
      // Esperar un momento antes de empezar a escuchar
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Escuchar respuesta
      const response = await this.startListening(timeout);
      
      return response;
    } catch (error) {
      console.error('Error en conversación:', error);
      throw error;
    }
  }

  // Método para anuncios importantes
  async announce(text, priority = 'normal') {
    const options = {};
    
    if (priority === 'urgent') {
      options.rate = 1.2;
      options.pitch = 1.1;
      options.volume = 1.0;
    } else if (priority === 'calm') {
      options.rate = 0.9;
      options.pitch = 0.9;
    }

    return this.speak(text, options);
  }

  // Verificar si está ocupado
  isBusy() {
    const voiceStore = useVoiceStore.getState();
    return voiceStore.isSpeaking || voiceStore.isListening;
  }

  // Limpiar recursos
  cleanup() {
    this.stopSpeaking();
    this.stopListening();
    
    if (this.recognitionTimeout) {
      clearTimeout(this.recognitionTimeout);
      this.recognitionTimeout = null;
    }
  }
}

// Instancia singleton
export const speechManager = new SpeechManager();

// Hook personalizado para usar el speech manager
export const useSpeech = () => {
  const voiceStore = useVoiceStore();

  return {
    ...voiceStore,
    speak: speechManager.speak.bind(speechManager),
    stopSpeaking: speechManager.stopSpeaking.bind(speechManager),
    startListening: speechManager.startListening.bind(speechManager),
    stopListening: speechManager.stopListening.bind(speechManager),
    askAndListen: speechManager.askAndListen.bind(speechManager),
    announce: speechManager.announce.bind(speechManager),
    isBusy: speechManager.isBusy.bind(speechManager),
    cleanup: speechManager.cleanup.bind(speechManager)
  };
};

