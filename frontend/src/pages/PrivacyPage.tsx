import React from 'react';
import { Link } from 'react-router-dom';

const PrivacyPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">隱私權政策</h1>
        
        <div className="prose max-w-none">
          <p className="text-gray-600 mb-6">
            TradingAgents 致力於保護您的隱私權。本政策說明我們如何收集、使用和保護您的個人資訊。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">資訊收集</h2>
          <p className="mb-4">我們可能收集以下類型的資訊：</p>
          <ul className="list-disc pl-6 mb-6">
            <li>帳戶註冊資訊（姓名、電子郵件、電話號碼）</li>
            <li>使用服務時的行為數據</li>
            <li>技術資訊（IP位址、瀏覽器類型、裝置資訊）</li>
            <li>投資偏好和風險承受度資料</li>
          </ul>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">資訊使用</h2>
          <p className="mb-4">我們使用收集的資訊用於：</p>
          <ul className="list-disc pl-6 mb-6">
            <li>提供個人化的AI投資分析服務</li>
            <li>改善服務品質和用戶體驗</li>
            <li>發送重要的服務通知</li>
            <li>防範欺詐和確保系統安全</li>
          </ul>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">資訊保護</h2>
          <p className="mb-6">
            我們採用業界標準的安全措施來保護您的個人資訊，包括資料加密、存取控制和定期安全審核。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">資訊分享</h2>
          <p className="mb-6">
            除非獲得您的明確同意或法律要求，我們不會向第三方分享您的個人資訊。
          </p>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">您的權利</h2>
          <p className="mb-4">您有權：</p>
          <ul className="list-disc pl-6 mb-6">
            <li>查看和更新您的個人資訊</li>
            <li>要求刪除您的帳戶和相關資料</li>
            <li>選擇退出非必要的通訊</li>
            <li>要求資料可攜性</li>
          </ul>
          
          <h2 className="text-2xl font-semibold mt-8 mb-4">政策更新</h2>
          <p className="mb-6">
            我們可能會定期更新本隱私權政策。重大變更時，我們會以適當方式通知您。
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

export default PrivacyPage;