/**
 * 投資人格測試 API 整合服務
 * 負責與後端 API 的所有通信
 */

import { UTMParams } from '../PersonalityTestApp';

// API 響應類型定義
export interface PersonalityTestQuestion {
  id: string;
  scenario: string;
  question: string;
  options: Array<{
    text: string;
    index: number;
  }>;
}

export interface PersonalityType {
  type: string;
  title: string;
  display_name: string;
  description: string;
  celebrity_comparison: string;
  characteristics: string[];
  investment_style: string;
  icon: string;
}

export interface DimensionScores {
  risk_tolerance: number;
  emotional_control: number;
  analytical_thinking: number;
  market_sensitivity: number;
  long_term_vision: number;
}

export interface PersonalityTestResult {
  id: string;
  session_id: string;
  personality_type: PersonalityType;
  dimension_scores: DimensionScores;
  percentile: number;
  recommendations: string[];
  share_content: {
    title: string;
    share_text: string;
    celebrity_comparison: string;
    percentile: number;
  };
  completed_at: string;
  completion_time: number;
}

export interface TestStartResponse {
  session_id: string;
  question: PersonalityTestQuestion;
  total_questions: number;
  message: string;
}

export interface SubmitAnswerResponse {
  completed: boolean;
  question?: PersonalityTestQuestion;
  result?: PersonalityTestResult;
  current_question: number;
  progress: number;
  message: string;
}

export interface ShareImageResponse {
  image_url: string;
  share_text: string;
  share_url: string;
}

export interface UserRegistrationData {
  name: string;
  email: string;
  phone?: string;
  result_id: string;
  utm_params?: UTMParams;
  referrer?: string;
}

export interface UserRegistrationResponse {
  user_id: string;
  success: boolean;
  message: string;
  next_steps: string[];
}

// API 錯誤類型
export class PersonalityTestAPIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public errorCode?: string,
    public details?: any
  ) {
    super(message);
    this.name = 'PersonalityTestAPIError';
  }
}

// API 服務類
export class PersonalityTestAPI {
  private baseUrl: string;
  private defaultHeaders: HeadersInit;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || window.location.origin;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  /**
   * 處理 API 響應
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorCode = response.status.toString();
      let details = null;

      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
        errorCode = errorData.error_code || errorCode;
        details = errorData.details || null;
      } catch {
        // 如果無法解析錯誤響應，使用默認錯誤消息
      }

      throw new PersonalityTestAPIError(errorMessage, response.status, errorCode, details);
    }

    try {
      return await response.json();
    } catch (error) {
      throw new PersonalityTestAPIError('Invalid JSON response', 500, 'INVALID_JSON');
    }
  }

  /**
   * 開始測試
   */
  async startTest(userInfo: {
    user_id?: string;
    name?: string;
    utm_params?: UTMParams;
    referrer?: string;
  }): Promise<TestStartResponse> {
    const response = await fetch(`${this.baseUrl}/api/personality-test/start`, {
      method: 'POST',
      headers: this.defaultHeaders,
      body: JSON.stringify({
        user_info: {
          user_id: userInfo.user_id || `guest_${Date.now()}`,
          name: userInfo.name || 'Guest User',
          started_at: new Date().toISOString(),
          utm_params: userInfo.utm_params,
          referrer: userInfo.referrer
        }
      }),
    });

    return this.handleResponse<TestStartResponse>(response);
  }

