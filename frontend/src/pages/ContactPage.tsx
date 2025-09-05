import React from 'react';
import { Link } from 'react-router-dom';

const ContactPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">聯繫我們</h1>
        
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h2 className="text-2xl font-semibold mb-4">聯繫資訊</h2>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium">客服信箱</h3>
                <p className="text-gray-600">support@tradingagents.com</p>
              </div>
              <div>
                <h3 className="font-medium">技術支援</h3>
                <p className="text-gray-600">tech@tradingagents.com</p>
              </div>
              <div>
                <h3 className="font-medium">商務合作</h3>
                <p className="text-gray-600">business@tradingagents.com</p>
              </div>
              <div>
                <h3 className="font-medium">服務時間</h3>
                <p className="text-gray-600">週一至週五 9:00-18:00 (GMT+8)</p>
              </div>
            </div>
          </div>
          
          <div>
            <h2 className="text-2xl font-semibold mb-4">常見問題</h2>
            <p className="text-gray-600 mb-4">
              在聯繫我們之前，您可以查看我們的幫助中心，可能已經有您需要的答案。
            </p>
            <Link 
              to="/help" 
              className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              前往幫助中心
            </Link>
          </div>
        </div>
        
        <div className="mt-12">
          <h2 className="text-2xl font-semibold mb-4">意見反饋</h2>
          <p className="text-gray-600">
            我們非常重視您的意見和建議。如果您對我們的服務有任何想法，請隨時與我們聯繫。
            您的反饋將幫助我們不斷改進服務品質。
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

export default ContactPage;