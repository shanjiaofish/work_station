import { apiClient } from './api';

class GMapService {
  
  // Process Google Maps routes
  async processRoutes(origin, destinations, onProgress = null) {
    if (!origin || origin.trim() === '') {
      throw new Error('Origin location is required');
    }

    if (!destinations || destinations.trim() === '') {
      throw new Error('At least one destination is required');
    }

    // Clean and validate destinations
    const destinationList = destinations
      .split('\n')
      .map(dest => dest.trim())
      .filter(dest => dest !== '');

    if (destinationList.length === 0) {
      throw new Error('No valid destinations provided');
    }

    const requestData = {
      origin: origin.trim(),
      destinations: destinations.trim()
    };

    const config = {
      timeout: 300000, // 5 minutes for route processing
    };

    if (onProgress) {
      onProgress({ phase: 'processing', progress: 0, message: 'Starting route processing...' });
    }

    const response = await apiClient.post('/api/gmap/process', requestData, config);
    
    if (onProgress) {
      onProgress({ phase: 'completed', progress: 100, message: 'Route processing completed' });
    }

    return response.data;
  }

  // Validate locations
  async validateLocations(locations) {
    if (!locations || !Array.isArray(locations) || locations.length === 0) {
      throw new Error('Locations array is required');
    }

    const cleanLocations = locations
      .filter(loc => loc && typeof loc === 'string' && loc.trim() !== '')
      .map(loc => loc.trim());

    if (cleanLocations.length === 0) {
      throw new Error('No valid locations provided');
    }

    const response = await apiClient.post('/api/gmap/validate-locations', {
      locations: cleanLocations
    });

    return response.data;
  }

  // Geocode address
  async geocodeAddress(address) {
    if (!address || address.trim() === '') {
      throw new Error('Address is required for geocoding');
    }

    const response = await apiClient.get('/api/gmap/geocode', {
      params: { address: address.trim() }
    });

    return response.data;
  }

  // Download Excel report
  async downloadExcelReport(sessionId) {
    if (!sessionId) {
      throw new Error('Session ID is required');
    }

    const response = await apiClient.get(`/api/gmap/download/excel/${sessionId}`, {
      responseType: 'blob'
    });

    // Create download link
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `google_maps_report_${sessionId}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Download ZIP of images
  async downloadImageZip(sessionId) {
    if (!sessionId) {
      throw new Error('Session ID is required');
    }

    const response = await apiClient.get(`/api/gmap/download/zip/${sessionId}`, {
      responseType: 'blob'
    });

    // Create download link
    const blob = new Blob([response.data], {
      type: 'application/zip'
    });
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `map_images_${sessionId}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Get active sessions
  async getSessions() {
    const response = await apiClient.get('/api/gmap/sessions');
    return response.data;
  }

  // Parse destinations text
  parseDestinations(destinationsText) {
    if (!destinationsText) return [];
    
    return destinationsText
      .split('\n')
      .map(dest => dest.trim())
      .filter(dest => dest !== '');
  }

  // Validate route data
  validateRouteData(origin, destinations) {
    const errors = [];

    if (!origin || origin.trim() === '') {
      errors.push('Origin location is required');
    }

    if (!destinations || destinations.trim() === '') {
      errors.push('At least one destination is required');
    } else {
      const destList = this.parseDestinations(destinations);
      if (destList.length === 0) {
        errors.push('No valid destinations found');
      } else if (destList.length > 20) {
        errors.push('Maximum 20 destinations allowed');
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // Get supported features
  getSupportedFeatures() {
    return {
      maxDestinations: 20,
      supportedLanguages: ['zh-TW', 'en'],
      outputFormats: ['excel', 'zip'],
      features: [
        'Route distance calculation',
        'Screenshot generation',
        'Batch processing',
        'Export to Excel',
        'Download route images'
      ]
    };
  }
}

export default GMapService;