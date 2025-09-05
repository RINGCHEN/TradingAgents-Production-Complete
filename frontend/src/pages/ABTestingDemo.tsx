import React, { useState } from 'react';
import ABTestingSystem from '../components/ABTestingSystem';
import './ABTestingDemo.css';

// A/B測試演示頁面
// Task 6.2 - A/B測試框架建立的演示實現

interface DemoScenario {
  id: string;
  name: string;
  description: string;
  testConfig: {
    name: string;
    description: string;
    primary_metric: string;
    variants: Array<{
      name: string;
      type: string;
      traffic_weight: number;
      config: any;
    }>;
  };
}

const ABTestingDemo: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState<'scenarios' | 'system'>('scenarios');

  // 預定義的測試場景
  const demoScenarios: DemoScenario[] = [
    {
      id: 'landing-page-cta',
      name: '著陸頁CTA按鈕測試',
      description: '測試不同的CTA按鈕文字和顏色對轉換率的影響',
      testConfig: {
        name: '著陸頁CTA按鈕優化測試',
        description: '比較「立即開始」vs「免費試用」按鈕文字的轉換效果',
        primary_metric: 'conversion_rate',
        variants: [
          {
            name: '控制組 - 立即開始',
            type: 'control',
            traffic_weight: 50,
            config: {
              button_text: '立即開始',
              button_color: '#3498db',
              button_size: 'large'
            }
          },
          {
            name: '實驗組 - 免費試用',
            type: 'treatment',
            traffic_weight: 50,
            config: {
              button_text: '免費試用',
              button_color: '#27ae60',
              button_size: 'large'
            }
          }
        ]
      }
    },
    {
      id: 'pricing-display',
      name: '價格展示方式測試',
      description: '測試不同的價格展示方式對用戶購買決策的影響',
      testConfig: {
        name: '價格展示優化測試',
        description: '比較月付 vs 年付優先展示對訂閱轉換的影響',
        primary_metric: 'signup_rate',
        variants: [
          {
            name: '控制組 - 月付優先',
            type: 'control',
            traffic_weight: 50,
            config: {
              default_plan: 'monthly',
              highlight_savings: false,
              price_format: 'standard'
            }
          },
          {
            name: '實驗組 - 年付優先',
            type: 'treatment',
            traffic_weight: 50,
            config: {
              default_plan: 'yearly',
              highlight_savings: true,
              price_format: 'with_discount'
            }
          }
        ]
      }
    },
    {
      id: 'social-proof',
      name: '社會證明元素測試',
      description: '測試添加用戶評價和使用統計對信任度的影響',
      testConfig: {
        name: '社會證明優化測試',
        description: '比較有無社會證明元素對用戶註冊率的影響',
        primary_metric: 'signup_rate',
        variants: [
          {
            name: '控制組 - 無社會證明',
            type: 'control',
            traffic_weight: 50,
            config: {
              show_testimonials: false,
              show_user_count: false,
              show_ratings: false
            }
          },
          {
            name: '實驗組 - 完整社會證明',
            type: 'treatment',
            traffic_weight: 50,
            config: {
              show_testimonials: true,
              show_user_count: true,
              show_ratings: true,
              testimonial_count: 3
            }
          }
        ]
      }
    },
    {
      id: 'form-length',
      name: '註冊表單長度測試',
      description: '測試簡化註冊表單對完成率的影響',
      testConfig: {
        name: '註冊表單優化測試',
        description: '比較長表單 vs 短表單對註冊完成率的影響',
        primary_metric: 'conversion_rate',
        variants: [
          {
            name: '控制組 - 完整表單',
            type: 'control',
            traffic_weight: 50,
            config: {
              fields: ['name', 'email', 'phone', 'company', 'job_title', 'industry'],
              required_fields: ['name', 'email', 'phone', 'company'],
              form_steps: 2
            }
          },
          {
            name: '實驗組 - 簡化表單',
            type: 'treatment',
            traffic_weight: 50,
            config: {
              fields: ['name', 'email'],
              required_fields: ['name', 'email'],
              form_steps: 1
            }
          }
        ]
      }
    }
  ];

  const renderScenarioCard = (scenario: DemoScenario) => (
    <div key={scenario.id} className="scenario-card">
      <div className="scenario-header">
        <h3>{scenario.name}</h3>
      </div>
      
      <div className="scenario-body">
        <p>{scenario.description}</p>
        
        <div className="scenario-details">
          <div className="detail-item">
            <span className="detail-label">主要指標:</span>
            <span className="detail-value">{scenario.testConfig.primary_metric}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">變體數量:</span>
            <span className="detail-value">{scenario.testConfig.variants.length}</span>
          </div>
        </div>
        
        <div className="variants-preview">
          <h4>測試變體:</h4>
          {scenario.testConfig.variants.map((variant, index) => (
            <div key={index} className="variant-preview">
              <span className={`variant-badge ${variant.type}`}>
                {variant.name}
              </span>
              <span className="variant-weight">{variant.traffic_weight}%</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="scenario-actions">
        <button 
          className="btn btn-primary"
          onClick={() => {
            setSelectedScenario(scenario.id);
            setDemoMode('system');
          }}
        >
          使用此場景
        </button>
      </div>
    </div>
  );

  const renderScenarios = () => (
    <div className="demo-scenarios">
      <div className="scenarios-header">
        <h2>A/B測試場景演示</h2>
        <p>選擇一個預設場景來體驗A/B測試系統的功能</p>
      </div>
      
      <div className="scenarios-grid">
        {demoScenarios.map(renderScenarioCard)}
      </div>
      
      <div className="demo-actions">
        <button 
          className="btn btn-secondary"
          onClick={() => setDemoMode('system')}
        >
          直接使用系統
        </button>
      </div>
    </div>
  );

  const renderSystemDemo = () => {
    const selectedScenarioData = selectedScenario 
      ? demoScenarios.find(s => s.id === selectedScenario)
      : null;

    return (
      <div className="system-demo">
        <div className="demo-header">
          <h2>A/B測試系統演示</h2>
          {selectedScenarioData && (
            <div className="selected-scenario-info">
              <span>當前場景: {selectedScenarioData.name}</span>
              <button 
                className="btn btn-link"
                onClick={() => {
                  setSelectedScenario(null);
                  setDemoMode('scenarios');
                }}
              >
                更換場景
              </button>
            </div>
          )}
        </div>
        
        <ABTestingSystem apiBaseUrl="/api/ab-testing" />
        
        {selectedScenarioData && (
          <div className="scenario-context">
            <h3>場景說明</h3>
            <div className="context-card">
              <h4>{selectedScenarioData.name}</h4>
              <p>{selectedScenarioData.description}</p>
              
              <div className="context-details">
                <h5>測試配置:</h5>
                <ul>
                  <li>主要指標: {selectedScenarioData.testConfig.primary_metric}</li>
                  <li>變體數量: {selectedScenarioData.testConfig.variants.length}</li>
                  <li>流量分配: 各50%</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="ab-testing-demo">
      <div className="demo-navigation">
        <button 
          className={`nav-btn ${demoMode === 'scenarios' ? 'active' : ''}`}
          onClick={() => setDemoMode('scenarios')}
        >
          測試場景
        </button>
        <button 
          className={`nav-btn ${demoMode === 'system' ? 'active' : ''}`}
          onClick={() => setDemoMode('system')}
        >
          系統演示
        </button>
      </div>
      
      <div className="demo-content">
        {demoMode === 'scenarios' ? renderScenarios() : renderSystemDemo()}
      </div>
      
      <div className="demo-footer">
        <div className="feature-highlights">
          <h3>系統特色</h3>
          <div className="features-grid">
            <div className="feature-item">
              <div className="feature-icon">🎯</div>
              <h4>多變量測試</h4>
              <p>支援同時測試多個變體，找出最佳組合</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">📊</div>
              <h4>統計顯著性</h4>
              <p>自動計算統計顯著性，確保測試結果可靠</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">⚡</div>
              <h4>實時監控</h4>
              <p>即時追蹤測試進度和轉換率變化</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🎛️</div>
              <h4>靈活管理</h4>
              <p>隨時啟動、暫停或結束測試</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ABTestingDemo;