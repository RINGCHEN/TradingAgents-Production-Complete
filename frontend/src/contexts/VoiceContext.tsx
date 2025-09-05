/**
 * 語音狀態管理 Context
 * 提供全局語音播放狀態管理、偏好設置和播放歷史
 * 
 * @author 魯班 (Code Artisan)
 * @version 1.0.0
 */

import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  ReactNode,
  useMemo,
} from 'react';
import ttsApiService, { TTSVoice, TTSJob, TTSStats } from '../services/TTSApiService';

// 語音偏好設置接口
export interface VoicePreferences {
  /** 默認語音ID */
  defaultVoiceId?: string;
  /** 默認音量 (0-1) */
  defaultVolume: number;
  /** 默認播放速度 (0.25-4.0) */
  defaultPlaybackRate: number;
  /** 是否自動播放 */
  autoPlay: boolean;
  /** 音頻格式偏好 */
  preferredFormat: 'mp3' | 'wav' | 'ogg' | 'm4a';
  /** 音質偏好 */
  preferredQuality: 'low' | 'medium' | 'high';
  /** 是否啟用音頻緩存 */
  enableCache: boolean;
  /** 主題偏好 */
  theme: 'light' | 'dark' | 'auto';
  /** 語言偏好 */
  preferredLanguage?: string;
  /** 性別偏好 */
  preferredGender?: 'male' | 'female' | 'neutral';
}

// 播放歷史記錄接口
export interface PlaybackRecord {
  id: string;
  text: string;
  voiceId: string;
  voiceName?: string;
  timestamp: number;
  duration?: number;
  completed: boolean;
}

// 當前播放狀態接口
export interface CurrentPlayback {
  isPlaying: boolean;
  isLoading: boolean;
  currentTrack?: {
    id: string;
    text: string;
    voiceId: string;
    voiceName?: string;
    audioUrl?: string;
    startTime: number;
  };
  progress: number;
  currentTime: number;
  duration: number;
  volume: number;
  playbackRate: number;
  error?: string;
}

// 語音狀態接口
export interface VoiceState {
  // 語音列表和管理
  voices: TTSVoice[];
  voicesLoading: boolean;
  voicesError?: string;
  
  // 當前播放狀態
  currentPlayback: CurrentPlayback;
  
  // 用戶偏好
  preferences: VoicePreferences;
  
  // 播放歷史
  playbackHistory: PlaybackRecord[];
  
  // 統計數據
  stats?: TTSStats;
  
  // 任務管理
  jobs: TTSJob[];
  jobsLoading: boolean;
  
  // 系統狀態
  isOnline: boolean;
  lastSync?: number;
}

// Action 類型定義
export type VoiceAction =
  | { type: 'SET_VOICES'; payload: TTSVoice[] }
  | { type: 'SET_VOICES_LOADING'; payload: boolean }
  | { type: 'SET_VOICES_ERROR'; payload: string | undefined }
  | { type: 'SET_CURRENT_PLAYBACK'; payload: Partial<CurrentPlayback> }
  | { type: 'UPDATE_PREFERENCES'; payload: Partial<VoicePreferences> }
  | { type: 'ADD_PLAYBACK_RECORD'; payload: PlaybackRecord }
  | { type: 'CLEAR_PLAYBACK_HISTORY' }
  | { type: 'SET_STATS'; payload: TTSStats }
  | { type: 'SET_JOBS'; payload: TTSJob[] }
  | { type: 'SET_JOBS_LOADING'; payload: boolean }
  | { type: 'SET_ONLINE_STATUS'; payload: boolean }
  | { type: 'SET_LAST_SYNC'; payload: number }
  | { type: 'RESET_STATE' };

// Context 接口定義
export interface VoiceContextType {
  state: VoiceState;
  dispatch: React.Dispatch<VoiceAction>;
  
  // 語音管理方法
  loadVoices: () => Promise<void>;
  refreshVoices: () => Promise<void>;
  getVoiceById: (id: string) => TTSVoice | undefined;
  
  // 播放控制方法
  startPlayback: (text: string, voiceId: string) => Promise<void>;
  stopPlayback: () => void;
  pausePlayback: () => void;
  resumePlayback: () => void;
  seekTo: (time: number) => void;
  setVolume: (volume: number) => void;
  setPlaybackRate: (rate: number) => void;
  
  // 偏好管理方法
  updatePreferences: (preferences: Partial<VoicePreferences>) => void;
  resetPreferences: () => void;
  
  // 歷史管理方法
  addToHistory: (record: Omit<PlaybackRecord, 'id' | 'timestamp'>) => void;
  clearHistory: () => void;
  getHistoryByVoice: (voiceId: string) => PlaybackRecord[];
  
