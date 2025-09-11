import React, { useState } from 'react';
import UpgradePromptComponent from './UpgradePromptComponent';
import './UpgradePromptComponent.css';

/**
 * 升級提示測試組件 - 測試GEMINI新的upgrade_prompt格式
 */

interface TestScenario {
  id: string;
  name: string;
  userTier: 'visitor' | 'trial' | 'free' | 'paid';
  upgradePrompt: string | {
    title: string;
    value_prop: string;
    cta: string;
  };
  description: string;
}

const UpgradePromptTest: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<string>('gemini_visitor');

  // 測試場景定義
  const testScenarios: TestScenario[] = [
    // GEMINI 新格式測試
    {
      id: 'gemini_visitor',
      name: 'GEMINI 訪客升級提示',
      userTier: 'visitor',
      upgradePrompt: {
        title: '解鎖完整 AI 投資建議',
        value_prop: '本次分析的核心買賣建議和目標價位已被隱藏。',
        cta: '立即註冊'
      },
      description: 'GEMINI 提供的訪客用戶結構化升級提示'
    },
    {
      id: 'gemini_free',
      name: 'GEMINI 免費會員升級提示',
      userTier: 'free',
      upgradePrompt: {
        title: '解鎖完整 AI 投資建議',
        value_prop: '本次分析的核心買賣建議和目標價位已被隱藏。',
        cta: '立即升級'
      },
      description: 'GEMINI 提供的免費會員結構化升級提示'
    },
    {
      id: 'gemini_trial',
      name: 'GEMINI 試用會員提醒',
      userTier: 'trial',
      upgradePrompt: {
        title: '試用期即將結束',
        value_prop: '您的7天免費試用還有2天結束，請及時升級以繼續享受專業服務。',
        cta: '立即升級'
      },
      description: 'GEMINI 提供的試用會員升級提醒'
    },
    // 舊格式兼容性測試
    {
      id: 'legacy_visitor',
      name: '舊格式 - 訪客提示',
      userTier: 'visitor',
      upgradePrompt: '註冊立即享受7天完整功能體驗！',
      description: '測試向下兼容舊的字符串格式'
    },
    {
      id: 'legacy_free',
      name: '舊格式 - 免費會員提示',
      userTier: 'free',
      upgradePrompt: '升級獲得專業投資建議，提升投資決策準確度',
      description: '測試向下兼容舊的字符串格式'
    },
    // 邊界情況測試
    {
      id: 'empty_prompt',
      name: '空提示測試',
      userTier: 'free',
      upgradePrompt: '',
      description: '測試空字符串提示的處理'
    },
    {
      id: 'paid_user',
      name: '付費用戶測試',
      userTier: 'paid',
      upgradePrompt: {
        title: '這不應該顯示',
        value_prop: '付費用戶不應該看到升級提示',
        cta: '不會顯示'
      },
      description: '測試付費用戶不顯示升級提示'
    }
  ];

  const selectedTest = testScenarios.find(s => s.id === selectedScenario);

  const handleScenarioChange = (scenarioId: string) => {
    setSelectedScenario(scenarioId);
  };

  const handleCustomUpgrade = () => {
    alert(`自定義升級點擊處理 - 用戶層級: ${selectedTest?.userTier}`);
  };

  return (
    <div className="upgrade-prompt-test">
      <div className="test-header">
        <h2>🧪 升級提示測試工具</h2>
        <p>測試 GEMINI 結構化 upgrade_prompt 格式和舊格式兼容性</p>
      </div>

      <div className="test-controls">
        <h3>測試場景選擇</h3>
        <div className="scenario-grid">
          {testScenarios.map(scenario => (
            <button
              key={scenario.id}
              className={`scenario-btn ${selectedScenario === scenario.id ? 'active' : ''}`}
              onClick={() => handleScenarioChange(scenario.id)}
            >
              <div className="scenario-title">{scenario.name}</div>
              <div className="scenario-desc">{scenario.description}</div>
              <div className="scenario-tier">用戶層級: {scenario.userTier}</div>
            </button>
          ))}
        </div>
      </div>

      {selectedTest && (
        <div className="test-display">
          <div className="test-info">
            <h3>當前測試場景</h3>
            <div className="test-details">
              <div><strong>場景名稱:</strong> {selectedTest.name}</div>
              <div><strong>用戶層級:</strong> {selectedTest.userTier}</div>
              <div><strong>描述:</strong> {selectedTest.description}</div>
              <div className="prompt-data">
                <strong>提示數據:</strong>
                <pre>{JSON.stringify(selectedTest.upgradePrompt, null, 2)}</pre>
              </div>
            </div>
          </div>

          <div className="test-render">
            <h3>渲染效果</h3>
            <div className="render-container">
              <UpgradePromptComponent
                upgradePrompt={selectedTest.upgradePrompt}
                userTier={selectedTest.userTier}
                onUpgradeClick={handleCustomUpgrade}
                className="test-component"
              />
            </div>
          </div>
        </div>
      )}

      <div className="test-footer">
        <h3>測試說明</h3>
        <ul>
          <li>✅ <strong>GEMINI 新格式</strong>: 支援 title, value_prop, cta 結構化數據</li>
          <li>✅ <strong>舊格式兼容</strong>: 向下兼容字符串格式的升級提示</li>
          <li>✅ <strong>主題樣式</strong>: 根據用戶層級自動應用不同的視覺主題</li>
          <li>✅ <strong>響應式設計</strong>: 支援各種螢幕尺寸和設備</li>
          <li>✅ <strong>無障礙設計</strong>: 支援鍵盤導航和螢幕閱讀器</li>
          <li>⚠️ <strong>付費用戶邏輯</strong>: 付費用戶不顯示升級提示</li>
        </ul>
      </div>

      <style jsx>{`
        .upgrade-prompt-test {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .test-header {
          text-align: center;
          margin-bottom: 30px;
          padding: 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-radius: 12px;
        }

        .test-header h2 {
          margin: 0 0 8px 0;
          font-size: 1.8rem;
        }

        .test-controls {
          margin-bottom: 30px;
        }

        .test-controls h3 {
          margin-bottom: 16px;
          color: #2c3e50;
        }

        .scenario-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 16px;
        }

        .scenario-btn {
          background: white;
          border: 2px solid #e9ecef;
          border-radius: 12px;
          padding: 16px;
          cursor: pointer;
          transition: all 0.3s ease;
          text-align: left;
        }

        .scenario-btn:hover {
          border-color: #667eea;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        }

        .scenario-btn.active {
          border-color: #667eea;
          background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
          box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
        }

        .scenario-title {
          font-weight: 600;
          color: #2c3e50;
          margin-bottom: 4px;
          font-size: 1rem;
        }

        .scenario-desc {
          font-size: 0.9rem;
          color: #6c757d;
          margin-bottom: 6px;
          line-height: 1.4;
        }

        .scenario-tier {
          font-size: 0.8rem;
          color: #495057;
          font-weight: 500;
          background: #f8f9fa;
          padding: 4px 8px;
          border-radius: 4px;
          display: inline-block;
        }

        .test-display {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 30px;
          margin-bottom: 30px;
        }

        .test-info, .test-render {
          background: white;
          border: 1px solid #e9ecef;
          border-radius: 12px;
          padding: 20px;
        }

        .test-info h3, .test-render h3 {
          margin: 0 0 16px 0;
          color: #2c3e50;
          border-bottom: 2px solid #f1f3f4;
          padding-bottom: 8px;
        }

        .test-details div {
          margin-bottom: 12px;
          font-size: 0.95rem;
        }

        .test-details strong {
          color: #495057;
        }

        .prompt-data {
          margin-top: 16px;
        }

        .prompt-data pre {
          background: #f8f9fa;
          border: 1px solid #e9ecef;
          border-radius: 6px;
          padding: 12px;
          font-size: 0.85rem;
          overflow-x: auto;
          color: #495057;
        }

        .render-container {
          background: #f8f9fa;
          border-radius: 8px;
          padding: 20px;
          min-height: 200px;
        }

        .test-component {
          margin: 0;
        }

        .test-footer {
          background: #f8f9fa;
          border: 1px solid #e9ecef;
          border-radius: 12px;
          padding: 20px;
        }

        .test-footer h3 {
          margin: 0 0 16px 0;
          color: #2c3e50;
        }

        .test-footer ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .test-footer li {
          margin: 8px 0;
          padding: 8px 12px;
          background: white;
          border-radius: 6px;
          border-left: 4px solid #28a745;
        }

        .test-footer li:last-child {
          border-left-color: #ffc107;
        }

        @media (max-width: 768px) {
          .test-display {
            grid-template-columns: 1fr;
          }
          
          .scenario-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default UpgradePromptTest;