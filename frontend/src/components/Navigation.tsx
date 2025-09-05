import React from 'react';
import BrandConfigManager from '../utils/BrandConfig';

const Navigation: React.FC = () => {
  return (
    <nav className="navbar">
      <div className="navbar-brand">{BrandConfigManager.getBrandName()}</div>
      <div className="navbar-nav">
        <a href="/" className="nav-link">首頁</a>
        <a href="/dashboard" className="nav-link">儀表板</a>
        <a href="/analysts" className="nav-link">分析師</a>
      </div>
    </nav>
  );
};

export default Navigation;