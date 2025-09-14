import { apiClient } from './api';

class MaterialService {
  
  // Search materials by query
  async searchMaterials(query, limit = 5) {
    if (!query || query.trim() === '') {
      throw new Error('Search query cannot be empty');
    }

    const response = await apiClient.get('/api/materials/search', {
      params: { q: query.trim(), limit }
    });
    
    // Handle new response format with success/data structure
    if (response.data.success) {
      return response.data.data;
    } else {
      throw new Error(response.data.error || 'Search failed');
    }
  }

  // Batch match materials
  async batchMatchMaterials(queries) {
    if (!queries || !Array.isArray(queries) || queries.length === 0) {
      throw new Error('Queries array is required for batch matching');
    }

    // Clean queries
    const cleanQueries = queries
      .filter(q => q && typeof q === 'string' && q.trim() !== '')
      .map(q => q.trim());

    if (cleanQueries.length === 0) {
      throw new Error('No valid queries provided');
    }

    const response = await apiClient.post('/api/materials/match-batch', {
      queries: cleanQueries
    });
    
    // Handle new response format with success/data structure
    if (response.data.success) {
      return response.data.data;
    } else {
      throw new Error(response.data.error || 'Batch match failed');
    }
  }

  // Create new material
  async createMaterial(materialData) {
    if (!materialData) {
      throw new Error('Material data is required');
    }

    // Validate required fields
    const requiredFields = ['material_name', 'carbon_footprint', 'declaration_unit'];
    for (const field of requiredFields) {
      if (!materialData[field]) {
        throw new Error(`${field} is required`);
      }
    }

    const response = await apiClient.post('/api/materials', materialData);
    
    // Handle new response format with success/data structure
    if (response.data.success) {
      return response.data;
    } else {
      throw new Error(response.data.error || 'Creation failed');
    }
  }

  // Get material by ID
  async getMaterialById(materialId) {
    if (!materialId) {
      throw new Error('Material ID is required');
    }

    const response = await apiClient.get(`/api/materials/${materialId}`);
    
    // Handle new response format with success/data structure
    if (response.data.success) {
      return response.data;
    } else {
      throw new Error(response.data.error || 'Failed to get material');
    }
  }

  // Update material
  async updateMaterial(materialId, updateData) {
    if (!materialId) {
      throw new Error('Material ID is required');
    }
    
    if (!updateData || Object.keys(updateData).length === 0) {
      throw new Error('Update data is required');
    }

    const response = await apiClient.put(`/api/materials/${materialId}`, updateData);
    
    // Handle new response format with success/data structure
    if (response.data.success) {
      return response.data;
    } else {
      throw new Error(response.data.error || 'Update failed');
    }
  }

  // Delete material
  async deleteMaterial(materialId) {
    if (!materialId) {
      throw new Error('Material ID is required');
    }

    const response = await apiClient.delete(`/api/materials/${materialId}`);
    
    // Handle new response format with success/data structure
    if (response.data.success) {
      return response.data;
    } else {
      throw new Error(response.data.error || 'Deletion failed');
    }
  }

  // Legacy method for backward compatibility
  async legacyBatchMatch(queries) {
    try {
      // Try new API first
      return await this.batchMatchMaterials(queries);
    } catch (error) {
      console.warn('New API failed, trying legacy endpoint:', error.message);
      
      // Fallback to legacy endpoint
      const response = await apiClient.post('/materials/match-batch', { queries });
      
      // Handle response format (legacy might have different format)
      if (response.data.success) {
        return response.data.data;
      } else if (Array.isArray(response.data)) {
        // Legacy format - direct array return
        return response.data;
      } else {
        throw new Error(response.data.error || 'Legacy batch match failed');
      }
    }
  }
}

export default MaterialService;