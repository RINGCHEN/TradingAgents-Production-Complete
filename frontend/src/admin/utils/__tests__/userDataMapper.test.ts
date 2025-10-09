import { mapBackendUserToFrontend, mapFrontendUserToBackend } from '../userDataMapper';
import { UserRole, MembershipTier, AuthProvider, UserStatus } from '../../types/AdminTypes';

describe('userDataMapper', () => {
  describe('mapBackendUserToFrontend', () => {
    it('應該正確映射所有欄位', () => {
      const backendUser = {
        id: 1,
        uuid: 'test-uuid',
        email: 'test@example.com',
        username: 'testuser',
        display_name: '測試 用戶',
        membership_tier: 'gold',
        auth_provider: 'email',
        status: 'active',
        email_verified: true,
        avatar_url: 'https://example.com/avatar.jpg',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-15T00:00:00Z',
        last_login: '2025-01-20T00:00:00Z',
        daily_api_quota: 100,
        api_calls_today: 50,
        total_analyses: 10,
        is_premium: true
      };

      const result = mapBackendUserToFrontend(backendUser);

      expect(result.id).toBe('1');
      expect(result.email).toBe('test@example.com');
      expect(result.firstName).toBe('測試');
      expect(result.lastName).toBe('用戶');
      expect(result.displayName).toBe('測試 用戶');
      expect(result.role).toBe(UserRole.USER);  // ⚠️ 固定值
      expect(result.membershipTier).toBe('gold');
      expect(result.authProvider).toBe('email');
      expect(result.isPremium).toBe(true);
    });

    it('role 欄位應該固定為 USER', () => {
      const diamondUser = {
        id: 1,
        email: 'diamond@example.com',
        membership_tier: 'diamond',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        status: 'active'
      };
      const result = mapBackendUserToFrontend(diamondUser);

      expect(result.role).toBe(UserRole.USER);  // 不是 ADMIN!
    });

    it('應該正確處理缺少 display_name 的情況', () => {
      const backendUser = {
        id: 2,
        email: 'noname@example.com',
        username: 'noname',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        status: 'active'
      };

      const result = mapBackendUserToFrontend(backendUser);

      expect(result.firstName).toBe('noname');
      expect(result.displayName).toBe('noname');
    });

    it('應該正確處理時間戳轉換', () => {
      const backendUser = {
        id: 3,
        email: 'test@example.com',
        created_at: '2025-01-01T10:30:00Z',
        updated_at: '2025-01-15T14:45:00Z',
        status: 'active'
      };

      const result = mapBackendUserToFrontend(backendUser);

      expect(result.createdAt).toBe('2025-01-01T10:30:00.000Z');
      expect(result.updatedAt).toBe('2025-01-15T14:45:00.000Z');
    });

    it('應該處理 null/undefined 時間戳', () => {
      const backendUser = {
        id: 4,
        email: 'nulltime@example.com',
        created_at: null,
        updated_at: undefined,
        last_login: null,
        status: 'active'
      };

      const result = mapBackendUserToFrontend(backendUser);

      // 應該提供默認值或當前時間
      expect(result.createdAt).toBeDefined();
      expect(result.updatedAt).toBeDefined();
      expect(result.lastLoginAt).toBeUndefined();
    });

    it('應該處理無效時間戳', () => {
      const backendUser = {
        id: 5,
        email: 'invalidtime@example.com',
        created_at: 'invalid-date',
        updated_at: 'not-a-timestamp',
        status: 'active'
      };

      const result = mapBackendUserToFrontend(backendUser);

      // 應該優雅地處理無效日期
      expect(result.createdAt).toBeDefined();
      expect(result.updatedAt).toBeDefined();
    });

    it('應該處理空的 tier 值並提供默認值', () => {
      const backendUser = {
        id: 6,
        email: 'notier@example.com',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        status: 'active'
        // membership_tier, auth_provider, status 都未提供
      };

      const result = mapBackendUserToFrontend(backendUser);

      // 應該提供默認值
      expect(result.membershipTier).toBe(MembershipTier.FREE);
      expect(result.authProvider).toBe(AuthProvider.EMAIL);
      expect(result.status).toBe(UserStatus.ACTIVE);
    });
  });

  describe('mapFrontendUserToBackend', () => {
    it('應該正確映射前端 User 到後端格式', () => {
      const frontendUser = {
        email: 'test@example.com',
        username: 'testuser',
        firstName: '測試',
        lastName: '用戶',
        displayName: '測試 用戶',
        membershipTier: MembershipTier.GOLD,
        authProvider: AuthProvider.EMAIL,
        status: UserStatus.ACTIVE,
        emailVerified: true,
        phone: '+886912345678',
        country: 'TW',
        timezone: 'Asia/Taipei',
        language: 'zh-TW'
      };

      const result = mapFrontendUserToBackend(frontendUser);

      expect(result.email).toBe('test@example.com');
      expect(result.username).toBe('testuser');
      expect(result.display_name).toBe('測試 用戶');
      expect(result.membership_tier).toBe(MembershipTier.GOLD);
      expect(result.auth_provider).toBe(AuthProvider.EMAIL);
      expect(result.status).toBe(UserStatus.ACTIVE);
      expect(result.phone).toBe('+886912345678');
    });

    it('應該使用預設枚舉值', () => {
      const minimalUser = {
        email: 'minimal@example.com'
      };

      const result = mapFrontendUserToBackend(minimalUser);

      expect(result.membership_tier).toBe(MembershipTier.FREE);
      expect(result.status).toBe(UserStatus.ACTIVE);
      expect(result.auth_provider).toBe(AuthProvider.EMAIL);
      expect(result.email_verified).toBe(false);
      expect(result.timezone).toBe('Asia/Taipei');
      expect(result.language).toBe('zh-TW');
    });
  });
});
