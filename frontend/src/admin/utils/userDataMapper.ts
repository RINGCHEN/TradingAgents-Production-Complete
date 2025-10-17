import { User, UserRole, UserStatus, MembershipTier, AuthProvider } from '../types/AdminTypes';

/**
 * 安全地轉換時間戳為 ISO 字符串
 * @param timestamp - 可能為 null/undefined 的時間戳
 * @param fieldName - 欄位名稱（用於日誌）
 * @param warnOnMissing - 是否在缺失時警告（對於必填欄位）
 * @returns ISO 字符串或 undefined
 */
function safeToISOString(
  timestamp: any,
  fieldName?: string,
  warnOnMissing: boolean = false
): string | undefined {
  if (!timestamp) {
    if (warnOnMissing && fieldName) {
      console.warn(`[userDataMapper] 缺少必填時間戳欄位: ${fieldName}，使用當前時間作為回退值`);
    }
    return undefined;
  }

  try {
    const date = new Date(timestamp);
    // 檢查是否為有效日期
    if (isNaN(date.getTime())) {
      if (fieldName) {
        console.warn(`[userDataMapper] 無效的時間戳格式 (${fieldName}): ${timestamp}`);
      }
      return undefined;
    }
    return date.toISOString();
  } catch (error) {
    if (fieldName) {
      console.warn(`[userDataMapper] 時間戳轉換失敗 (${fieldName}):`, error);
    }
    return undefined;
  }
}

/**
 * 將後端 UserResponse 映射為前端 User
 *
 * ⚠️ 重要：role 欄位處理說明
 * - 當前設定：固定為 UserRole.USER
 * - 原因：後端沒有提供真正的 role 欄位
 * - 不可用於：權限判斷、RBAC 控制
 * - 可用於：UI 標籤顯示（但需配合 membershipTier）
 * - TODO: Phase 2 等後端實現真正的 role 欄位後修正
 */
export function mapBackendUserToFrontend(backendUser: any): User {
  // 處理 display_name → firstName/lastName
  let firstName = '';
  let lastName = '';
  if (backendUser.display_name) {
    const parts = backendUser.display_name.trim().split(/\s+/);
    firstName = parts[0] || '';
    lastName = parts.slice(1).join(' ') || '';
  } else {
    firstName = backendUser.username || backendUser.email.split('@')[0];
  }

  return {
    // 基礎識別
    id: String(backendUser.id),
    uuid: backendUser.uuid,
    email: backendUser.email,
    username: backendUser.username || backendUser.email.split('@')[0],

    // 顯示名稱
    firstName,
    lastName,
    displayName: backendUser.display_name || `${firstName} ${lastName}`.trim(),

    // 頭像
    avatar: backendUser.avatar_url || '/default-avatar.png',

    // ⚠️ 角色：固定為 USER（Phase 1 臨時方案）
    role: UserRole.USER,

    // 會員與認證（使用枚舉或提供默認值）
    membershipTier: backendUser.membership_tier as MembershipTier || MembershipTier.FREE,
    authProvider: backendUser.auth_provider as AuthProvider || AuthProvider.EMAIL,

    // 狀態（使用枚舉或提供默認值）
    status: backendUser.status as UserStatus || UserStatus.ACTIVE,
    emailVerified: backendUser.email_verified,

    // 配額
    dailyApiQuota: backendUser.daily_api_quota,
    monthlyApiQuota: backendUser.monthly_api_quota,
    apiCallsToday: backendUser.api_calls_today,
    apiCallsMonth: backendUser.api_calls_month,

    // 統計
    totalAnalyses: backendUser.total_analyses,
    loginCount: backendUser.login_count,
    isPremium: backendUser.is_premium,

    // 時間戳（使用安全轉換，必填欄位缺失時警告並使用當前時間）
    createdAt: safeToISOString(backendUser.created_at, 'created_at', true) || new Date().toISOString(),
    updatedAt: safeToISOString(backendUser.updated_at, 'updated_at', true) || new Date().toISOString(),
    lastLoginAt: safeToISOString(backendUser.last_login, 'last_login', false),

    // 個人資料
    phone: backendUser.phone,
    country: backendUser.country,
    timezone: backendUser.timezone,
    language: backendUser.language
  } as User;
}

/**
 * 將前端 User 映射為後端請求格式
 */
export function mapFrontendUserToBackend(frontendUser: Partial<User>): any {
  const display_name = frontendUser.displayName
    || [frontendUser.firstName, frontendUser.lastName].filter(Boolean).join(' ')
    || frontendUser.username
    || '';

  return {
    email: frontendUser.email,
    username: frontendUser.username,
    display_name,
    avatar_url: frontendUser.avatar === '/default-avatar.png' ? null : frontendUser.avatar,
    membership_tier: frontendUser.membershipTier || MembershipTier.FREE,
    status: frontendUser.status || UserStatus.ACTIVE,
    auth_provider: frontendUser.authProvider || AuthProvider.EMAIL,
    email_verified: frontendUser.emailVerified || false,
    daily_api_quota: frontendUser.dailyApiQuota,
    monthly_api_quota: frontendUser.monthlyApiQuota,
    phone: frontendUser.phone,
    country: frontendUser.country,
    timezone: frontendUser.timezone || 'Asia/Taipei',
    language: frontendUser.language || 'zh-TW'
  };
}
