import { mapBackendUserToFrontend, mapFrontendUserToBackend } from '../userDataMapper';
import { UserRole } from '../../types/AdminTypes';

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
  });

  describe('mapFrontendUserToBackend', () => {
    it('應該正確映射前端 User 到後端格式', () => {
      const frontendUser = {
        email: 'test@example.com',
        username: 'testuser',
        firstName: '測試',
        lastName: '用戶',
        displayName: '測試 用戶',
        membershipTier: 'gold' as any,
        authProvider: 'email' as any,
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
      expect(result.membership_tier).toBe('gold');
      expect(result.auth_provider).toBe('email');
      expect(result.phone).toBe('+886912345678');
    });

    it('應該使用預設值', () => {
      const minimalUser = {
        email: 'minimal@example.com'
      };

      const result = mapFrontendUserToBackend(minimalUser);

      expect(result.membership_tier).toBe('free');
      expect(result.status).toBe('active');
      expect(result.auth_provider).toBe('email');
      expect(result.email_verified).toBe(false);
      expect(result.timezone).toBe('Asia/Taipei');
      expect(result.language).toBe('zh-TW');
    });
  });
});
