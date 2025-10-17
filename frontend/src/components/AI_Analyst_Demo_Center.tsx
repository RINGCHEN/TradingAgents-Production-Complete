import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { TrendingUp, Brain, Target, AlertTriangle, MessageCircle, Shield } from 'lucide-react';

interface AnalystInsight {
  analyst_name: string;
  analyst_type: string;
  analysis: string;
  confidence: number;
  timestamp: string;
}

interface ComprehensiveAnalysis {
  stock_symbol: string;
  analysis_id: string;
  insights: AnalystInsight[];
  final_recommendation: string;
  confidence_score: string;
  upgrade_message?: string;
}

interface PopularStock {
  symbol: string;
  name: string;
  sector: string;
  market_cap: string;
}

const AI_ANALYST_ICONS: { [key: string]: React.ComponentType<{ className?: string }> } = {
  'technical_analyst': TrendingUp,
  'fundamentals_analyst': Target,
  'news_analyst': MessageCircle,
  'risk_analyst': AlertTriangle,
  'social_media_analyst': MessageCircle,
  'investment_planner': Brain
};

export const AIAnalystDemoCenter: React.FC = () => {
  const [popularStocks, setPopularStocks] = useState<PopularStock[]>([]);
  const [selectedStock, setSelectedStock] = useState<string>('2330.TW');
  const [analysis, setAnalysis] = useState<ComprehensiveAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [userTier, setUserTier] = useState<'free' | 'gold' | 'diamond'>('free');
  const [quickDemo, setQuickDemo] = useState<any>(null);

  const apiBase = process.env.REACT_APP_API_URL || 'https://twshocks-app-79rsx.ondigitalocean.app';

  useEffect(() => {
    fetchPopularStocks();
    runQuickDemo();
  }, []);

  const fetchPopularStocks = async () => {
    try {
      const response = await axios.get(`${apiBase}/api/v1/ai-demo/popular-stocks`);
      setPopularStocks(response.data.popular_stocks);
    } catch (error) {
      console.error('Error fetching popular stocks:', error);
    }
  };

  const runQuickDemo = async () => {
    try {
      const response = await axios.post(`${apiBase}/api/v1/ai-demo/quick-demo`);
      setQuickDemo(response.data);
    } catch (error) {
      console.error('Error running quick demo:', error);
    }
  };

  const runAnalysis = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${apiBase}/api/v1/ai-demo/analyze`, {
        stock_symbol: selectedStock,
        analysis_level: 'premium',
        user_tier: userTier
      });
      setAnalysis(response.data);
    } catch (error) {
      console.error('Error running analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white p-6">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-4">
            🚀 <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              TradingAgents AI 投資分析師
            </span>
          </h1>
          <p className="text-xl text-gray-600 mb-6">
            台灣首個 100% 系統驗證完成的企業級 AI 投資分析平台
          </p>
          <div className="flex justify-center space-x-4 mb-8">
            <Badge className="px-4 py-2 bg-green-100 text-green-800">17/17 系統驗證完成</Badge>
            <Badge className="px-4 py-2 bg-blue-100 text-blue-800">6位專業 AI 分析師</Badge>
            <Badge className="px-4 py-2 bg-purple-100 text-purple-800">即時台股數據</Badge>
          </div>
        </div>

        {/* Quick Demo Display */}
        {quickDemo && (
          <Card className="mb-8 border-2 border-blue-200 shadow-xl">
            <CardHeader>
              <CardTitle className="text-2xl text-center text-blue-700">
                🎯 AI 分析師即時展示 - {quickDemo.stock_symbol}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                {Object.entries(quickDemo.insights || {}).map(([analystType, insight]: [string, any]) => {
                  const IconComponent = AI_ANALYST_ICONS[analystType] || Brain;
                  return (
                    <Card key={analystType} className="hover:shadow-lg transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-center mb-2">
                          <IconComponent className="w-5 h-5 mr-2 text-blue-600" />
                          <h3 className="font-semibold text-sm">{insight.analyst}</h3>
                        </div>
                        <p className="text-sm text-gray-700">{insight.analysis}</p>
                        <small className="text-xs text-gray-500">{insight.timestamp}</small>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
              <div className="text-center p-6 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg">
                <h3 className="text-xl font-bold text-green-700 mb-2">{quickDemo.summary}</h3>
                <p className="text-blue-700 font-medium">{quickDemo.call_to_action}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Interactive Analysis Section */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Panel: Controls */}
          <div className="lg:col-span-1">
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>🎯 選擇分析標的</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">熱門台股</label>
                    <select 
                      value={selectedStock} 
                      onChange={(e) => setSelectedStock(e.target.value)}
                      className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      {popularStocks.map((stock) => (
                        <option key={stock.symbol} value={stock.symbol}>
                          {stock.name} ({stock.symbol})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">會員等級體驗</label>
                    <div className="space-y-2">
                      {[
                        { value: 'free', label: 'FREE - 1位分析師', color: 'bg-gray-100' },
                        { value: 'gold', label: 'GOLD - 4位分析師', color: 'bg-yellow-100' },
                        { value: 'diamond', label: 'DIAMOND - 6位分析師', color: 'bg-purple-100' }
                      ].map((tier) => (
                        <button
                          key={tier.value}
                          onClick={() => setUserTier(tier.value as any)}
                          className={`w-full p-3 rounded-lg text-left transition-colors ${
                            userTier === tier.value 
                              ? 'ring-2 ring-blue-500 ' + tier.color 
                              : 'border ' + tier.color + ' hover:ring-1 hover:ring-blue-300'
                          }`}
                        >
                          {tier.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <Button 
                    onClick={runAnalysis} 
                    disabled={loading}
                    className="w-full py-3 text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                  >
                    {loading ? '🔄 AI分析師協同分析中...' : '🚀 開始 AI 投資分析'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Member Benefits */}
            <Card>
              <CardHeader>
                <CardTitle>💎 會員權益對比</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 bg-gray-50 rounded">
                  <div className="font-medium">🆓 FREE</div>
                  <div className="text-sm text-gray-600">1位分析師 • 預覽功能</div>
                </div>
                <div className="p-3 bg-yellow-50 rounded">
                  <div className="font-medium">🥇 GOLD - NT$ 1,999/月</div>
                  <div className="text-sm text-gray-600">4位分析師 • 完整報告</div>
                </div>
                <div className="p-3 bg-purple-50 rounded">
                  <div className="font-medium">💎 DIAMOND - NT$ 4,999/月</div>
                  <div className="text-sm text-gray-600">6位分析師 • VIP服務</div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Panel: Analysis Results */}
          <div className="lg:col-span-2">
            {analysis && (
              <div className="space-y-6">
                {/* Upgrade Message */}
                {analysis.upgrade_message && (
                  <Alert className="border-yellow-200 bg-yellow-50">
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    <AlertDescription className="text-yellow-800 font-medium">
                      {analysis.upgrade_message}
                    </AlertDescription>
                  </Alert>
                )}

                {/* Analysis Insights */}
                <div className="grid gap-4">
                  {analysis.insights.map((insight, index) => {
                    const IconComponent = AI_ANALYST_ICONS[insight.analyst_type] || Brain;
                    return (
                      <Card key={index} className="hover:shadow-lg transition-shadow">
                        <CardContent className="p-6">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center">
                              <IconComponent className="w-6 h-6 mr-3 text-blue-600" />
                              <h3 className="text-lg font-semibold">{insight.analyst_name}</h3>
                            </div>
                            <Badge className="bg-blue-100 text-blue-800">
                              信心度: {(insight.confidence * 100).toFixed(0)}%
                            </Badge>
                          </div>
                          <p className="text-gray-700 leading-relaxed">{insight.analysis}</p>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>

                {/* Final Recommendation */}
                <Card className="border-2 border-green-200 bg-green-50">
                  <CardHeader>
                    <CardTitle className="text-green-700 flex items-center">
                      <Target className="w-6 h-6 mr-2" />
                      🏆 最終投資建議
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-lg text-green-800 mb-2">{analysis.final_recommendation}</p>
                    <div className="flex justify-between items-center">
                      <Badge className="bg-green-200 text-green-800">
                        整體信心度: {analysis.confidence_score}
                      </Badge>
                      <span className="text-sm text-green-600">
                        分析ID: {analysis.analysis_id}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                {/* Call to Action */}
                <div className="text-center p-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg text-white">
                  <h3 className="text-2xl font-bold mb-4">🚀 升級會員，解鎖完整AI投資分析能力！</h3>
                  <div className="flex justify-center space-x-4">
                    <Button 
                      onClick={() => window.location.href = '/pricing'}
                      className="bg-white text-blue-600 hover:bg-gray-100 font-semibold px-8 py-3"
                    >
                      💎 立即升級會員
                    </Button>
                    <Button 
                      onClick={() => window.location.href = '/pricing?plan=gold'}
                      className="bg-transparent border-2 border-white text-white hover:bg-white hover:text-purple-600 font-semibold px-8 py-3"
                    >
                      🥇 選擇GOLD方案
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {!analysis && !loading && (
              <div className="text-center py-20">
                <Brain className="w-20 h-20 mx-auto text-gray-300 mb-6" />
                <h3 className="text-2xl font-semibold text-gray-600 mb-4">
                  準備體驗AI投資分析的震撼力量
                </h3>
                <p className="text-gray-500">
                  選擇股票和會員等級，開始您的專業投資分析之旅
                </p>
              </div>
            )}

            {loading && (
              <div className="text-center py-20">
                <div className="animate-spin rounded-full h-20 w-20 border-b-2 border-blue-600 mx-auto mb-6"></div>
                <h3 className="text-2xl font-semibold text-blue-600 mb-4">
                  🤖 AI分析師團隊協同分析中...
                </h3>
                <p className="text-gray-500">
                  {userTier === 'free' ? '1位' : userTier === 'gold' ? '4位' : '6位'} 
                  專業分析師正在為您分析 {selectedStock}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};