import React from 'react';
import BrandConfigManager from '../utils/BrandConfig';

interface NavigationProps {
  user: {
    id: string;
    name: string;
    email: string;
    tier: 'free' | 'gold' | 'diamond';
  } | null;
  onLogout: () => void;
}

const Navigation: React.FC<NavigationProps> = ({ user, onLogout }) => {
  return (
    <nav className="navbar">
      <div className="navbar-brand">{BrandConfigManager.getBrandName()}</div>
      <div className="navbar-nav">
        <a href="/" className="nav-link">首頁</a>
        <a href="/dashboard" className="nav-link">儀表板</a>
        <a href="/analysts" className="nav-link">分析師</a>
        {user && (
          <>
            <span className="nav-link user-info">
              {user.name} ({user.tier.toUpperCase()})
            </span>
            <button onClick={onLogout} className="nav-link logout-btn">
              登出
            </button>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navigation;