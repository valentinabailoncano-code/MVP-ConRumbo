const API_BASE_URL = 'http://localhost:8000/api/conrumbo';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Triaje
  async submitTriage(triageData) {
    return this.request('/triage', {
      method: 'POST',
      body: JSON.stringify(triageData),
    });
  }

  // Protocolos
  async getNextStep(stepData) {
    return this.request('/next_step', {
      method: 'POST',
      body: JSON.stringify(stepData),
    });
  }

  async getProtocol(protocolId) {
    return this.request(`/protocol/${protocolId}`);
  }

  async listProtocols() {
    return this.request('/protocols');
  }

  // Búsqueda
  async search(query, context = null) {
    return this.request('/search', {
      method: 'POST',
      body: JSON.stringify({ query, context }),
    });
  }

  // Sesión
  async resetSession() {
    return this.request('/session/reset', {
      method: 'POST',
    });
  }

  async getSessionStatus() {
    return this.request('/session/status');
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

export const apiClient = new ApiClient();

// Funciones de utilidad para manejo de errores
export const handleApiError = (error) => {
  console.error('API Error:', error);
  
  if (error.message.includes('Failed to fetch')) {
    return {
      type: 'network',
      message: 'Sin conexión a internet. Usando modo offline.',
      offline: true
    };
  }
  
  if (error.message.includes('Consulta no permitida')) {
    return {
      type: 'safety',
      message: error.message,
      safety: true
    };
  }
  
  return {
    type: 'general',
    message: error.message || 'Error desconocido',
    offline: false
  };
};

// Cache para modo offline
class OfflineCache {
  constructor() {
    this.cache = new Map();
    this.loadFromStorage();
  }

  set(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
    this.saveToStorage();
  }

  get(key, maxAge = 24 * 60 * 60 * 1000) { // 24 horas por defecto
    const item = this.cache.get(key);
    if (!item) return null;
    
    if (Date.now() - item.timestamp > maxAge) {
      this.cache.delete(key);
      this.saveToStorage();
      return null;
    }
    
    return item.data;
  }

  has(key) {
    return this.cache.has(key);
  }

  clear() {
    this.cache.clear();
    this.saveToStorage();
  }

  loadFromStorage() {
    try {
      const stored = localStorage.getItem('conrumbo-offline-cache');
      if (stored) {
        const data = JSON.parse(stored);
        this.cache = new Map(data);
      }
    } catch (error) {
      console.error('Error loading offline cache:', error);
    }
  }

  saveToStorage() {
    try {
      const data = Array.from(this.cache.entries());
      localStorage.setItem('conrumbo-offline-cache', JSON.stringify(data));
    } catch (error) {
      console.error('Error saving offline cache:', error);
    }
  }
}

export const offlineCache = new OfflineCache();

// Cliente API con soporte offline
export class OfflineApiClient extends ApiClient {
  async request(endpoint, options = {}) {
    const cacheKey = `${endpoint}-${JSON.stringify(options.body || {})}`;
    
    try {
      // Intentar request normal
      const response = await super.request(endpoint, options);
      
      // Cachear respuestas exitosas para protocolos críticos
      if (endpoint.includes('/protocol/') || endpoint.includes('/triage')) {
        offlineCache.set(cacheKey, response);
      }
      
      return response;
    } catch (error) {
      // Si falla, intentar usar cache offline
      const cachedResponse = offlineCache.get(cacheKey);
      
      if (cachedResponse) {
        console.log('Using offline cache for:', endpoint);
        return {
          ...cachedResponse,
          _offline: true,
          _cached: true
        };
      }
      
      // Si no hay cache, usar fallbacks para protocolos críticos
      if (endpoint.includes('/protocol/')) {
        return this.getOfflineProtocolFallback(endpoint);
      }
      
      throw error;
    }
  }

  getOfflineProtocolFallback(endpoint) {
    const protocolId = endpoint.split('/').pop();
    
    // Fallbacks básicos para protocolos críticos
    const fallbacks = {
      'pa_rcp_adulto_v1': {
        id: 'pa_rcp_adulto_v1',
        title: 'RCP Adulto (Modo Offline)',
        steps: [
          {
            id: 1,
            instruction: 'Verificar conciencia y respiración',
            voice_cue: 'Toque los hombros y grite: ¿Está bien?',
            ui: { timer: false, next_button: true }
          },
          {
            id: 2,
            instruction: 'Llamar al 112 y pedir DEA',
            voice_cue: 'Llame al 112 inmediatamente',
            ui: { timer: false, next_button: true }
          },
          {
            id: 3,
            instruction: 'Iniciar compresiones torácicas 30:2',
            voice_cue: 'Coloque las manos en el centro del pecho y comprima fuerte y rápido',
            ui: { timer: true, timer_duration: 18, next_button: false }
          }
        ],
        _offline: true,
        _fallback: true
      },
      'pa_asfixia_adulto_v1': {
        id: 'pa_asfixia_adulto_v1',
        title: 'Atragantamiento Adulto (Modo Offline)',
        steps: [
          {
            id: 1,
            instruction: 'Evaluar si puede toser',
            voice_cue: '¿Puede toser? Si puede, anímelo a toser fuerte',
            ui: { timer: false, next_button: true }
          },
          {
            id: 2,
            instruction: '5 golpes interescapulares',
            voice_cue: 'Incline hacia adelante y dé 5 golpes firmes entre los omóplatos',
            ui: { timer: true, timer_duration: 10, next_button: true }
          },
          {
            id: 3,
            instruction: '5 compresiones abdominales',
            voice_cue: 'Maniobra de Heimlich: 5 compresiones hacia arriba en el abdomen',
            ui: { timer: true, timer_duration: 10, next_button: true }
          }
        ],
        _offline: true,
        _fallback: true
      }
    };

    const fallback = fallbacks[protocolId];
    if (fallback) {
      return fallback;
    }

    throw new Error('Protocolo no disponible offline');
  }
}

export const offlineApiClient = new OfflineApiClient();

