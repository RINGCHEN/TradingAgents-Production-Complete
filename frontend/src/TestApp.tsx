import React from 'react';
import TestPricingApp from './TestPricingApp';

/**
 * 簡化的測試應用 - 專門用於測試PayUni功能
 */
const TestApp: React.FC = () => {
  React.useEffect(() => {
    console.log('🚀 TestApp已載入 - PayUni測試環境');
  }, []);

  return (
    <div>
      <TestPricingApp />
    </div>
  );
};

export default TestApp;