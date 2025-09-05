/**
 * 語音狀態管理系統 - 企業級Zustand Store
 * 管理全局語音播放狀態、用戶偏好設置和播放歷史
 * 支援六大數位分析師語音協調播放
 * 
 * @author 梁建築師 (Code Architect)
 * @version 1.0.0 Enterprise
 */

import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';
import { TTSVoice, AudioFormat } from '../admin/types/AdminTypes';

// ==================== 介面定義 ====================

// 語音播放記錄
export interface VoicePlaybackRecord {
  id: string;
  text: string;
  voiceId: string;
  duration?: number;
  playedAt: Date;
  analystId?: string;
  scenario?: string;
  completed: boolean;
}

// 當前播放狀態
export interface CurrentPlayback {
  text: string;
  voiceId: string;
  startTime: Date;
  analystId?: string;
  scenario?: string;
  progress?: number;
}

// 用戶語音偏好設置
export interface VoiceUserPreferences {
  defaultVoiceId: string;
  defaultAudioFormat: AudioFormat;
  volume: number;
  speakingRate: number;
  pitch: number;
  autoPlay: boolean;
  showControls: boolean;
  
  // 分析師偏好
  analystPreferences: {
    [analystId: string]: {
      voiceId: string;
      speakingRate: number;
      pitch: number;
      volume: number;
    };
  };
  
  // 場景偏好
  scenarioPreferences: {
    [scenario: string]: {
      voiceId?: string;
      speakingRate?: number;
      pitch?: number;
      volume?: number;
    };
  };
}

// 語音隊列項目
export interface VoiceQueueItem {
  id: string;
  text: string;
  voiceId: string;
  analystId?: string;
  scenario?: string;
  priority: number;
  settings?: {
    speakingRate?: number;
    pitch?: number;
    volume?: number;
  };
  metadata?: {
    title?: string;
    category?: string;
    timestamp: Date;
  };
}

// 語音狀態統計
export interface VoiceStats {
  totalPlayed: number;
  totalDuration: number;
  favoriteVoice: string;
  mostUsedAnalyst: string;
  dailyUsage: { [date: string]: number };
  weeklyUsage: { [week: string]: number };
  monthlyUsage: { [month: string]: number };
}

// ==================== Store 狀態介面 ====================

export interface VoiceStoreState {
  // 語音數據
  voices: TTSVoice[];
  currentVoice: TTSVoice | null;
  
  // 播放狀態
  isGloballyPlaying: boolean;
  currentPlayback: CurrentPlayback | null;
  playbackHistory: VoicePlaybackRecord[];
  
  // 語音隊列
  voiceQueue: VoiceQueueItem[];
  queueIndex: number;
  isQueuePlaying: boolean;
  repeatMode: 'none' | 'one' | 'all';
  shuffleMode: boolean;
  
  // 用戶偏好
  userPreferences: VoiceUserPreferences;
  
  // 統計數據
  stats: VoiceStats;
  
  // 加載狀態
  isLoading: boolean;
  error: string | null;
  
  // 緩存控制
  lastUpdate: Date | null;
  cacheTimeout: number;
}

export interface VoiceStoreActions {
  // ==================== 語音管理 Actions ====================
  setVoices: (voices: TTSVoice[]) => void;
  setCurrentVoice: (voice: TTSVoice | null) => void;
  addVoice: (voice: TTSVoice) => void;
  removeVoice: (voiceId: string) => void;
  updateVoice: (voiceId: string, updates: Partial<TTSVoice>) => void;
  
  // ==================== 播放控制 Actions ====================
  setCurrentPlaying: (playback: CurrentPlayback | null) => void;
  setGlobalPlayState: (isPlaying: boolean) => void;
  addToHistory: (record: VoicePlaybackRecord) => void;
  clearHistory: () => void;
  removeFromHistory: (recordId: string) => void;
  updatePlaybackProgress: (progress: number) => void;
  
