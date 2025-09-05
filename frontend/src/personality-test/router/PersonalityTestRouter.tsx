import React from 'react';
import { Routes, Route } from 'react-router-dom';
import PersonalityTestApp from '../PersonalityTestApp';

/**
 * 投資人格測試路由器
 * 處理 /personality-test/* 路徑的路由
 */
const PersonalityTestRouter: React.FC = () => {
  return (
    <Routes>
      {/* 所有 /personality-test/* 路徑都由 PersonalityTestApp 處理 */}
      <Route path="/*" element={<PersonalityTestApp mode="standalone" />} />
    </Routes>
  );
};

export default PersonalityTestRouter;