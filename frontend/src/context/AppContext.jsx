import React, { createContext, useContext, useReducer, useEffect } from 'react';
import APIService from '../services/api';

// Initial state
const initialState = {
  // App state
  isLoading: false,
  error: null,
  
  // Service status
  serviceStatus: {
    api: 'unknown',
    database: 'unknown',
    ocr: 'unknown',
    googleMaps: 'unknown'
  },
  
  // Materials state
  materials: {
    searchResults: [],
    batchResults: [],
    isSearching: false,
    searchError: null
  },
  
  // OCR state
  ocr: {
    isProcessing: false,
    currentFile: null,
    results: null,
    reports: [],
    progress: null,
    error: null
  },
  
  // Google Maps state
  gmap: {
    isProcessing: false,
    currentSession: null,
    results: [],
    sessions: [],
    error: null
  },
  
  // UI state
  ui: {
    currentPage: 'carbon-match',
    notifications: [],
    theme: 'light'
  }
};

// Action types
const actionTypes = {
  // Global actions
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  UPDATE_SERVICE_STATUS: 'UPDATE_SERVICE_STATUS',
  
  // Material actions
  SET_MATERIALS_LOADING: 'SET_MATERIALS_LOADING',
  SET_MATERIAL_SEARCH_RESULTS: 'SET_MATERIAL_SEARCH_RESULTS',
  SET_MATERIAL_BATCH_RESULTS: 'SET_MATERIAL_BATCH_RESULTS',
  SET_MATERIALS_ERROR: 'SET_MATERIALS_ERROR',
  CLEAR_MATERIALS_ERROR: 'CLEAR_MATERIALS_ERROR',
  
  // OCR actions
  SET_OCR_PROCESSING: 'SET_OCR_PROCESSING',
  SET_OCR_FILE: 'SET_OCR_FILE',
  SET_OCR_RESULTS: 'SET_OCR_RESULTS',
  SET_OCR_PROGRESS: 'SET_OCR_PROGRESS',
  SET_OCR_REPORTS: 'SET_OCR_REPORTS',
  SET_OCR_ERROR: 'SET_OCR_ERROR',
  CLEAR_OCR_ERROR: 'CLEAR_OCR_ERROR',
  
  // Google Maps actions
  SET_GMAP_PROCESSING: 'SET_GMAP_PROCESSING',
  SET_GMAP_SESSION: 'SET_GMAP_SESSION',
  SET_GMAP_RESULTS: 'SET_GMAP_RESULTS',
  SET_GMAP_SESSIONS: 'SET_GMAP_SESSIONS',
  SET_GMAP_ERROR: 'SET_GMAP_ERROR',
  CLEAR_GMAP_ERROR: 'CLEAR_GMAP_ERROR',
  
  // UI actions
  SET_CURRENT_PAGE: 'SET_CURRENT_PAGE',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  SET_THEME: 'SET_THEME'
};

// Reducer function
function appReducer(state, action) {
  switch (action.type) {
    // Global actions
    case actionTypes.SET_LOADING:
      return { ...state, isLoading: action.payload };
    
    case actionTypes.SET_ERROR:
      return { ...state, error: action.payload };
    
    case actionTypes.CLEAR_ERROR:
      return { ...state, error: null };
    
    case actionTypes.UPDATE_SERVICE_STATUS:
      return {
        ...state,
        serviceStatus: { ...state.serviceStatus, ...action.payload }
      };
    
    // Material actions
    case actionTypes.SET_MATERIALS_LOADING:
      return {
        ...state,
        materials: { ...state.materials, isSearching: action.payload }
      };
    
    case actionTypes.SET_MATERIAL_SEARCH_RESULTS:
      return {
        ...state,
        materials: {
          ...state.materials,
          searchResults: action.payload,
          isSearching: false,
          searchError: null
        }
      };
    
    case actionTypes.SET_MATERIAL_BATCH_RESULTS:
      return {
        ...state,
        materials: {
          ...state.materials,
          batchResults: action.payload,
          isSearching: false,
          searchError: null
        }
      };
    
    case actionTypes.SET_MATERIALS_ERROR:
      return {
        ...state,
        materials: {
          ...state.materials,
          isSearching: false,
          searchError: action.payload
        }
      };
    
    case actionTypes.CLEAR_MATERIALS_ERROR:
      return {
        ...state,
        materials: { ...state.materials, searchError: null }
      };
    
    // OCR actions
    case actionTypes.SET_OCR_PROCESSING:
      return {
        ...state,
        ocr: { ...state.ocr, isProcessing: action.payload }
      };
    
    case actionTypes.SET_OCR_FILE:
      return {
        ...state,
        ocr: { ...state.ocr, currentFile: action.payload }
      };
    
    case actionTypes.SET_OCR_RESULTS:
      return {
        ...state,
        ocr: {
          ...state.ocr,
          results: action.payload,
          isProcessing: false,
          error: null
        }
      };
    
    case actionTypes.SET_OCR_PROGRESS:
      return {
        ...state,
        ocr: { ...state.ocr, progress: action.payload }
      };
    
    case actionTypes.SET_OCR_REPORTS:
      return {
        ...state,
        ocr: { ...state.ocr, reports: action.payload }
      };
    
    case actionTypes.SET_OCR_ERROR:
      return {
        ...state,
        ocr: {
          ...state.ocr,
          isProcessing: false,
          error: action.payload
        }
      };
    
    case actionTypes.CLEAR_OCR_ERROR:
      return {
        ...state,
        ocr: { ...state.ocr, error: null }
      };
    
    // Google Maps actions
    case actionTypes.SET_GMAP_PROCESSING:
      return {
        ...state,
        gmap: { ...state.gmap, isProcessing: action.payload }
      };
    
    case actionTypes.SET_GMAP_SESSION:
      return {
        ...state,
        gmap: { ...state.gmap, currentSession: action.payload }
      };
    
    case actionTypes.SET_GMAP_RESULTS:
      return {
        ...state,
        gmap: {
          ...state.gmap,
          results: action.payload,
          isProcessing: false,
          error: null
        }
      };
    
    case actionTypes.SET_GMAP_SESSIONS:
      return {
        ...state,
        gmap: { ...state.gmap, sessions: action.payload }
      };
    
    case actionTypes.SET_GMAP_ERROR:
      return {
        ...state,
        gmap: {
          ...state.gmap,
          isProcessing: false,
          error: action.payload
        }
      };
    
    case actionTypes.CLEAR_GMAP_ERROR:
      return {
        ...state,
        gmap: { ...state.gmap, error: null }
      };
    
    // UI actions
    case actionTypes.SET_CURRENT_PAGE:
      return {
        ...state,
        ui: { ...state.ui, currentPage: action.payload }
      };
    
    case actionTypes.ADD_NOTIFICATION:
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: [...state.ui.notifications, {
            id: Date.now(),
            ...action.payload
          }]
        }
      };
    
    case actionTypes.REMOVE_NOTIFICATION:
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: state.ui.notifications.filter(
            notif => notif.id !== action.payload
          )
        }
      };
    
    case actionTypes.SET_THEME:
      return {
        ...state,
        ui: { ...state.ui, theme: action.payload }
      };
    
    default:
      return state;
  }
}