  // ==================== 隊列管理 Actions ====================
  addToQueue: (item: VoiceQueueItem) => void;
  removeFromQueue: (itemId: string) => void;
  clearQueue: () => void;
  reorderQueue: (fromIndex: number, toIndex: number) => void;
  setQueueIndex: (index: number) => void;
  nextInQueue: () => VoiceQueueItem | null;
  previousInQueue: () => VoiceQueueItem | null;
  setRepeatMode: (mode: 'none' | 'one' | 'all') => void;
  setShuffleMode: (enabled: boolean) => void;
  setQueuePlaying: (playing: boolean) => void;
  
  // ==================== 偏好設置 Actions ====================
  updateUserPreferences: (preferences: Partial<VoiceUserPreferences>) => void;
  updateAnalystPreference: (analystId: string, preference: VoiceUserPreferences['analystPreferences'][string]) => void;
  updateScenarioPreference: (scenario: string, preference: VoiceUserPreferences['scenarioPreferences'][string]) => void;
  resetPreferences: () => void;
  
  // ==================== 統計 Actions ====================
  updateStats: (updates: Partial<VoiceStats>) => void;
  incrementPlayCount: (voiceId: string, analystId?: string) => void;
  addPlayDuration: (duration: number) => void;
  resetStats: () => void;
  
  // ==================== 工具 Actions ====================
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  refreshCache: () => void;
  
  // ==================== 高級功能 Actions ====================
  createSmartPlaylist: (criteria: {
    analystIds?: string[];
    scenarios?: string[];
    textKeywords?: string[];
    maxItems?: number;
  }) => VoiceQueueItem[];
  
  exportUserData: () => {
    preferences: VoiceUserPreferences;
    history: VoicePlaybackRecord[];
    stats: VoiceStats;
  };
  
  importUserData: (data: {
    preferences?: VoiceUserPreferences;
    history?: VoicePlaybackRecord[];
    stats?: VoiceStats;
  }) => void;
}

// ==================== 初始狀態 ====================

const defaultUserPreferences: VoiceUserPreferences = {
  defaultVoiceId: 'zh-TW-HsiaoChenNeural',
  defaultAudioFormat: AudioFormat.MP3,
  volume: 0.8,
  speakingRate: 1.0,
  pitch: 0,
  autoPlay: false,
  showControls: true,
  analystPreferences: {},
  scenarioPreferences: {}
};

const defaultStats: VoiceStats = {
  totalPlayed: 0,
  totalDuration: 0,
  favoriteVoice: '',
  mostUsedAnalyst: '',
  dailyUsage: {},
  weeklyUsage: {},
  monthlyUsage: {}
};

const initialState: VoiceStoreState = {
  voices: [],
  currentVoice: null,
  isGloballyPlaying: false,
  currentPlayback: null,
  playbackHistory: [],
  voiceQueue: [],
  queueIndex: 0,
  isQueuePlaying: false,
  repeatMode: 'none',
  shuffleMode: false,
  userPreferences: defaultUserPreferences,
  stats: defaultStats,
  isLoading: false,
  error: null,
  lastUpdate: null,
  cacheTimeout: 5 * 60 * 1000 // 5分鐘緩存
};

// ==================== Store 實現 ====================

