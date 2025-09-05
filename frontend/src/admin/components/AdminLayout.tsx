/**
 * 管理後台主佈局組件
 * 簡化版本，主要功能已整合到AdminApp中
 */

import React from 'react';

interface AdminLayoutProps {
  children: React.ReactNode;
}

export const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  return (
    <div className="admin-layout">
      {children}
    </div>
  );
};