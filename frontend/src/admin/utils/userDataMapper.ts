import { User, UserRole, UserStatus, MembershipTier, AuthProvider } from '../types/AdminTypes';

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

    // 會員與認證
    membershipTier: backendUser.membership_tier as MembershipTier,
    authProvider: backendUser.auth_provider as AuthProvider,

    // 狀態
    status: backendUser.status as UserStatus,
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

    // 時間戳
    createdAt: new Date(backendUser.created_at).toISOString(),
    updatedAt: new Date(backendUser.updated_at).toISOString(),
    lastLoginAt: backendUser.last_login ? new Date(backendUser.last_login).toISOString() : undefined,

    // 個人資料
    phone: backendUser.phone,
    country: backendUser.country,
    timezone: backendUser.timezone,
    language: backendUser.language
  };
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
    membership_tier: frontendUser.membershipTier || 'free',
    status: frontendUser.status || 'active',
    auth_provider: frontendUser.authProvider || 'email',
    email_verified: frontendUser.emailVerified || false,
    daily_api_quota: frontendUser.dailyApiQuota,
    monthly_api_quota: frontendUser.monthlyApiQuota,
    phone: frontendUser.phone,
    country: frontendUser.country,
    timezone: frontendUser.timezone || 'Asia/Taipei',
    language: frontendUser.language || 'zh-TW'
  };
}
