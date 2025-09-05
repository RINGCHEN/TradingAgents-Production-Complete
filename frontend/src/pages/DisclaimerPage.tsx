import React from 'react';
import { Link } from 'react-router-dom';

const DisclaimerPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">免責聲明</h1>
        
        <div className="prose max-w-none">
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-8">
            <p className="font-medium text-red-800">重要警告：</p>
            <p className="text-red-700">
              投資涉及風險，您可能會損失部分或全部投資本金。在做出任何投資決策之前，
              請仔細考慮您的財務狀況和風險承受能力。
            </p>
          </div>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">一般免責聲明</h2>
          <p className="mb-6">
            TradingAgents 提供的所有資訊、分析、建議和服務僅供參考用途，
            不構成任何形式的投資建議、金融建議或交易建議。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">AI分析限制</h2>
          <ul className="list-disc pl-6 mb-6">
            <li>AI分析基於歷史數據和模型，無法預測未來市場變化</li>
            <li>市場條件瞬息萬變，AI分析可能存在延遲或不準確性</li>
            <li>分析結果不能替代專業的財務顧問建議</li>
            <li>技術故障或數據錯誤可能影響分析準確性</li>
          </ul>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">投資風險</h2>
          <div className="space-y-4 mb-6">
            <div>
              <h3 className="font-semibold">市場風險</h3>
              <p className="text-gray-600">股票價格可能因市場條件、經濟因素等大幅波動</p>
            </div>
            <div>
              <h3 className="font-semibold">流動性風險</h3>
              <p className="text-gray-600">某些投資可能難以在理想價格或時間點出售</p>
            </div>
            <div>
              <h3 className="font-semibold">信用風險</h3>
              <p className="text-gray-600">發行機構可能無法履行其財務義務</p>
            </div>
            <div>
              <h3 className="font-semibold">匯率風險</h3>
              <p className="text-gray-600">投資外幣資產可能面臨匯率波動風險</p>
            </div>
          </div>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">數據來源聲明</h2>
          <p className="mb-6">
            我們的數據來源包括但不限於公開市場資訊、第三方數據提供商和官方統計機構。
            我們不保證數據的完整性、準確性或及時性。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">責任限制</h2>
          <p className="mb-6">
            TradingAgents、其員工、代理人或關聯公司對於：
          </p>
          <ul className="list-disc pl-6 mb-6">
            <li>因使用我們服務而產生的任何投資損失</li>
            <li>服務中斷、數據錯誤或技術故障</li>
            <li>第三方數據的準確性或可靠性</li>
            <li>因依賴我們服務而做出的投資決策</li>
          </ul>
          <p className="mb-6">均不承擔任何責任。</p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">專業建議</h2>
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
            <p className="text-blue-800">
              <strong>建議：</strong>在做出重大投資決策之前，請諮詢合格的財務顧問、
              會計師或其他專業人士，以確保投資策略符合您的個人財務狀況和目標。
            </p>
          </div>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">監管聲明</h2>
          <p className="mb-6">
            TradingAgents 不是註冊的投資顧問或經紀商。我們不代表客戶進行交易，
            也不持有客戶資金。所有投資決策均由用戶自行做出。
          </p>
          
          <p className="text-sm text-gray-500 mt-8">
            最後更新：2025年1月
          </p>
        </div>
        
        <div className="mt-8">
          <Link 
            to="/" 
            className="text-blue-600 hover:text-blue-800 transition-colors"
          >
            ← 返回首頁
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DisclaimerPage;