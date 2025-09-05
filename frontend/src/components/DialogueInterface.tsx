import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  MessageCircle, 
  Send, 
  Bot, 
  User, 
  Activity, 
  TrendingUp,
  Loader2,
  Wifi,
  WifiOff
} from 'lucide-react';

// 類型定義
interface DialogueMessage {
  id: string;
  role: 'user' | 'analyst' | 'system' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: any;
  analysis_data?: any;
  art_data?: any;
}

interface DialogueSession {
  session_id: string;
  user_id: string;
  analyst_type: string;
  dialogue_type: string;
  interaction_mode: string;
  status: string;
  messages: DialogueMessage[];
  context: any;
  created_at: string;
  updated_at: string;
}

interface StreamingEvent {
  event: string;
  data: any;
  timestamp: string;
  session_id?: string;
}

interface AnalysisProgress {
  stage: string;
  message: string;
  progress: number;
  stock_id?: string;
}

// 主要組件
export const DialogueInterface: React.FC = () => {
  const [session, setSession] = useState<DialogueSession | null>(null);
  const [messages, setMessages] = useState<DialogueMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<AnalysisProgress | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  
  // 自動滾動到最新消息
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // 創建對話會話
  const createSession = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/dialogue/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test_token_123' // 測試用 token
        },
        body: JSON.stringify({
          message: '開始對話',
          dialogue_type: 'analysis',
          interaction_mode: 'conversational',
          context: {},
          preferences: {}
        })
      });
      
      if (response.ok) {
        const sessionData: DialogueSession = await response.json();
        setSession(sessionData);
        setMessages(sessionData.messages || []);
        
        // 建立 WebSocket 連接
        connectWebSocket(sessionData.session_id);
      } else {
        console.error('Failed to create session');
      }
    } catch (error) {
      console.error('Error creating session:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // WebSocket 連接
  const connectWebSocket = (sessionId: string) => {
    const wsUrl = `ws://localhost:8000/api/dialogue/ws/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setConnectionStatus('connected');
      setIsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'connected':
          console.log('Dialogue connected:', data.message);
          break;
          
        case 'response':
          const newMessage: DialogueMessage = data.data;
          setMessages(prev => [...prev, newMessage]);
          break;
          
        case 'processing':
          // 可以顯示處理中狀態
          break;
          
        case 'error':
          console.error('WebSocket error:', data.message);
          break;
          
        default:
          console.log('Unknown message type:', data);
      }
    };
    
    ws.onclose = () => {
      setConnectionStatus('disconnected');
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };
    
    ws.onerror = (error: any) => {
      setConnectionStatus('disconnected');
      console.error('WebSocket error:', error);
    };
    
    wsRef.current = ws;
  };
  
  // 發送消息
  const sendMessage = async () => {
    if (!inputMessage.trim() || !session) return;
    
    // 添加用戶消息到界面
    const userMessage: DialogueMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    // 通過 WebSocket 發送消息
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'message',
        content: inputMessage,
        context: {}
      }));
    }
    
    setInputMessage('');
  };
  
  // SSE 流式分析
  const startStreamingAnalysis = (stockId: string = '2330') => {
    if (!session) return;
    
    const eventSource = new EventSource(
      `/api/dialogue/sessions/${session.session_id}/stream?message=請分析${stockId}的投資前景&dialogue_type=analysis&interaction_mode=streaming`,
      {
        // headers: {
        //   'Authorization': 'Bearer test_token_123'
        // }
      }
    );
    
    eventSource.onopen = () => {
      setAnalysisProgress({ stage: 'connecting', message: '連接分析服務...', progress: 0 });
    };
    
    eventSource.addEventListener('analysis_start', (event) => {
      const data = JSON.parse(event.data);
      setAnalysisProgress({ stage: 'started', message: data.message, progress: 0 });
    });
    
    eventSource.addEventListener('analysis_progress', (event) => {
      const data = JSON.parse(event.data);
      setAnalysisProgress({
        stage: data.stage,
        message: data.message,
        progress: data.progress
      });
    });
    
    eventSource.addEventListener('analysis_complete', (event) => {
      const data = JSON.parse(event.data);
      const newMessage: DialogueMessage = data.response;
      setMessages(prev => [...prev, newMessage]);
      setAnalysisProgress(null);
      eventSource.close();
    });
    
    eventSource.onerror = () => {
      setAnalysisProgress(null);
      eventSource.close();
    };
    
    eventSourceRef.current = eventSource;
  };
  
  // 清理連接
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);
  
  // 渲染消息
  const renderMessage = (message: DialogueMessage) => {
    const isUser = message.role === 'user';
    
    return (
      <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start max-w-[70%]`}>
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-blue-500 ml-2' : 'bg-green-500 mr-2'
          }`}>
            {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
          </div>
          <div className={`rounded-lg px-3 py-2 ${
            isUser 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-900 border border-gray-200'
          }`}>
            <p className="text-sm">{message.content}</p>
            {message.analysis_data && (
              <div className="mt-2 p-2 bg-white/10 rounded text-xs">
                <pre>{JSON.stringify(message.analysis_data, null, 2)}</pre>
              </div>
            )}
            <p className="text-xs opacity-70 mt-1">
              {new Date(message.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className="max-w-4xl mx-auto p-4">
      <Card className="h-[600px] flex flex-col">
        <CardHeader className="flex-shrink-0">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MessageCircle size={24} />
              <span>AI投資分析師對話系統</span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={isConnected ? 'default' : 'secondary'}>
                {isConnected ? (
                  <>
                    <Wifi size={12} className="mr-1" />
                    已連接
                  </>
                ) : (
                  <>
                    <WifiOff size={12} className="mr-1" />
                    未連接
                  </>
                )}
              </Badge>
              {!session && (
                <Button onClick={createSession} disabled={isLoading} size="sm">
                  {isLoading ? <Loader2 size={16} className="animate-spin" /> : '開始對話'}
                </Button>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        
        <CardContent className="flex-1 flex flex-col overflow-hidden">
          {!session ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Bot size={48} className="mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600 mb-4">歡迎使用AI投資分析師對話系統</p>
                <Button onClick={createSession} disabled={isLoading}>
                  {isLoading ? <Loader2 size={16} className="animate-spin mr-2" /> : null}
                  開始對話
                </Button>
              </div>
            </div>
          ) : (
            <>
              {/* 分析進度顯示 */}
              {analysisProgress && (
                <Alert className="mb-4">
                  <Activity className="h-4 w-4" />
                  <AlertDescription>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span>{analysisProgress.message}</span>
                        <span className="text-sm text-gray-500">{analysisProgress.progress}%</span>
                      </div>
                      <Progress value={analysisProgress.progress} />
                    </div>
                  </AlertDescription>
                </Alert>
              )}
              
              {/* 消息列表 */}
              <ScrollArea className="flex-1 pr-4">
                <div className="space-y-2">
                  {messages.map(renderMessage)}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
              
              {/* 輸入區域 */}
              <div className="flex-shrink-0 mt-4 space-y-2">
                <div className="flex space-x-2">
                  <Button 
                    onClick={() => startStreamingAnalysis('2330')} 
                    variant="outline" 
                    size="sm"
                    disabled={!isConnected}
                  >
                    <TrendingUp size={16} className="mr-1" />
                    分析台積電
                  </Button>
                  <Button 
                    onClick={() => startStreamingAnalysis('2454')} 
                    variant="outline" 
                    size="sm"
                    disabled={!isConnected}
                  >
                    <TrendingUp size={16} className="mr-1" />
                    分析聯發科
                  </Button>
                </div>
                
                <div className="flex space-x-2">
                  <Input
                    value={inputMessage}
                    onChange={(e: any) => setInputMessage(e.target.value)}
                    placeholder="輸入您的問題..."
                    onKeyPress={(e: any) => e.key === 'Enter' && sendMessage()}
                    disabled={!isConnected}
                  />
                  <Button 
                    onClick={sendMessage} 
                    disabled={!inputMessage.trim() || !isConnected}
                  >
                    <Send size={16} />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DialogueInterface;