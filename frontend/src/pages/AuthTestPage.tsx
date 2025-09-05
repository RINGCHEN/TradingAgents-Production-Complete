/**
 * AuthTestPage - 認證系統測試頁面
 * 用於測試和演示修復後的認證系統功能
 */

import React from 'react';
import AuthenticationDemo from '../components/AuthenticationDemo';

const AuthTestPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-4">
              認證系統測試頁面
            </h1>
            <p className="text-gray-600 text-lg">
              此頁面用於測試和演示修復後的認證系統功能，包括錯誤處理和訪客模式降級
            </p>
          </div>
          
          <AuthenticationDemo />
          
          <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4 text-gray-800">測試說明</h2>
            <div className="space-y-4 text-gray-700">
              <div>
                <h3 className="font-semibold text-gray-800">功能測試:</h3>
                <ul className="list-disc list-inside space-y-1 mt-2">
                  <li>點擊「登錄」按鈕測試登錄功能</li>
                  <li>點擊「測試錯誤」按鈕測試錯誤處理機制</li>
                  <li>點擊「測試權限」按鈕測試功能權限檢查</li>
                  <li>點擊「刷新狀態」按鈕測試狀態刷新</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-800">錯誤處理測試:</h3>
                <ul className="list-disc list-inside space-y-1 mt-2">
                  <li>使用 error@test.com 作為信箱測試錯誤處理</li>
                  <li>觀察系統如何分類和處理不同類型的錯誤</li>
                  <li>測試錯誤恢復和重試機制</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-800">訪客模式測試:</h3>
                <ul className="list-disc list-inside space-y-1 mt-2">
                  <li>觀察未登錄狀態下的功能限制</li>
                  <li>測試訪客模式下的可用功能</li>
                  <li>測試從錯誤狀態降級到訪客模式</li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-800">狀態監控:</h3>
                <ul className="list-disc list-inside space-y-1 mt-2">
                  <li>觀察系統狀態區域的實時更新</li>
                  <li>查看測試結果區域的錯誤記錄</li>
                  <li>監控認證狀態的變化過程</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthTestPage;