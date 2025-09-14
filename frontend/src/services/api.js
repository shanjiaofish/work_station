import axios from 'axios';
import { API_BASE } from '../api/config';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    
    // Handle common error responses
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          throw new Error(data?.error || 'Invalid request');
        case 404:
          throw new Error(data?.error || 'Resource not found');
        case 500:
          throw new Error(data?.error || 'Server error occurred');
        default:
          throw new Error(data?.error || `HTTP ${status} error`);
      }
    } else if (error.request) {
      throw new Error('Network error - please check your connection');
    } else {
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }
);

// API Service class
class APIService {
  
  // Health check
  async healthCheck() {
    const response = await apiClient.get('/api/general/health');
    return response.data;
  }

  // Test connection
  async testConnection() {
    const response = await apiClient.get('/api/general/hello');
    return response.data;
  }

  // Get service info
  async getServiceInfo() {
    const response = await apiClient.get('/api/general/info');
    return response.data;
  }
}

export default APIService;
export { apiClient };