  // 統計和監控方法
  loadStats: () => Promise<void>;
  loadJobs: () => Promise<void>;
  
  // 實用方法
  exportPreferences: () => string;
  importPreferences: (data: string) => boolean;
}

// 默認偏好設置
const defaultPreferences: VoicePreferences = {
  defaultVolume: 0.8,
  defaultPlaybackRate: 1.0,
  autoPlay: false,
  preferredFormat: 'mp3',
  preferredQuality: 'medium',
  enableCache: true,
  theme: 'auto',
};

// 默認播放狀態
const defaultCurrentPlayback: CurrentPlayback = {
  isPlaying: false,
  isLoading: false,
  progress: 0,
  currentTime: 0,
  duration: 0,
  volume: 0.8,
  playbackRate: 1.0,
};

// 初始狀態
const initialState: VoiceState = {
  voices: [],
  voicesLoading: false,
  currentPlayback: defaultCurrentPlayback,
  preferences: defaultPreferences,
  playbackHistory: [],
  jobs: [],
  jobsLoading: false,
  isOnline: navigator.onLine,
};

// Reducer 函數
function voiceReducer(state: VoiceState, action: VoiceAction): VoiceState {
  switch (action.type) {
    case 'SET_VOICES':
      return {
        ...state,
        voices: action.payload,
        voicesLoading: false,
        voicesError: undefined,
      };
    
    case 'SET_VOICES_LOADING':
      return {
        ...state,
        voicesLoading: action.payload,
      };
    
    case 'SET_VOICES_ERROR':
      return {
        ...state,
        voicesError: action.payload,
        voicesLoading: false,
      };
    
    case 'SET_CURRENT_PLAYBACK':
      return {
        ...state,
        currentPlayback: {
          ...state.currentPlayback,
          ...action.payload,
        },
      };
    
    case 'UPDATE_PREFERENCES':
      const newPreferences = {
        ...state.preferences,
        ...action.payload,
      };
      // 保存到 localStorage
      localStorage.setItem('voicePreferences', JSON.stringify(newPreferences));
      return {
        ...state,
        preferences: newPreferences,
      };
    
    case 'ADD_PLAYBACK_RECORD':
      const newHistory = [action.payload, ...state.playbackHistory.slice(0, 99)]; // 保持最多100條記錄
      localStorage.setItem('playbackHistory', JSON.stringify(newHistory));
      return {
        ...state,
        playbackHistory: newHistory,
      };
    
    case 'CLEAR_PLAYBACK_HISTORY':
      localStorage.removeItem('playbackHistory');
      return {
        ...state,
        playbackHistory: [],
      };
    
    case 'SET_STATS':
      return {
        ...state,
        stats: action.payload,
      };
    
    case 'SET_JOBS':
      return {
        ...state,
        jobs: action.payload,
        jobsLoading: false,
      };
    
    case 'SET_JOBS_LOADING':
      return {
        ...state,
        jobsLoading: action.payload,
      };
    
    case 'SET_ONLINE_STATUS':
      return {
        ...state,
        isOnline: action.payload,
      };
    
    case 'SET_LAST_SYNC':
      return {
        ...state,
        lastSync: action.payload,
      };
    
    case 'RESET_STATE':
      localStorage.removeItem('voicePreferences');
      localStorage.removeItem('playbackHistory');
      return initialState;
    
    default:
      return state;
  }
}

// 加載保存的狀態
function loadStoredState(): Partial<VoiceState> {
  try {
    const storedPreferences = localStorage.getItem('voicePreferences');
    const storedHistory = localStorage.getItem('playbackHistory');
    
    return {
      preferences: storedPreferences 
        ? { ...defaultPreferences, ...JSON.parse(storedPreferences) }
        : defaultPreferences,
      playbackHistory: storedHistory ? JSON.parse(storedHistory) : [],
    };
  } catch (error) {
    console.warn('Failed to load stored voice state:', error);
    return {};
  }
}

// 創建 Context
const VoiceContext = createContext<VoiceContextType | undefined>(undefined);

// Provider 組件
export interface VoiceProviderProps {
  children: ReactNode;
}

