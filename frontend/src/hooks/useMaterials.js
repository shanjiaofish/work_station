import { useCallback } from 'react';
import { useAppContext } from '../context/AppContext';
import MaterialService from '../services/materialService';

export function useMaterials() {
  const { state, actions } = useAppContext();
  const materialService = new MaterialService();

  const searchMaterials = useCallback(async (query, limit = 5) => {
    try {
      actions.setMaterialsLoading(true);
      actions.clearMaterialsError();

      const response = await materialService.searchMaterials(query, limit);
      
      if (response.success) {
        actions.setMaterialSearchResults(response.data || []);
        return response.data || [];
      } else {
        throw new Error(response.message || 'Search failed');
      }
    } catch (error) {
      console.error('Material search error:', error);
      actions.setMaterialsError(error.message);
      actions.addNotification({
        type: 'error',
        title: 'Search Failed',
        message: error.message
      });
      throw error;
    } finally {
      actions.setMaterialsLoading(false);
    }
  }, [actions, materialService]);

  const batchMatchMaterials = useCallback(async (queries) => {
    try {
      actions.setMaterialsLoading(true);
      actions.clearMaterialsError();

      // Try new API first, fallback to legacy
      let results;
      try {
        results = await materialService.batchMatchMaterials(queries);
      } catch (error) {
        console.warn('New API failed, trying legacy:', error.message);
        results = await materialService.legacyBatchMatch(queries);
      }

      actions.setMaterialBatchResults(results);
      
      actions.addNotification({
        type: 'success',
        title: 'Batch Matching Complete',
        message: `Processed ${queries.length} materials successfully`
      });

      return results;
    } catch (error) {
      console.error('Batch matching error:', error);
      actions.setMaterialsError(error.message);
      
      // Return empty results to allow manual selection
      const emptyResults = queries.map(query => ({
        query: query,
        matches: [],
        default: null
      }));
      
      actions.setMaterialBatchResults(emptyResults);
      
      actions.addNotification({
        type: 'warning',
        title: 'Batch Matching Failed',
        message: 'API error occurred. You can still select materials manually.'
      });

      return emptyResults;
    } finally {
      actions.setMaterialsLoading(false);
    }
  }, [actions, materialService]);

  const createMaterial = useCallback(async (materialData) => {
    try {
      actions.setMaterialsLoading(true);
      actions.clearMaterialsError();

      const response = await materialService.createMaterial(materialData);
      
      if (response.success) {
        actions.addNotification({
          type: 'success',
          title: 'Material Created',
          message: `${materialData.material_name} has been created successfully`
        });
        return response.data;
      } else {
        throw new Error(response.message || 'Creation failed');
      }
    } catch (error) {
      console.error('Material creation error:', error);
      actions.setMaterialsError(error.message);
      actions.addNotification({
        type: 'error',
        title: 'Creation Failed',
        message: error.message
      });
      throw error;
    } finally {
      actions.setMaterialsLoading(false);
    }
  }, [actions, materialService]);

  const updateMaterial = useCallback(async (materialId, updateData) => {
    try {
      actions.setMaterialsLoading(true);
      actions.clearMaterialsError();

      const response = await materialService.updateMaterial(materialId, updateData);
      
      if (response.success) {
        actions.addNotification({
          type: 'success',
          title: 'Material Updated',
          message: 'Material has been updated successfully'
        });
        return response.data;
      } else {
        throw new Error(response.message || 'Update failed');
      }
    } catch (error) {
      console.error('Material update error:', error);
      actions.setMaterialsError(error.message);
      actions.addNotification({
        type: 'error',
        title: 'Update Failed',
        message: error.message
      });
      throw error;
    } finally {
      actions.setMaterialsLoading(false);
    }
  }, [actions, materialService]);

  const deleteMaterial = useCallback(async (materialId) => {
    try {
      actions.setMaterialsLoading(true);
      actions.clearMaterialsError();

      const response = await materialService.deleteMaterial(materialId);
      
      if (response.success) {
        actions.addNotification({
          type: 'success',
          title: 'Material Deleted',
          message: 'Material has been deleted successfully'
        });
        return true;
      } else {
        throw new Error(response.message || 'Deletion failed');
      }
    } catch (error) {
      console.error('Material deletion error:', error);
      actions.setMaterialsError(error.message);
      actions.addNotification({
        type: 'error',
        title: 'Deletion Failed',
        message: error.message
      });
      throw error;
    } finally {
      actions.setMaterialsLoading(false);
    }
  }, [actions, materialService]);

  return {
    // State
    materials: state.materials,
    isLoading: state.materials.isSearching,
    error: state.materials.searchError,
    
    // Actions
    searchMaterials,
    batchMatchMaterials,
    createMaterial,
    updateMaterial,
    deleteMaterial,
    
    // Utilities
    clearError: actions.clearMaterialsError
  };
}