// Create context
const AppContext = createContext();

// Context provider component
export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const apiService = new APIService();

  // Check service status on mount
  useEffect(() => {
    checkServiceStatus();
  }, []);

  const checkServiceStatus = async () => {
    try {
      const healthData = await apiService.healthCheck();
      
      if (healthData.success && healthData.data) {
        dispatch({
          type: actionTypes.UPDATE_SERVICE_STATUS,
          payload: {
            api: 'connected',
            database: healthData.data.services?.database === 'connected' ? 'connected' : 'disconnected',
            ocr: healthData.data.services?.ocr === 'available' ? 'available' : 'unavailable',
            googleMaps: healthData.data.services?.google_maps === 'available' ? 'available' : 'unavailable'
          }
        });
      }
    } catch (error) {
      console.error('Service status check failed:', error);
      dispatch({
        type: actionTypes.UPDATE_SERVICE_STATUS,
        payload: {
          api: 'disconnected',
          database: 'unknown',
          ocr: 'unknown',
          googleMaps: 'unknown'
        }
      });
    }
  };

  // Action creators
  const actions = {
    // Global actions
    setLoading: (loading) => dispatch({ type: actionTypes.SET_LOADING, payload: loading }),
    setError: (error) => dispatch({ type: actionTypes.SET_ERROR, payload: error }),
    clearError: () => dispatch({ type: actionTypes.CLEAR_ERROR }),
    
    // Material actions
    setMaterialsLoading: (loading) => dispatch({ type: actionTypes.SET_MATERIALS_LOADING, payload: loading }),
    setMaterialSearchResults: (results) => dispatch({ type: actionTypes.SET_MATERIAL_SEARCH_RESULTS, payload: results }),
    setMaterialBatchResults: (results) => dispatch({ type: actionTypes.SET_MATERIAL_BATCH_RESULTS, payload: results }),
    setMaterialsError: (error) => dispatch({ type: actionTypes.SET_MATERIALS_ERROR, payload: error }),
    clearMaterialsError: () => dispatch({ type: actionTypes.CLEAR_MATERIALS_ERROR }),
    
    // OCR actions
    setOCRProcessing: (processing) => dispatch({ type: actionTypes.SET_OCR_PROCESSING, payload: processing }),
    setOCRFile: (file) => dispatch({ type: actionTypes.SET_OCR_FILE, payload: file }),
    setOCRResults: (results) => dispatch({ type: actionTypes.SET_OCR_RESULTS, payload: results }),
    setOCRProgress: (progress) => dispatch({ type: actionTypes.SET_OCR_PROGRESS, payload: progress }),
    setOCRReports: (reports) => dispatch({ type: actionTypes.SET_OCR_REPORTS, payload: reports }),
    setOCRError: (error) => dispatch({ type: actionTypes.SET_OCR_ERROR, payload: error }),
    clearOCRError: () => dispatch({ type: actionTypes.CLEAR_OCR_ERROR }),
    
    // Google Maps actions
    setGMapProcessing: (processing) => dispatch({ type: actionTypes.SET_GMAP_PROCESSING, payload: processing }),
    setGMapSession: (session) => dispatch({ type: actionTypes.SET_GMAP_SESSION, payload: session }),
    setGMapResults: (results) => dispatch({ type: actionTypes.SET_GMAP_RESULTS, payload: results }),
    setGMapSessions: (sessions) => dispatch({ type: actionTypes.SET_GMAP_SESSIONS, payload: sessions }),
    setGMapError: (error) => dispatch({ type: actionTypes.SET_GMAP_ERROR, payload: error }),
    clearGMapError: () => dispatch({ type: actionTypes.CLEAR_GMAP_ERROR }),
    
    // UI actions
    setCurrentPage: (page) => dispatch({ type: actionTypes.SET_CURRENT_PAGE, payload: page }),
    addNotification: (notification) => dispatch({ type: actionTypes.ADD_NOTIFICATION, payload: notification }),
    removeNotification: (id) => dispatch({ type: actionTypes.REMOVE_NOTIFICATION, payload: id }),
    setTheme: (theme) => dispatch({ type: actionTypes.SET_THEME, payload: theme }),
    
    // Utility actions
    checkServiceStatus
  };

  const value = {
    state,
    actions
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

// Custom hook to use the context
export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}

export default AppContext;