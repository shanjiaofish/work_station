import { apiClient } from './api';

class OCRService {
  
  // Process PDF file with OCR
  async processPDF(file, onProgress = null) {
    if (!file) {
      throw new Error('PDF file is required');
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      throw new Error('File must be a PDF');
    }

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    // Configure request with progress tracking
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5 minutes for OCR processing
    };

    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress({ phase: 'uploading', progress: percentCompleted });
      };
    }

    const response = await apiClient.post('/api/ocr/process-pdf', formData, config);
    return response.data;
  }

  // Get OCR processing status
  async getStatus() {
    const response = await apiClient.get('/api/ocr/status');
    return response.data;
  }

  // List available OCR reports
  async getReports() {
    const response = await apiClient.get('/api/ocr/reports');
    return response.data;
  }

  // Download OCR report
  async downloadReport(filename) {
    if (!filename) {
      throw new Error('Report filename is required');
    }

    const response = await apiClient.get(`/api/ocr/download-report/${filename}`, {
      responseType: 'blob'
    });

    // Create download link
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Validate file before processing
  validateFile(file) {
    const errors = [];

    if (!file) {
      errors.push('No file provided');
      return { isValid: false, errors };
    }

    // Check file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      errors.push('File must be a PDF');
    }

    // Check file size (16MB limit)
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
      errors.push('File size must be less than 16MB');
    }

    // Check file name
    if (file.name.length > 255) {
      errors.push('File name is too long');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // Get supported file formats and limits
  getSupportedFormats() {
    return {
      formats: ['.pdf'],
      maxFileSize: '16MB',
      maxFiles: 1,
      description: 'PDF files containing invoice images'
    };
  }
}

export default OCRService;