export const VoiceProvider: React.FC<VoiceProviderProps> = ({ children }) => {
  // 初始化狀態，包含保存的數據
  const [state, dispatch] = useReducer(voiceReducer, {
    ...initialState,
    ...loadStoredState(),
  });

  // 網絡狀態監控
  useEffect(() => {
    const handleOnline = () => dispatch({ type: 'SET_ONLINE_STATUS', payload: true });
    const handleOffline = () => dispatch({ type: 'SET_ONLINE_STATUS', payload: false });

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // 語音管理方法
  const loadVoices = useCallback(async () => {
    if (!state.isOnline) return;

    dispatch({ type: 'SET_VOICES_LOADING', payload: true });
    
    try {
      const voices = await ttsApiService.getVoices({ active_only: true });
      dispatch({ type: 'SET_VOICES', payload: voices });
      dispatch({ type: 'SET_LAST_SYNC', payload: Date.now() });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '獲取語音列表失敗';
      dispatch({ type: 'SET_VOICES_ERROR', payload: errorMessage });
      console.error('Load voices error:', error);
    }
  }, [state.isOnline]);

  const refreshVoices = useCallback(async () => {
    await loadVoices();
  }, [loadVoices]);

  const getVoiceById = useCallback((id: string) => {
    return state.voices.find(voice => voice.model_id === id || String(voice.id) === id);
  }, [state.voices]);

  // 播放控制方法
  const startPlayback = useCallback(async (text: string, voiceId: string) => {
    if (!state.isOnline) {
      throw new Error('網絡連接不可用');
    }

    const voice = getVoiceById(voiceId);
    if (!voice) {
      throw new Error('找不到指定的語音');
    }

    dispatch({
      type: 'SET_CURRENT_PLAYBACK',
      payload: {
        isLoading: true,
        currentTrack: {
          id: `${Date.now()}-${Math.random()}`,
          text,
          voiceId,
          voiceName: voice.name,
          startTime: Date.now(),
        },
        error: undefined,
      },
    });

    try {
      const result = await ttsApiService.quickSynthesis(text, voiceId, {
        speaking_rate: state.preferences.defaultPlaybackRate,
        audio_format: state.preferences.preferredFormat,
      });

      if (result.success && result.audio_url) {
        dispatch({
          type: 'SET_CURRENT_PLAYBACK',
          payload: {
            isLoading: false,
            isPlaying: true,
            currentTrack: {
              id: `${Date.now()}-${Math.random()}`,
              text,
              voiceId,
              voiceName: voice.name,
              audioUrl: result.audio_url,
              startTime: Date.now(),
            },
            duration: result.estimated_duration || 0,
          },
        });

        // 添加到播放歷史
        addToHistory({
          text,
          voiceId,
          voiceName: voice.name,
          duration: result.estimated_duration,
          completed: false,
        });
      } else {
        throw new Error('語音合成失敗');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '播放失敗';
      dispatch({
        type: 'SET_CURRENT_PLAYBACK',
        payload: {
          isLoading: false,
          isPlaying: false,
          error: errorMessage,
        },
      });
      console.error('Start playback error:', error);
      throw error;
    }
  }, [state.isOnline, state.preferences, getVoiceById]);

  const stopPlayback = useCallback(() => {
    dispatch({
      type: 'SET_CURRENT_PLAYBACK',
      payload: {
        isPlaying: false,
        currentTime: 0,
        progress: 0,
        currentTrack: undefined,
      },
    });
  }, []);

  const pausePlayback = useCallback(() => {
    dispatch({
      type: 'SET_CURRENT_PLAYBACK',
      payload: { isPlaying: false },
    });
  }, []);

  const resumePlayback = useCallback(() => {
    if (state.currentPlayback.currentTrack) {
      dispatch({
        type: 'SET_CURRENT_PLAYBACK',
        payload: { isPlaying: true },
      });
    }
  }, [state.currentPlayback.currentTrack]);

  const seekTo = useCallback((time: number) => {
    const clampedTime = Math.max(0, Math.min(time, state.currentPlayback.duration));
    const progress = state.currentPlayback.duration > 0 
      ? (clampedTime / state.currentPlayback.duration) * 100 
      : 0;
    
    dispatch({
      type: 'SET_CURRENT_PLAYBACK',
      payload: {
        currentTime: clampedTime,
        progress,
      },
    });
  }, [state.currentPlayback.duration]);

  const setVolume = useCallback((volume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    dispatch({
      type: 'SET_CURRENT_PLAYBACK',
      payload: { volume: clampedVolume },
    });
  }, []);

  const setPlaybackRate = useCallback((rate: number) => {
    const clampedRate = Math.max(0.25, Math.min(4, rate));
    dispatch({
      type: 'SET_CURRENT_PLAYBACK',
      payload: { playbackRate: clampedRate },
    });
  }, []);

  // 偏好管理方法
  const updatePreferences = useCallback((preferences: Partial<VoicePreferences>) => {
    dispatch({ type: 'UPDATE_PREFERENCES', payload: preferences });
  }, []);

  const resetPreferences = useCallback(() => {
    dispatch({ type: 'UPDATE_PREFERENCES', payload: defaultPreferences });
  }, []);

  // 歷史管理方法
  const addToHistory = useCallback((record: Omit<PlaybackRecord, 'id' | 'timestamp'>) => {
    const historyRecord: PlaybackRecord = {
      ...record,
      id: `${Date.now()}-${Math.random()}`,
      timestamp: Date.now(),
    };
    dispatch({ type: 'ADD_PLAYBACK_RECORD', payload: historyRecord });
  }, []);

  const clearHistory = useCallback(() => {
    dispatch({ type: 'CLEAR_PLAYBACK_HISTORY' });
  }, []);

  const getHistoryByVoice = useCallback((voiceId: string) => {
    return state.playbackHistory.filter(record => record.voiceId === voiceId);
  }, [state.playbackHistory]);

  // 統計和監控方法
  const loadStats = useCallback(async () => {
    if (!state.isOnline) return;

    try {
      const stats = await ttsApiService.getStats();
      dispatch({ type: 'SET_STATS', payload: stats });
    } catch (error) {
      console.error('Load stats error:', error);
    }
  }, [state.isOnline]);

  const loadJobs = useCallback(async () => {
    if (!state.isOnline) return;

    dispatch({ type: 'SET_JOBS_LOADING', payload: true });
    
    try {
      const jobs = await ttsApiService.getJobs({ limit: 50 });
      dispatch({ type: 'SET_JOBS', payload: jobs });
    } catch (error) {
      console.error('Load jobs error:', error);
      dispatch({ type: 'SET_JOBS_LOADING', payload: false });
    }
  }, [state.isOnline]);

  // 實用方法
  const exportPreferences = useCallback(() => {
    const exportData = {
      preferences: state.preferences,
      version: '1.0.0',
      timestamp: Date.now(),
    };
    return JSON.stringify(exportData, null, 2);
  }, [state.preferences]);

  const importPreferences = useCallback((data: string): boolean => {
    try {
      const importData = JSON.parse(data);
      if (importData.preferences && typeof importData.preferences === 'object') {
        dispatch({ type: 'UPDATE_PREFERENCES', payload: importData.preferences });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Import preferences error:', error);
      return false;
    }
  }, []);

  // 初始化加載
  useEffect(() => {
    if (state.voices.length === 0 && state.isOnline && !state.voicesLoading) {
      loadVoices();
    }
  }, [loadVoices, state.voices.length, state.isOnline, state.voicesLoading]);

  // 創建 context 值
  const contextValue = useMemo<VoiceContextType>(() => ({
    state,
    dispatch,
    loadVoices,
    refreshVoices,
    getVoiceById,
    startPlayback,
    stopPlayback,
    pausePlayback,
    resumePlayback,
    seekTo,
    setVolume,
    setPlaybackRate,
    updatePreferences,
    resetPreferences,
    addToHistory,
    clearHistory,
    getHistoryByVoice,
    loadStats,
    loadJobs,
    exportPreferences,
    importPreferences,
  }), [
    state,
    loadVoices,
    refreshVoices,
    getVoiceById,
    startPlayback,
    stopPlayback,
    pausePlayback,
    resumePlayback,
    seekTo,
    setVolume,
    setPlaybackRate,
    updatePreferences,
    resetPreferences,
    addToHistory,
    clearHistory,
    getHistoryByVoice,
    loadStats,
    loadJobs,
    exportPreferences,
    importPreferences,
  ]);

  return (
    <VoiceContext.Provider value={contextValue}>
      {children}
    </VoiceContext.Provider>
  );
};

// Hook 用於使用 Context
export const useVoice = (): VoiceContextType => {
  const context = useContext(VoiceContext);
  if (context === undefined) {
    throw new Error('useVoice must be used within a VoiceProvider');
  }
  return context;
};

// 選擇器 Hooks（用於性能優化）
export const useVoices = () => {
  const { state } = useVoice();
  return useMemo(() => ({
    voices: state.voices,
    loading: state.voicesLoading,
    error: state.voicesError,
  }), [state.voices, state.voicesLoading, state.voicesError]);
};

export const useCurrentPlayback = () => {
  const { state } = useVoice();
  return state.currentPlayback;
};

export const useVoicePreferences = () => {
  const { state, updatePreferences, resetPreferences } = useVoice();
  return useMemo(() => ({
    preferences: state.preferences,
    updatePreferences,
    resetPreferences,
  }), [state.preferences, updatePreferences, resetPreferences]);
};

export const usePlaybackHistory = () => {
  const { state, addToHistory, clearHistory, getHistoryByVoice } = useVoice();
  return useMemo(() => ({
    history: state.playbackHistory,
    addToHistory,
    clearHistory,
    getHistoryByVoice,
  }), [state.playbackHistory, addToHistory, clearHistory, getHistoryByVoice]);
};

export default VoiceContext;