  /**
   * 提交答案
   */
  async submitAnswer(
    sessionId: string,
    questionId: string,
    selectedOption: number
  ): Promise<SubmitAnswerResponse> {
    const response = await fetch(`${this.baseUrl}/api/personality-test/submit-answer`, {
      method: 'POST',
      headers: this.defaultHeaders,
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        selected_option: selectedOption,
      }),
    });

    return this.handleResponse<SubmitAnswerResponse>(response);
  }

  /**
   * 獲取測試結果
   */
  async getTestResult(sessionId: string): Promise<PersonalityTestResult> {
    const response = await fetch(`${this.baseUrl}/api/personality-test/result/${sessionId}`, {
      method: 'GET',
      headers: this.defaultHeaders,
    });

    return this.handleResponse<PersonalityTestResult>(response);
  }

  /**
   * 生成分享圖片
   */
  async generateShareImage(
    sessionId: string,
    template: string = 'personality_result'
  ): Promise<ShareImageResponse> {
    const response = await fetch(`${this.baseUrl}/api/share/generate-image`, {
      method: 'POST',
      headers: this.defaultHeaders,
      body: JSON.stringify({
        session_id: sessionId,
        template: template,
      }),
    });

    return this.handleResponse<ShareImageResponse>(response);
  }

  /**
   * 追蹤分享行為
   */
  async trackShare(shareData: {
    result_id: string;
    platform: string;
    share_text: string;
    share_url: string;
    user_agent?: string;
    referrer?: string;
  }): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/share/track`, {
      method: 'POST',
      headers: this.defaultHeaders,
      body: JSON.stringify({
        ...shareData,
        user_agent: shareData.user_agent || navigator.userAgent,
        referrer: shareData.referrer || document.referrer,
        created_at: new Date().toISOString(),
      }),
    });

    await this.handleResponse<void>(response);
  }

  /**
   * 用戶註冊轉換
   */
  async registerUser(registrationData: UserRegistrationData): Promise<UserRegistrationResponse> {
    const response = await fetch(`${this.baseUrl}/api/personality-test/register`, {
      method: 'POST',
      headers: this.defaultHeaders,
      body: JSON.stringify({
        ...registrationData,
        registered_at: new Date().toISOString(),
      }),
    });

    return this.handleResponse<UserRegistrationResponse>(response);
  }

  /**
   * 追蹤轉換步驟
   */
  async trackConversionStep(stepData: {
    session_id: string;
    step: string;
    action: string;
    data?: Record<string, any>;
  }): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/conversion/track-step`, {
      method: 'POST',
      headers: this.defaultHeaders,
      body: JSON.stringify({
        ...stepData,
        created_at: new Date().toISOString(),
      }),
    });

    await this.handleResponse<void>(response);
  }

  /**
   * 獲取分享結果頁面數據
   */
  async getSharePageData(resultId: string): Promise<{
    result: PersonalityTestResult;
    share_image_url?: string;
    meta_tags: {
      title: string;
      description: string;
      image: string;
      url: string;
    };
  }> {
    const response = await fetch(`${this.baseUrl}/api/personality-test/share/${resultId}`, {
      method: 'GET',
      headers: this.defaultHeaders,
    });

    return this.handleResponse(response);
  }

  /**
   * 健康檢查
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${this.baseUrl}/api/health`, {
      method: 'GET',
      headers: this.defaultHeaders,
    });

    return this.handleResponse(response);
  }

  /**
   * 設置認證令牌
   */
  setAuthToken(token: string): void {
    this.defaultHeaders = {
      ...this.defaultHeaders,
      'Authorization': `Bearer ${token}`,
    };
  }

  /**
   * 清除認證令牌
   */
  clearAuthToken(): void {
    const { Authorization, ...headers } = this.defaultHeaders as any;
    this.defaultHeaders = headers;
  }

  /**
   * 通用請求方法
   */
  async request<T = any>(
    endpoint: string, 
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    data?: any
  ): Promise<{ success: boolean; data: T; message?: string }> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    
    const requestInit: RequestInit = {
      method,
      headers: this.defaultHeaders,
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      requestInit.body = JSON.stringify(data);
    }

    const response = await fetch(url, requestInit);
    
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorCode = response.status.toString();
      let details = null;

      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
        errorCode = errorData.error_code || errorCode;
        details = errorData.details || null;
      } catch {
        // 如果無法解析錯誤響應，使用默認錯誤消息
      }

      throw new PersonalityTestAPIError(errorMessage, response.status, errorCode, details);
    }

    try {
      const responseData = await response.json();
      return {
        success: true,
        data: responseData,
        message: responseData.message || 'Success'
      };
    } catch (error) {
      throw new PersonalityTestAPIError('Invalid JSON response', 500, 'INVALID_JSON');
    }
  }
}

// 默認 API 實例
export const personalityTestAPI = new PersonalityTestAPI();

// 錯誤處理工具函數
export const handleAPIError = (error: unknown): string => {
  if (error instanceof PersonalityTestAPIError) {
    switch (error.statusCode) {
      case 400:
        return '請求參數錯誤，請檢查輸入內容';
      case 401:
        return '未授權訪問，請重新登入';
      case 403:
        return '權限不足，無法執行此操作';
      case 404:
        return '找不到請求的資源';
      case 429:
        return '請求過於頻繁，請稍後再試';
      case 500:
        return '服務器內部錯誤，請稍後再試';
      case 503:
        return '服務暫時不可用，請稍後再試';
      default:
        return error.message || '發生未知錯誤';
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return '發生未知錯誤，請稍後再試';
};