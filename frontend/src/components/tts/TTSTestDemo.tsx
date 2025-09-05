/**
 * TTS系統測試演示組件
 * 用於驗證和展示TTS功能的完整性
 * 包含六大分析師語音合成測試和API連接測試
 * 
 * @author 魯班 (Code Artisan)
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import { TTSMainApp } from './TTSMainApp';
import { AnalystVoicePanel } from '../analyst/AnalystVoicePanel';
import { VoicePlayer } from '../voice/VoicePlayer';
import { useVoiceStore } from '../../store/voiceStore';
import { TTSApiService } from '../../services/TTSApiService';

export interface TTSTestDemoProps {
  showFullApp?: boolean;
  showTestResults?: boolean;
  autoRunTests?: boolean;
}

interface TestResult {
  testName: string;
  status: 'pending' | 'running' | 'passed' | 'failed';
  message: string;
  duration?: number;
}

const TEST_SCENARIOS = [
  {
    id: 'api-connection',
    name: 'API連接測試',
    description: '測試TTS後端API連接狀態'
  },
  {
    id: 'voice-list',
    name: '語音模型加載',
    description: '測試語音模型列表獲取'
  },
  {
    id: 'analyst-config',
    name: '分析師配置',
    description: '測試六大分析師語音配置'
  },
  {
    id: 'voice-synthesis',
    name: '語音合成',
    description: '測試基本語音合成功能'
  },
  {
    id: 'analyst-synthesis',
    name: '分析師語音合成',
    description: '測試分析師專用語音合成'
  },
  {
    id: 'store-integration',
    name: 'Store整合',
    description: '測試Zustand狀態管理整合'
  }
];

const DEMO_TEXTS = {
  fundamentals: '根據最新財報分析，台積電第三季營收成長15%，毛利率維持在52%的高水準，主要受惠於先進製程需求強勁。',
  news: '突發消息：央行今日宣布升息半碼，基準利率調升至1.875%，預期將對房地產市場產生降溫效應。',
  risk: '風險提醒：近期美股波動加劇，VIX恐慌指數升至28，建議投資人控制持股比重，避免過度槓桿操作。',
  sentiment: '市場情緒分析顯示，投資者信心指數連續三週下滑，主要擔憂通膨壓力持續，建議採取防禦性投資策略。',
  investment: '投資建議：建議將投資組合調整為股票40%、債券35%、商品15%、現金10%，以因應市場不確定性。',
  'taiwan-market': '台股盤中分析：加權指數目前站穩15,500點，電子股領漲，外資連續五日買超，短線偏多格局維持。'
};

export const TTSTestDemo: React.FC<TTSTestDemoProps> = ({
  showFullApp = true,
  showTestResults = true,
  autoRunTests = true
}) => {
  // 狀態管理
  const [activeTab, setActiveTab] = useState<'app' | 'tests' | 'demo'>('app');
  const [testResults, setTestResults] = useState<TestResult[]>(
    TEST_SCENARIOS.map(scenario => ({
      testName: scenario.name,
      status: 'pending',
      message: scenario.description
    }))
  );
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [selectedAnalyst, setSelectedAnalyst] = useState('fundamentals');
  const [demoText, setDemoText] = useState(DEMO_TEXTS.fundamentals);

  // Store
  const { voices, error: storeError } = useVoiceStore();
  
  // 服務實例
  const ttsService = TTSApiService.getInstance();

  // 更新測試結果
  const updateTestResult = (testName: string, status: TestResult['status'], message: string, duration?: number) => {
    setTestResults(prev => prev.map(result => 
      result.testName === testName 
        ? { ...result, status, message, duration }
        : result
    ));
  };

  // 執行單個測試
  const runSingleTest = async (testId: string, testName: string): Promise<boolean> => {
    const startTime = Date.now();
    updateTestResult(testName, 'running', '執行中...');

    try {
      switch (testId) {
        case 'api-connection':
          await ttsService.healthCheck();
          updateTestResult(testName, 'passed', 'API連接正常', Date.now() - startTime);
          return true;

        case 'voice-list':
          const voicesResponse = await ttsService.getVoices();
          if (voicesResponse && Array.isArray(voicesResponse)) {
            updateTestResult(testName, 'passed', `成功加載 ${voicesResponse.length} 個語音模型`, Date.now() - startTime);
            return true;
          }
          throw new Error('語音列表格式錯誤');

        case 'analyst-config':
          const configs = ttsService.getAllAnalystVoiceConfigs();
          if (configs.length === 6) {
            updateTestResult(testName, 'passed', `成功加載 ${configs.length} 個分析師配置`, Date.now() - startTime);
            return true;
          }
          throw new Error('分析師配置數量不正確');

        case 'voice-synthesis':
          const testBlob = await ttsService.synthesizeSpeech('這是語音合成測試', 'zh-TW-HsiaoChenNeural');
          if (testBlob && testBlob.size > 0) {
            updateTestResult(testName, 'passed', `合成成功，音頻大小：${(testBlob.size / 1024).toFixed(1)}KB`, Date.now() - startTime);
            return true;
          }
          throw new Error('語音合成失敗');

        case 'analyst-synthesis':
          const analystBlob = await ttsService.synthesizeAnalystSpeech('fundamentals', '這是分析師語音測試', 'analysis');
          if (analystBlob && analystBlob.size > 0) {
            updateTestResult(testName, 'passed', `分析師語音合成成功，音頻大小：${(analystBlob.size / 1024).toFixed(1)}KB`, Date.now() - startTime);
            return true;
          }
          throw new Error('分析師語音合成失敗');

        case 'store-integration':
          if (typeof useVoiceStore === 'function' && !storeError) {
            updateTestResult(testName, 'passed', 'Zustand Store整合正常', Date.now() - startTime);
            return true;
          }
          throw new Error('Store整合失敗');

        default:
          throw new Error('未知的測試類型');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '測試失敗';
      updateTestResult(testName, 'failed', errorMessage, Date.now() - startTime);
      return false;
    }
  };

  // 執行所有測試
  const runAllTests = async () => {
    if (isRunningTests) return;
    
    setIsRunningTests(true);
    let passedCount = 0;

    for (const scenario of TEST_SCENARIOS) {
      const success = await runSingleTest(scenario.id, scenario.name);
      if (success) passedCount++;
      
      // 測試間間隔
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    setIsRunningTests(false);
    console.log(`測試完成：${passedCount}/${TEST_SCENARIOS.length} 通過`);
  };

  // 處理分析師選擇
  const handleAnalystChange = (analystId: string) => {
    setSelectedAnalyst(analystId);
    setDemoText(DEMO_TEXTS[analystId as keyof typeof DEMO_TEXTS] || DEMO_TEXTS.fundamentals);
  };

  // 自動運行測試
  useEffect(() => {
    if (autoRunTests && activeTab === 'tests') {
      const timer = setTimeout(runAllTests, 1000);
      return () => clearTimeout(timer);
    }
  }, [autoRunTests, activeTab]);

  // 獲取測試統計
  const testStats = {
    total: testResults.length,
    passed: testResults.filter(r => r.status === 'passed').length,
    failed: testResults.filter(r => r.status === 'failed').length,
    running: testResults.filter(r => r.status === 'running').length,
    pending: testResults.filter(r => r.status === 'pending').length
  };

  return (
    <div className="tts-test-demo">
      {/* 標籤導航 */}
      <div className="demo-tabs">
        <button
          className={`demo-tab ${activeTab === 'app' ? 'active' : ''}`}
          onClick={() => setActiveTab('app')}
        >
          🎙️ 完整應用
        </button>
        <button
          className={`demo-tab ${activeTab === 'tests' ? 'active' : ''}`}
          onClick={() => setActiveTab('tests')}
        >
          🧪 功能測試
        </button>
        <button
          className={`demo-tab ${activeTab === 'demo' ? 'active' : ''}`}
          onClick={() => setActiveTab('demo')}
        >
          🎯 快速演示
        </button>
      </div>

      {/* 內容區域 */}
      <div className="demo-content">
        {/* 完整應用標籤 */}
        {activeTab === 'app' && showFullApp && (
          <div className="app-section">
            <h2>TTS語音服務完整應用</h2>
            <p>這是完整的TTS語音服務應用程式，包含六大數位分析師語音合成功能。</p>
            <TTSMainApp
              className="demo-app"
              showNavigation={true}
              enableAdvancedFeatures={true}
              theme="light"
            />
          </div>
        )}

        {/* 功能測試標籤 */}
        {activeTab === 'tests' && showTestResults && (
          <div className="tests-section">
            <div className="test-header">
              <h2>TTS系統功能測試</h2>
              <div className="test-controls">
                <button 
                  onClick={runAllTests} 
                  disabled={isRunningTests}
                  className="run-tests-btn"
                >
                  {isRunningTests ? '🔄 測試進行中...' : '▶️ 執行測試'}
                </button>
                <div className="test-stats">
                  <span className="stat passed">✅ {testStats.passed}</span>
                  <span className="stat failed">❌ {testStats.failed}</span>
                  <span className="stat running">⏳ {testStats.running}</span>
                  <span className="stat pending">⏸️ {testStats.pending}</span>
                </div>
              </div>
            </div>

            <div className="test-results">
              {testResults.map((result, index) => (
                <div key={index} className={`test-result ${result.status}`}>
                  <div className="test-info">
                    <div className="test-name">{result.testName}</div>
                    <div className="test-message">{result.message}</div>
                    {result.duration && (
                      <div className="test-duration">{result.duration}ms</div>
                    )}
                  </div>
                  <div className="test-status">
                    {result.status === 'pending' && '⏸️'}
                    {result.status === 'running' && '⏳'}
                    {result.status === 'passed' && '✅'}
                    {result.status === 'failed' && '❌'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 快速演示標籤 */}
        {activeTab === 'demo' && (
          <div className="demo-section">
            <h2>TTS快速演示</h2>
            
            {/* 分析師選擇 */}
            <div className="analyst-selector">
              <h3>選擇分析師</h3>
              <div className="analyst-buttons">
                {Object.entries(DEMO_TEXTS).map(([analystId, text]) => (
                  <button
                    key={analystId}
                    className={`analyst-btn ${selectedAnalyst === analystId ? 'active' : ''}`}
                    onClick={() => handleAnalystChange(analystId)}
                  >
                    {analystId === 'fundamentals' && '📊 基本面'}
                    {analystId === 'news' && '📰 新聞'}
                    {analystId === 'risk' && '⚠️ 風險'}
                    {analystId === 'sentiment' && '💭 情緒'}
                    {analystId === 'investment' && '💰 投資'}
                    {analystId === 'taiwan-market' && '🇹🇼 台股'}
                  </button>
                ))}
              </div>
            </div>

            {/* 文字內容 */}
            <div className="demo-text">
              <h3>演示文字</h3>
              <textarea
                value={demoText}
                onChange={(e) => setDemoText(e.target.value)}
                placeholder="輸入要合成的文字..."
                rows={4}
              />
            </div>

            {/* 語音播放器 */}
            <div className="demo-player">
              <h3>語音播放</h3>
              <VoicePlayer
                text={demoText}
                voiceId="zh-TW-HsiaoChenNeural"
                showControls={true}
                className="demo-voice-player"
              />
            </div>

            {/* 分析師面板 */}
            <div className="demo-analyst-panel">
              <h3>分析師面板</h3>
              <AnalystVoicePanel
                className="demo-panel"
                showQuickActions={true}
                enableQueueMode={true}
                maxVisibleAnalysts={3}
                onAnalystSelect={(analystId) => console.log('選擇分析師:', analystId)}
              />
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        .tts-test-demo {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
          font-family: 'Inter', sans-serif;
        }

        .demo-tabs {
          display: flex;
          gap: 4px;
          margin-bottom: 24px;
          border-bottom: 1px solid #e2e8f0;
        }

        .demo-tab {
          background: transparent;
          border: none;
          padding: 12px 20px;
          cursor: pointer;
          border-radius: 8px 8px 0 0;
          font-weight: 500;
          color: #64748b;
          transition: all 0.2s ease;
        }

        .demo-tab:hover {
          color: #475569;
          background: #f8fafc;
        }

        .demo-tab.active {
          color: #3b82f6;
          background: #ffffff;
          border-bottom: 2px solid #3b82f6;
        }

        .demo-content {
          background: #ffffff;
          border-radius: 0 8px 8px 8px;
          padding: 24px;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .test-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
          flex-wrap: wrap;
          gap: 16px;
        }

        .test-controls {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .run-tests-btn {
          background: linear-gradient(135deg, #3b82f6, #2563eb);
          color: #ffffff;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .run-tests-btn:hover:not(:disabled) {
          background: linear-gradient(135deg, #2563eb, #1d4ed8);
          transform: translateY(-1px);
        }

        .run-tests-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
          transform: none;
        }

        .test-stats {
          display: flex;
          gap: 12px;
        }

        .stat {
          font-size: 14px;
          font-weight: 500;
          padding: 4px 8px;
          border-radius: 4px;
        }

        .stat.passed {
          background: rgba(34, 197, 94, 0.1);
          color: #22c55e;
        }

        .stat.failed {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .stat.running {
          background: rgba(245, 158, 11, 0.1);
          color: #f59e0b;
        }

        .stat.pending {
          background: rgba(156, 163, 175, 0.1);
          color: #9ca3af;
        }

        .test-results {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .test-result {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 16px;
          border-radius: 8px;
          border: 1px solid #e2e8f0;
          transition: all 0.2s ease;
        }

        .test-result.running {
          background: rgba(245, 158, 11, 0.05);
          border-color: #f59e0b;
        }

        .test-result.passed {
          background: rgba(34, 197, 94, 0.05);
          border-color: #22c55e;
        }

        .test-result.failed {
          background: rgba(239, 68, 68, 0.05);
          border-color: #ef4444;
        }

        .test-info {
          flex: 1;
        }

        .test-name {
          font-weight: 600;
          color: #1e293b;
          margin-bottom: 4px;
        }

        .test-message {
          color: #64748b;
          font-size: 14px;
        }

        .test-duration {
          color: #94a3b8;
          font-size: 12px;
          margin-top: 4px;
        }

        .test-status {
          font-size: 18px;
          margin-left: 16px;
        }

        .analyst-selector {
          margin-bottom: 24px;
        }

        .analyst-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 8px;
        }

        .analyst-btn {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          padding: 8px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .analyst-btn:hover {
          background: #f1f5f9;
          border-color: #cbd5e1;
        }

        .analyst-btn.active {
          background: linear-gradient(135deg, #3b82f6, #2563eb);
          color: #ffffff;
          border-color: #3b82f6;
        }

        .demo-text {
          margin-bottom: 24px;
        }

        .demo-text textarea {
          width: 100%;
          padding: 12px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          font-family: inherit;
          font-size: 14px;
          resize: vertical;
        }

        .demo-text textarea:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .demo-player,
        .demo-analyst-panel {
          margin-bottom: 24px;
        }

        h2 {
          color: #1e293b;
          margin-bottom: 8px;
        }

        h3 {
          color: #374151;
          margin-bottom: 8px;
          font-size: 16px;
        }

        @media (max-width: 768px) {
          .tts-test-demo {
            padding: 12px;
          }

          .demo-content {
            padding: 16px;
          }

          .test-header {
            flex-direction: column;
            align-items: stretch;
          }

          .test-controls {
            justify-content: space-between;
          }

          .analyst-buttons {
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
};

export default TTSTestDemo;