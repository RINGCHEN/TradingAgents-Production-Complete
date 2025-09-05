import React, { useState, useEffect } from 'react';
import './AboutPage.css';

interface TeamMember {
  id: string;
  name: string;
  role: string;
  bio: string;
  avatar: string;
  linkedin?: string;
  twitter?: string;
}

interface Milestone {
  year: string;
  title: string;
  description: string;
  icon: string;
}

const AboutPage: React.FC = () => {
  const [activeSection, setActiveSection] = useState('story');
  const [isLoading, setIsLoading] = useState(true);

  // 團隊成員數據
  const teamMembers: TeamMember[] = [
    {
      id: '1',
      name: '張志明',
      role: '創始人 & CEO',
      bio: '前華爾街量化分析師，擁有15年金融科技經驗。致力於將AI技術應用於投資分析領域。',
      avatar: '/avatars/ceo.jpg',
      linkedin: 'https://linkedin.com/in/zhiming-zhang',
      twitter: 'https://twitter.com/zhiming_zhang'
    },
    {
      id: '2',
      name: '李美華',
      role: 'CTO & 技術總監',
      bio: '前Google機器學習工程師，專精於大數據分析和AI算法開發。MIT計算機科學博士。',
      avatar: '/avatars/cto.jpg',
      linkedin: 'https://linkedin.com/in/meihua-li'
    },
    {
      id: '3',
      name: '王建國',
      role: '首席數據科學家',
      bio: '金融數據分析專家，曾在摩根士丹利擔任量化研究主管。史丹佛大學統計學博士。',
      avatar: '/avatars/data-scientist.jpg',
      linkedin: 'https://linkedin.com/in/jianguo-wang'
    },
    {
      id: '4',
      name: '陳雅婷',
      role: '產品總監',
      bio: '用戶體驗設計專家，曾在蘋果公司負責金融產品設計。專注於創造直觀易用的投資工具。',
      avatar: '/avatars/product-director.jpg',
      linkedin: 'https://linkedin.com/in/yating-chen'
    }
  ];

  // 發展里程碑
  const milestones: Milestone[] = [
    {
      year: '2020',
      title: '公司成立',
      description: 'TradingAgents 在台北成立，開始研發AI投資分析技術',
      icon: '🚀'
    },
    {
      year: '2021',
      title: '技術突破',
      description: '成功開發第一代AI分析師，準確率達到75%',
      icon: '🧠'
    },
    {
      year: '2022',
      title: '產品上線',
      description: 'Beta版本發布，獲得1000+早期用戶積極反饋',
      icon: '📱'
    },
    {
      year: '2023',
      title: '快速成長',
      description: '用戶突破10萬，完成A輪融資，團隊擴展至50人',
      icon: '📈'
    },
    {
      year: '2024',
      title: '國際擴展',
      description: '進軍東南亞市場，支援多國股市分析',
      icon: '🌏'
    },
    {
      year: '2025',
      title: '持續創新',
      description: '推出社群功能和個性化推薦，邁向智能投資生態系統',
      icon: '✨'
    }
  ];

  useEffect(() => {
    // 模擬載入
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 800);

    return () => clearTimeout(timer);
  }, []);

  const handleSectionChange = (section: string) => {
    setActiveSection(section);
  };

  if (isLoading) {
    return (
      <div className="about-page">
        <div className="about-loading">
          <div className="loading-spinner"></div>
          <p>載入中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="about-page">
      {/* 頁面標題 */}
      <div className="about-header">
        <div className="header-content">
          <h1 className="about-title">
            <span className="about-icon">🏢</span>
            關於我們
          </h1>
          <p className="about-subtitle">
            用AI重新定義投資分析，讓每個人都能做出更明智的投資決策
          </p>
        </div>
      </div>

      <div className="about-container">
        {/* 導航標籤 */}
        <div className="about-nav">
          <div className="nav-container">
            <button
              className={`nav-tab ${activeSection === 'story' ? 'active' : ''}`}
              onClick={() => handleSectionChange('story')}
            >
              <span className="tab-icon">📖</span>
              我們的故事
            </button>
            <button
              className={`nav-tab ${activeSection === 'mission' ? 'active' : ''}`}
              onClick={() => handleSectionChange('mission')}
            >
              <span className="tab-icon">🎯</span>
              使命願景
            </button>
            <button
              className={`nav-tab ${activeSection === 'team' ? 'active' : ''}`}
              onClick={() => handleSectionChange('team')}
            >
              <span className="tab-icon">👥</span>
              團隊介紹
            </button>
            <button
              className={`nav-tab ${activeSection === 'timeline' ? 'active' : ''}`}
              onClick={() => handleSectionChange('timeline')}
            >
              <span className="tab-icon">⏰</span>
              發展歷程
            </button>
          </div>
        </div>

        {/* 內容區域 */}
        <div className="about-content">
          {/* 我們的故事 */}
          {activeSection === 'story' && (
            <div className="content-section story-section">
              <div className="section-header">
                <h2 className="section-title">我們的故事</h2>
                <p className="section-subtitle">從一個想法到改變投資世界的平台</p>
              </div>

              <div className="story-content">
                <div className="story-text">
                  <div className="story-paragraph">
                    <h3>起源</h3>
                    <p>
                      TradingAgents 的故事始於2020年，當時我們的創始人張志明在華爾街工作時發現，
                      儘管有豐富的金融數據和先進的分析工具，但大多數個人投資者仍然難以做出明智的投資決策。
                      傳統的投資分析需要大量的專業知識和時間，這讓普通投資者處於劣勢。
                    </p>
                  </div>

                  <div className="story-paragraph">
                    <h3>願景</h3>
                    <p>
                      我們相信，每個人都應該有機會獲得專業級的投資分析。通過人工智能技術，
                      我們可以將複雜的金融分析簡化為易於理解的洞察，讓投資決策變得更加民主化。
                      這就是 TradingAgents 誕生的初衷。
                    </p>
                  </div>

                  <div className="story-paragraph">
                    <h3>創新</h3>
                    <p>
                      我們開發了獨特的AI分析師系統，結合機器學習、自然語言處理和大數據分析技術，
                      能夠實時分析市場動態、公司財報、新聞情緒等多維度信息，為用戶提供個性化的投資建議。
                      我們的目標不是取代人類的判斷，而是增強每個人的投資能力。
                    </p>
                  </div>
                </div>

                <div className="story-stats">
                  <div className="stat-item">
                    <div className="stat-number">100K+</div>
                    <div className="stat-label">活躍用戶</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number">1M+</div>
                    <div className="stat-label">分析報告</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number">85%</div>
                    <div className="stat-label">準確率</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number">24/7</div>
                    <div className="stat-label">服務時間</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 使命願景 */}
          {activeSection === 'mission' && (
            <div className="content-section mission-section">
              <div className="section-header">
                <h2 className="section-title">使命願景</h2>
                <p className="section-subtitle">我們的核心價值觀和長遠目標</p>
              </div>

              <div className="mission-content">
                <div className="mission-cards">
                  <div className="mission-card">
                    <div className="card-icon">🎯</div>
                    <h3 className="card-title">使命</h3>
                    <p className="card-description">
                      通過AI技術民主化投資分析，讓每個人都能獲得專業級的投資洞察，
                      做出更明智的財務決策，實現財富增長目標。
                    </p>
                  </div>

                  <div className="mission-card">
                    <div className="card-icon">🔮</div>
                    <h3 className="card-title">願景</h3>
                    <p className="card-description">
                      成為全球領先的AI投資分析平台，建立一個智能、透明、
                      包容的投資生態系統，讓投資變得簡單而有效。
                    </p>
                  </div>

                  <div className="mission-card">
                    <div className="card-icon">⚖️</div>
                    <h3 className="card-title">價值觀</h3>
                    <p className="card-description">
                      誠信透明、用戶至上、持續創新、數據驅動。
                      我們相信技術應該服務於人，讓投資更加公平和可及。
                    </p>
                  </div>
                </div>

                <div className="principles-section">
                  <h3 className="principles-title">我們的原則</h3>
                  <div className="principles-list">
                    <div className="principle-item">
                      <div className="principle-icon">🔒</div>
                      <div className="principle-content">
                        <h4>數據安全</h4>
                        <p>採用銀行級安全標準，保護用戶隱私和數據安全</p>
                      </div>
                    </div>
                    <div className="principle-item">
                      <div className="principle-icon">🎓</div>
                      <div className="principle-content">
                        <h4>教育優先</h4>
                        <p>不僅提供分析結果，更注重投資教育和知識傳播</p>
                      </div>
                    </div>
                    <div className="principle-item">
                      <div className="principle-icon">🌱</div>
                      <div className="principle-content">
                        <h4>可持續發展</h4>
                        <p>關注ESG投資，推動負責任的投資理念</p>
                      </div>
                    </div>
                    <div className="principle-item">
                      <div className="principle-icon">🤝</div>
                      <div className="principle-content">
                        <h4>社群共建</h4>
                        <p>建立開放的投資者社群，促進知識分享和交流</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 團隊介紹 */}
          {activeSection === 'team' && (
            <div className="content-section team-section">
              <div className="section-header">
                <h2 className="section-title">團隊介紹</h2>
                <p className="section-subtitle">來自世界頂尖機構的專業團隊</p>
              </div>

              <div className="team-content">
                <div className="team-grid">
                  {teamMembers.map(member => (
                    <div key={member.id} className="team-card">
                      <div className="member-avatar">
                        <img 
                          src={member.avatar} 
                          alt={member.name}
                          onError={(e: any) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            target.nextElementSibling!.classList.remove('hidden');
                          }}
                        />
                        <div className="avatar-placeholder hidden">
                          {member.name.charAt(0)}
                        </div>
                      </div>
                      <div className="member-info">
                        <h3 className="member-name">{member.name}</h3>
                        <p className="member-role">{member.role}</p>
                        <p className="member-bio">{member.bio}</p>
                        <div className="member-social">
                          {member.linkedin && (
                            <a 
                              href={member.linkedin} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="social-link"
                              aria-label={`${member.name} LinkedIn`}
                            >
                              💼
                            </a>
                          )}
                          {member.twitter && (
                            <a 
                              href={member.twitter} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="social-link"
                              aria-label={`${member.name} Twitter`}
                            >
                              🐦
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="team-culture">
                  <h3 className="culture-title">團隊文化</h3>
                  <div className="culture-items">
                    <div className="culture-item">
                      <span className="culture-icon">🚀</span>
                      <span className="culture-text">追求卓越，持續創新</span>
                    </div>
                    <div className="culture-item">
                      <span className="culture-icon">🤝</span>
                      <span className="culture-text">協作共贏，開放溝通</span>
                    </div>
                    <div className="culture-item">
                      <span className="culture-icon">📚</span>
                      <span className="culture-text">終身學習，知識分享</span>
                    </div>
                    <div className="culture-item">
                      <span className="culture-icon">⚡</span>
                      <span className="culture-text">敏捷高效，結果導向</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 發展歷程 */}
          {activeSection === 'timeline' && (
            <div className="content-section timeline-section">
              <div className="section-header">
                <h2 className="section-title">發展歷程</h2>
                <p className="section-subtitle">從創立到今天的重要里程碑</p>
              </div>

              <div className="timeline-content">
                <div className="timeline">
                  {milestones.map((milestone, index) => (
                    <div key={milestone.year} className="timeline-item">
                      <div className="timeline-marker">
                        <span className="marker-icon">{milestone.icon}</span>
                      </div>
                      <div className="timeline-content-item">
                        <div className="timeline-year">{milestone.year}</div>
                        <h3 className="timeline-title">{milestone.title}</h3>
                        <p className="timeline-description">{milestone.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 聯繫我們區域 */}
        <div className="contact-cta">
          <div className="cta-content">
            <h3>想了解更多？</h3>
            <p>歡迎聯繫我們，了解更多關於 TradingAgents 的信息</p>
            <div className="cta-buttons">
              <a href="/contact" className="cta-button primary">
                <span className="button-icon">📧</span>
                聯繫我們
              </a>
              <a href="/careers" className="cta-button secondary">
                <span className="button-icon">💼</span>
                加入我們
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;