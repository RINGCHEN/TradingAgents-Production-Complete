import React from 'react';
import { Link } from 'react-router-dom';

const TermsPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">服務條款</h1>
        
        <div className="prose max-w-none">
          <p className="text-gray-600 mb-6">
            歡迎使用 TradingAgents 服務。使用我們的服務即表示您同意遵守以下條款。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">服務說明</h2>
          <p className="mb-6">
            TradingAgents 提供AI驅動的投資分析服務，包括但不限於股票分析、投資建議、
            市場監控等功能。我們的服務旨在協助用戶做出更明智的投資決策。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">用戶責任</h2>
          <ul className="list-disc pl-6 mb-6">
            <li>提供真實、準確的註冊資訊</li>
            <li>妥善保管帳戶資訊和密碼</li>
            <li>遵守當地法律法規</li>
            <li>不得濫用服務或進行惡意行為</li>
            <li>理解投資風險並自負責任</li>
          </ul>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">投資風險聲明</h2>
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
            <p className="font-medium text-yellow-800">重要提醒：</p>
            <p className="text-yellow-700">
              投資有風險，所有投資決策應基於您自己的判斷。TradingAgents 提供的分析和建議
              僅供參考，不構成投資建議。過去的績效不代表未來的結果。
            </p>
          </div>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">服務可用性</h2>
          <p className="mb-6">
            我們努力確保服務的可用性，但不保證服務不會中斷。我們保留因維護、
            升級或其他原因暫時中斷服務的權利。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">知識產權</h2>
          <p className="mb-6">
            TradingAgents 的所有內容、技術和服務均受知識產權法保護。
            未經授權不得複製、分發或用於商業用途。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">免責聲明</h2>
          <p className="mb-6">
            在法律允許的最大範圍內，TradingAgents 對因使用服務而產生的任何直接、
            間接、偶然或後果性損害不承擔責任。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">條款修改</h2>
          <p className="mb-6">
            我們保留隨時修改這些條款的權利。重大變更會提前通知用戶。
            繼續使用服務即表示接受修改後的條款。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">聯繫我們</h2>
          <p className="mb-6">
            如對本條款有任何疑問，請通過 
            <Link to="/contact" className="text-blue-600 hover:text-blue-800 mx-1">
              聯繫我們
            </Link>
            頁面與我們取得聯繫。
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

export default TermsPage;