export const useVoiceStore = create<VoiceStoreState & VoiceStoreActions>()(
  devtools(
    persist(
      subscribeWithSelector((set, get) => ({
        ...initialState,

        // ==================== 語音管理 Actions ====================
        setVoices: (voices) => set(
          { voices, lastUpdate: new Date() },
          false,
          'setVoices'
        ),

        setCurrentVoice: (voice) => set(
          { currentVoice: voice },
          false,
          'setCurrentVoice'
        ),

        addVoice: (voice) => set(
          (state) => ({
            voices: [...state.voices, voice],
            lastUpdate: new Date()
          }),
          false,
          'addVoice'
        ),

        removeVoice: (voiceId) => set(
          (state) => ({
            voices: state.voices.filter(v => v.model_id !== voiceId),
            currentVoice: state.currentVoice?.model_id === voiceId ? null : state.currentVoice,
            lastUpdate: new Date()
          }),
          false,
          'removeVoice'
        ),

        updateVoice: (voiceId, updates) => set(
          (state) => ({
            voices: state.voices.map(v => 
              v.model_id === voiceId ? { ...v, ...updates } : v
            ),
            currentVoice: state.currentVoice?.model_id === voiceId 
              ? { ...state.currentVoice, ...updates }
              : state.currentVoice,
            lastUpdate: new Date()
          }),
          false,
          'updateVoice'
        ),

        // ==================== 播放控制 Actions ====================
        setCurrentPlaying: (playback) => set(
          { 
            currentPlayback: playback,
            isGloballyPlaying: playback !== null
          },
          false,
          'setCurrentPlaying'
        ),

        setGlobalPlayState: (isPlaying) => set(
          { isGloballyPlaying: isPlaying },
          false,
          'setGlobalPlayState'
        ),

        addToHistory: (record) => set(
          (state) => {
            const newHistory = [record, ...state.playbackHistory];
            // 限制歷史記錄數量，保留最近1000條
            const trimmedHistory = newHistory.slice(0, 1000);
            
            return {
              playbackHistory: trimmedHistory,
              stats: {
                ...state.stats,
                totalPlayed: state.stats.totalPlayed + 1
              }
            };
          },
          false,
          'addToHistory'
        ),

        clearHistory: () => set(
          { playbackHistory: [] },
          false,
          'clearHistory'
        ),

        removeFromHistory: (recordId) => set(
          (state) => ({
            playbackHistory: state.playbackHistory.filter(record => record.id !== recordId)
          }),
          false,
          'removeFromHistory'
        ),

        updatePlaybackProgress: (progress) => set(
          (state) => state.currentPlayback ? {
            currentPlayback: { ...state.currentPlayback, progress }
          } : {},
          false,
          'updatePlaybackProgress'
        ),

        // ==================== 隊列管理 Actions ====================
        addToQueue: (item) => set(
          (state) => ({
            voiceQueue: [...state.voiceQueue, item]
          }),
          false,
          'addToQueue'
        ),

        removeFromQueue: (itemId) => set(
          (state) => {
            const newQueue = state.voiceQueue.filter(item => item.id !== itemId);
            const newIndex = state.queueIndex >= newQueue.length ? 0 : state.queueIndex;
            return {
              voiceQueue: newQueue,
              queueIndex: newIndex
            };
          },
          false,
          'removeFromQueue'
        ),

        clearQueue: () => set(
          { voiceQueue: [], queueIndex: 0, isQueuePlaying: false },
          false,
          'clearQueue'
        ),

        reorderQueue: (fromIndex, toIndex) => set(
          (state) => {
            const newQueue = [...state.voiceQueue];
            const [movedItem] = newQueue.splice(fromIndex, 1);
            newQueue.splice(toIndex, 0, movedItem);
            
            // 調整當前索引
            let newIndex = state.queueIndex;
            if (fromIndex === state.queueIndex) {
              newIndex = toIndex;
            } else if (fromIndex < state.queueIndex && toIndex >= state.queueIndex) {
              newIndex = state.queueIndex - 1;
            } else if (fromIndex > state.queueIndex && toIndex <= state.queueIndex) {
              newIndex = state.queueIndex + 1;
            }
            
            return { voiceQueue: newQueue, queueIndex: newIndex };
          },
          false,
          'reorderQueue'
        ),

        setQueueIndex: (index) => set(
          (state) => ({
            queueIndex: Math.max(0, Math.min(index, state.voiceQueue.length - 1))
          }),
          false,
          'setQueueIndex'
        ),

        nextInQueue: () => {
          const state = get();
          const { voiceQueue, queueIndex, repeatMode, shuffleMode } = state;
          
          if (voiceQueue.length === 0) return null;
          
          let nextIndex: number;
          
          if (shuffleMode) {
            nextIndex = Math.floor(Math.random() * voiceQueue.length);
          } else if (repeatMode === 'one') {
            nextIndex = queueIndex;
          } else if (repeatMode === 'all') {
            nextIndex = (queueIndex + 1) % voiceQueue.length;
          } else {
            nextIndex = queueIndex + 1;
            if (nextIndex >= voiceQueue.length) return null;
          }
          
          set({ queueIndex: nextIndex }, false, 'nextInQueue');
          return voiceQueue[nextIndex];
        },

        previousInQueue: () => {
          const state = get();
          const { voiceQueue, queueIndex } = state;
          
          if (voiceQueue.length === 0 || queueIndex === 0) return null;
          
          const prevIndex = queueIndex - 1;
          set({ queueIndex: prevIndex }, false, 'previousInQueue');
          return voiceQueue[prevIndex];
        },

        setRepeatMode: (mode) => set(
          { repeatMode: mode },
          false,
          'setRepeatMode'
        ),

        setShuffleMode: (enabled) => set(
          { shuffleMode: enabled },
          false,
          'setShuffleMode'
        ),

        setQueuePlaying: (playing) => set(
          { isQueuePlaying: playing },
          false,
          'setQueuePlaying'
        ),

        // ==================== 偏好設置 Actions ====================
        updateUserPreferences: (preferences) => set(
          (state) => ({
            userPreferences: { ...state.userPreferences, ...preferences }
          }),
          false,
          'updateUserPreferences'
        ),

        updateAnalystPreference: (analystId, preference) => set(
          (state) => ({
            userPreferences: {
              ...state.userPreferences,
              analystPreferences: {
                ...state.userPreferences.analystPreferences,
                [analystId]: preference
              }
            }
          }),
          false,
          'updateAnalystPreference'
        ),

        updateScenarioPreference: (scenario, preference) => set(
          (state) => ({
            userPreferences: {
              ...state.userPreferences,
              scenarioPreferences: {
                ...state.userPreferences.scenarioPreferences,
                [scenario]: preference
              }
            }
          }),
          false,
          'updateScenarioPreference'
        ),

        resetPreferences: () => set(
          { userPreferences: defaultUserPreferences },
          false,
          'resetPreferences'
        ),

        // ==================== 統計 Actions ====================
        updateStats: (updates) => set(
          (state) => ({
            stats: { ...state.stats, ...updates }
          }),
          false,
          'updateStats'
        ),

        incrementPlayCount: (voiceId, analystId) => set(
          (state) => {
            const today = new Date().toISOString().split('T')[0];
            const thisWeek = new Date().toISOString().split('T')[0].substring(0, 8) + 'W' + Math.ceil(new Date().getDate() / 7);
            const thisMonth = new Date().toISOString().substring(0, 7);
            
            return {
              stats: {
                ...state.stats,
                totalPlayed: state.stats.totalPlayed + 1,
                favoriteVoice: voiceId, // 簡化實現，實際應統計最常用
                mostUsedAnalyst: analystId || state.stats.mostUsedAnalyst,
                dailyUsage: {
                  ...state.stats.dailyUsage,
                  [today]: (state.stats.dailyUsage[today] || 0) + 1
                },
                weeklyUsage: {
                  ...state.stats.weeklyUsage,
                  [thisWeek]: (state.stats.weeklyUsage[thisWeek] || 0) + 1
                },
                monthlyUsage: {
                  ...state.stats.monthlyUsage,
                  [thisMonth]: (state.stats.monthlyUsage[thisMonth] || 0) + 1
                }
              }
            };
          },
          false,
          'incrementPlayCount'
        ),

        addPlayDuration: (duration) => set(
          (state) => ({
            stats: {
              ...state.stats,
              totalDuration: state.stats.totalDuration + duration
            }
          }),
          false,
          'addPlayDuration'
        ),

        resetStats: () => set(
          { stats: defaultStats },
          false,
          'resetStats'
        ),

        // ==================== 工具 Actions ====================
        setLoading: (loading) => set(
          { isLoading: loading },
          false,
          'setLoading'
        ),

        setError: (error) => set(
          { error },
          false,
          'setError'
        ),

        refreshCache: () => set(
          { lastUpdate: new Date() },
          false,
          'refreshCache'
        ),

        // ==================== 高級功能 Actions ====================
        createSmartPlaylist: (criteria) => {
          const state = get();
          const { playbackHistory } = state;
          
          // 基於歷史記錄和條件創建智能播放列表
          let filteredHistory = playbackHistory;
          
          if (criteria.analystIds) {
            filteredHistory = filteredHistory.filter(record => 
              criteria.analystIds!.includes(record.analystId || '')
            );
          }
          
          if (criteria.scenarios) {
            filteredHistory = filteredHistory.filter(record => 
              criteria.scenarios!.includes(record.scenario || '')
            );
          }
          
          if (criteria.textKeywords) {
            filteredHistory = filteredHistory.filter(record => 
              criteria.textKeywords!.some(keyword => 
                record.text.toLowerCase().includes(keyword.toLowerCase())
              )
            );
          }
          
          // 轉換為隊列項目並限制數量
          const playlist = filteredHistory
            .slice(0, criteria.maxItems || 50)
            .map((record, index) => ({
              id: `smart-${Date.now()}-${index}`,
              text: record.text,
              voiceId: record.voiceId,
              analystId: record.analystId,
              scenario: record.scenario,
              priority: 5,
              metadata: {
                title: `智能推薦 ${index + 1}`,
                category: 'smart-playlist',
                timestamp: new Date()
              }
            }));
          
          return playlist;
        },

        exportUserData: () => {
          const state = get();
          return {
            preferences: state.userPreferences,
            history: state.playbackHistory,
            stats: state.stats
          };
        },

        importUserData: (data) => set(
          (state) => ({
            userPreferences: data.preferences || state.userPreferences,
            playbackHistory: data.history || state.playbackHistory,
            stats: data.stats || state.stats,
            lastUpdate: new Date()
          }),
          false,
          'importUserData'
        )
      })),
      {
        name: 'voice-store',
        partialize: (state) => ({
          userPreferences: state.userPreferences,
          playbackHistory: state.playbackHistory.slice(0, 100), // 只持久化最近100條記錄
          stats: state.stats,
          repeatMode: state.repeatMode,
          shuffleMode: state.shuffleMode
        })
      }
    ),
    {
      name: 'VoiceStore'
    }
  )
);

// ==================== Hook 工具函數 ====================

// 獲取分析師偏好設置的Hook
export const useAnalystPreferences = () => {
  return useVoiceStore((state) => ({
    preferences: state.userPreferences.analystPreferences,
    updatePreference: state.updateAnalystPreference
  }));
};

// 獲取播放隊列控制的Hook
export const useVoiceQueue = () => {
  return useVoiceStore((state) => ({
    queue: state.voiceQueue,
    currentIndex: state.queueIndex,
    isPlaying: state.isQueuePlaying,
    repeatMode: state.repeatMode,
    shuffleMode: state.shuffleMode,
    addToQueue: state.addToQueue,
    removeFromQueue: state.removeFromQueue,
    clearQueue: state.clearQueue,
    nextInQueue: state.nextInQueue,
    previousInQueue: state.previousInQueue,
    setRepeatMode: state.setRepeatMode,
    setShuffleMode: state.setShuffleMode
  }));
};

// 獲取播放統計的Hook
export const useVoiceStats = () => {
  return useVoiceStore((state) => ({
    stats: state.stats,
    incrementPlayCount: state.incrementPlayCount,
    addPlayDuration: state.addPlayDuration
  }));
};

export default useVoiceStore;