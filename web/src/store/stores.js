import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Store para el triaje
export const useTriageStore = create((set, get) => ({
  currentTriage: null,
  triageHistory: [],
  isLoading: false,
  error: null,

  setTriage: (triage) => set({ currentTriage: triage }),
  
  addToHistory: (triage) => set((state) => ({
    triageHistory: [triage, ...state.triageHistory.slice(0, 9)] // Mantener últimos 10
  })),
  
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  
  clearTriage: () => set({ 
    currentTriage: null, 
    error: null 
  }),

  reset: () => set({
    currentTriage: null,
    triageHistory: [],
    isLoading: false,
    error: null
  })
}));

// Store para protocolos
export const useProtocolStore = create((set, get) => ({
  activeProtocol: null,
  currentStep: 0,
  stepHistory: [],
  userResponses: [],
  isPlaying: false,
  isLoading: false,
  error: null,

  setActiveProtocol: (protocol) => set({ 
    activeProtocol: protocol,
    currentStep: 0,
    stepHistory: [],
    userResponses: []
  }),

  setCurrentStep: (step) => set({ currentStep: step }),
  
  addToStepHistory: (stepIndex) => set((state) => ({
    stepHistory: [...state.stepHistory, stepIndex]
  })),

  addUserResponse: (response) => set((state) => ({
    userResponses: [...state.userResponses, response]
  })),

  setPlaying: (playing) => set({ isPlaying: playing }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),

  nextStep: () => set((state) => ({
    currentStep: state.currentStep + 1
  })),

  previousStep: () => set((state) => ({
    currentStep: Math.max(0, state.currentStep - 1)
  })),

  reset: () => set({
    activeProtocol: null,
    currentStep: 0,
    stepHistory: [],
    userResponses: [],
    isPlaying: false,
    isLoading: false,
    error: null
  })
}));

// Store para voz
export const useVoiceStore = create(
  persist(
    (set, get) => ({
      isListening: false,
      isSpeaking: false,
      isSupported: false,
      voiceEnabled: true,
      speechRate: 1.0,
      speechPitch: 1.0,
      selectedVoice: null,
      availableVoices: [],
      lastTranscript: '',
      error: null,

      setListening: (listening) => set({ isListening: listening }),
      setSpeaking: (speaking) => set({ isSpeaking: speaking }),
      setSupported: (supported) => set({ isSupported: supported }),
      setVoiceEnabled: (enabled) => set({ voiceEnabled: enabled }),
      setSpeechRate: (rate) => set({ speechRate: rate }),
      setSpeechPitch: (pitch) => set({ speechPitch: pitch }),
      setSelectedVoice: (voice) => set({ selectedVoice: voice }),
      setAvailableVoices: (voices) => set({ availableVoices: voices }),
      setLastTranscript: (transcript) => set({ lastTranscript: transcript }),
      setError: (error) => set({ error }),

      toggleVoice: () => set((state) => ({ 
        voiceEnabled: !state.voiceEnabled 
      })),

      reset: () => set({
        isListening: false,
        isSpeaking: false,
        lastTranscript: '',
        error: null
      })
    }),
    {
      name: 'conrumbo-voice-settings',
      partialize: (state) => ({
        voiceEnabled: state.voiceEnabled,
        speechRate: state.speechRate,
        speechPitch: state.speechPitch,
        selectedVoice: state.selectedVoice
      })
    }
  )
);

// Store para configuración de la app
export const useAppStore = create(
  persist(
    (set, get) => ({
      isOnline: navigator.onLine,
      theme: 'light',
      fontSize: 'normal',
      highContrast: false,
      handsFreeModeEnabled: false,
      emergencyContactsEnabled: false,
      notificationsEnabled: false,
      installPromptEvent: null,
      isInstalled: false,

      setOnline: (online) => set({ isOnline: online }),
      setTheme: (theme) => set({ theme }),
      setFontSize: (size) => set({ fontSize: size }),
      setHighContrast: (enabled) => set({ highContrast: enabled }),
      setHandsFreeMode: (enabled) => set({ handsFreeModeEnabled: enabled }),
      setEmergencyContacts: (enabled) => set({ emergencyContactsEnabled: enabled }),
      setNotifications: (enabled) => set({ notificationsEnabled: enabled }),
      setInstallPrompt: (event) => set({ installPromptEvent: event }),
      setInstalled: (installed) => set({ isInstalled: installed }),

      toggleTheme: () => set((state) => ({
        theme: state.theme === 'light' ? 'dark' : 'light'
      })),

      toggleHighContrast: () => set((state) => ({
        highContrast: !state.highContrast
      })),

      reset: () => set({
        theme: 'light',
        fontSize: 'normal',
        highContrast: false,
        handsFreeModeEnabled: false,
        emergencyContactsEnabled: false,
        notificationsEnabled: false
      })
    }),
    {
      name: 'conrumbo-app-settings',
      partialize: (state) => ({
        theme: state.theme,
        fontSize: state.fontSize,
        highContrast: state.highContrast,
        handsFreeModeEnabled: state.handsFreeModeEnabled,
        emergencyContactsEnabled: state.emergencyContactsEnabled,
        notificationsEnabled: state.notificationsEnabled
      })
    }
  )
);

// Store para el metrónomo RCP
export const useMetronomeStore = create((set, get) => ({
  isActive: false,
  bpm: 110,
  currentBeat: 0,
  cycleCount: 0,
  compressionCount: 0,
  ventilationCount: 0,
  isCompressionPhase: true,
  audioContext: null,
  oscillator: null,

  setBpm: (bpm) => set({ bpm: Math.max(100, Math.min(120, bpm)) }),
  setActive: (active) => set({ isActive: active }),
  setCurrentBeat: (beat) => set({ currentBeat: beat }),
  setCycleCount: (count) => set({ cycleCount: count }),
  setCompressionCount: (count) => set({ compressionCount: count }),
  setVentilationCount: (count) => set({ ventilationCount: count }),
  setCompressionPhase: (phase) => set({ isCompressionPhase: phase }),
  setAudioContext: (context) => set({ audioContext: context }),
  setOscillator: (oscillator) => set({ oscillator }),

  incrementBeat: () => set((state) => ({
    currentBeat: state.currentBeat + 1
  })),

  incrementCompression: () => set((state) => {
    const newCount = state.compressionCount + 1;
    if (newCount >= 30) {
      return {
        compressionCount: 0,
        ventilationCount: 0,
        isCompressionPhase: false,
        cycleCount: state.cycleCount + 1
      };
    }
    return { compressionCount: newCount };
  }),

  incrementVentilation: () => set((state) => {
    const newCount = state.ventilationCount + 1;
    if (newCount >= 2) {
      return {
        ventilationCount: 0,
        isCompressionPhase: true
      };
    }
    return { ventilationCount: newCount };
  }),

  reset: () => set({
    isActive: false,
    currentBeat: 0,
    cycleCount: 0,
    compressionCount: 0,
    ventilationCount: 0,
    isCompressionPhase: true
  }),

  stop: () => {
    const { oscillator, audioContext } = get();
    if (oscillator) {
      oscillator.stop();
      oscillator.disconnect();
    }
    if (audioContext) {
      audioContext.close();
    }
    set({
      isActive: false,
      audioContext: null,
      oscillator: null
    });
  }
}));

