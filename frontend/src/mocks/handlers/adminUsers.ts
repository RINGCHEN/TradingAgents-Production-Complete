/**
 * MSW Handlers for Admin User Management APIs
 *
 * IMPORTANT: These handlers return raw backend format (snake_case)
 * RealAdminApiService handles the mapping to frontend format
 * DO NOT call mapBackendUserToFrontend in handlers or data gets mapped twice!
 */

import { rest } from 'msw';
import { mapFrontendUserToBackend } from '../../admin/utils/userDataMapper';
import { User } from '../../admin/types/AdminTypes';

// Mock backend user data (snake_case format from API)
const mockBackendUsers = [
  {
    id: 1,
    uuid: 'user-001-uuid',
    email: 'admin@example.com',
    username: 'admin',
    display_name: 'Admin User',
    membership_tier: 'diamond',
    auth_provider: 'email',
    status: 'active',
    email_verified: true,
    avatar_url: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-15T00:00:00Z',
    last_login: '2025-01-20T10:30:00Z',
    daily_api_quota: 1000,
    api_calls_today: 150,
    total_analyses: 50,
    is_premium: true,
    login_count: 120
  },
  {
    id: 2,
    uuid: 'user-002-uuid',
    email: 'gold@example.com',
    username: 'golduser',
    display_name: 'Gold Member',
    membership_tier: 'gold',
    auth_provider: 'google',
    status: 'active',
    email_verified: true,
    avatar_url: 'https://example.com/avatar2.jpg',
    created_at: '2025-01-05T00:00:00Z',
    updated_at: '2025-01-18T00:00:00Z',
    last_login: '2025-01-19T15:45:00Z',
    daily_api_quota: 500,
    api_calls_today: 80,
    total_analyses: 25,
    is_premium: true,
    login_count: 45
  },
  {
    id: 3,
    uuid: 'user-003-uuid',
    email: 'free@example.com',
    username: 'freeuser',
    display_name: 'Free User',
    membership_tier: 'free',
    auth_provider: 'email',
    status: 'active',
    email_verified: false,
    avatar_url: null,
    created_at: '2025-01-10T00:00:00Z',
    updated_at: '2025-01-10T00:00:00Z',
    last_login: null,
    daily_api_quota: 10,
    api_calls_today: 5,
    total_analyses: 2,
    is_premium: false,
    login_count: 3
  },
  {
    id: 4,
    uuid: 'user-004-uuid',
    email: 'suspended@example.com',
    username: 'suspendeduser',
    display_name: 'Suspended User',
    membership_tier: 'free',
    auth_provider: 'email',
    status: 'suspended',
    email_verified: true,
    avatar_url: null,
    created_at: '2024-12-01T00:00:00Z',
    updated_at: '2025-01-12T00:00:00Z',
    last_login: '2025-01-10T08:20:00Z',
    daily_api_quota: 10,
    api_calls_today: 0,
    total_analyses: 15,
    is_premium: false,
    login_count: 89
  }
];

// In-memory storage for tests (will reset between tests)
let users = [...mockBackendUsers];
let nextId = 5;

export const adminUsersHandlers = [
  // GET /admin/users - List users with pagination and filters
  // Returns backend format: { items, total, page, page_size } with snake_case records
  rest.get('/admin/users', (req, res, ctx) => {
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const limit = parseInt(req.url.searchParams.get('limit') || '25');
    const keyword = req.url.searchParams.get('keyword'); // ⚠️ Backend uses 'keyword' not 'search'
    const role = req.url.searchParams.get('role');
    const status = req.url.searchParams.get('status');

    // Filter users
    let filtered = [...users];

    if (keyword) {
      const keywordLower = keyword.toLowerCase();
      filtered = filtered.filter(u =>
        u.email.toLowerCase().includes(keywordLower) ||
        u.username.toLowerCase().includes(keywordLower) ||
        u.display_name?.toLowerCase().includes(keywordLower)
      );
    }

    if (status) {
      filtered = filtered.filter(u => u.status === status);
    }

    // Calculate pagination
    const total = filtered.length;
    const start = (page - 1) * limit;
    const end = start + limit;
    const paginatedUsers = filtered.slice(start, end);

    // ⚠️ Return raw backend objects (snake_case) - RealAdminApiService will map them
    // DO NOT call mapBackendUserToFrontend here, or users get mapped twice!
    return res(
      ctx.status(200),
      ctx.json({
        items: paginatedUsers,  // Backend uses 'items' not 'users'
        total,
        page,
        page_size: limit  // Backend uses 'page_size' not 'limit'
      })
    );
  }),

  // GET /admin/users/:id - Get single user
  // Returns backend format with snake_case - RealAdminApiService will map it
  rest.get('/admin/users/:id', (req, res, ctx) => {
    const { id } = req.params;
    const user = users.find(u => u.id === parseInt(id as string));

    if (!user) {
      return res(
        ctx.status(404),
        ctx.json({ success: false, message: '用戶不存在' })
      );
    }

    // ⚠️ Return raw backend object (snake_case) - DO NOT map here
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: user,  // Raw backend format
        message: '獲取用戶成功'
      })
    );
  }),

  // POST /admin/users - Create user
  // Receives frontend format, stores backend format, returns backend format
  rest.post('/admin/users/', async (req, res, ctx) => {
    const frontendUserData = await req.json() as Partial<User>;

    // Transform to backend format using mapper (for storage)
    const backendUserData = mapFrontendUserToBackend(frontendUserData);

    // Create new user with backend format
    const newBackendUser = {
      id: nextId++,
      uuid: `user-${String(nextId).padStart(3, '0')}-uuid`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_login: null,
      api_calls_today: 0,
      total_analyses: 0,
      login_count: 0,
      ...backendUserData
    };

    users.push(newBackendUser);

    // ⚠️ Return raw backend object (snake_case) - RealAdminApiService will map it
    return res(
      ctx.status(201),
      ctx.json({
        success: true,
        data: newBackendUser,  // Raw backend format
        message: '用戶創建成功'
      })
    );
  }),

  // PUT /admin/users/:id - Update user
  // Receives frontend format, stores backend format, returns backend format
  rest.put('/admin/users/:id', async (req, res, ctx) => {
    const { id } = req.params;
    const frontendUserData = await req.json() as Partial<User>;

    const userIndex = users.findIndex(u => u.id === parseInt(id as string));

    if (userIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ success: false, message: '用戶不存在' })
      );
    }

    // Transform to backend format (for storage)
    const backendUpdateData = mapFrontendUserToBackend(frontendUserData);

    // Update user
    users[userIndex] = {
      ...users[userIndex],
      ...backendUpdateData,
      updated_at: new Date().toISOString()
    };

    // ⚠️ Return raw backend object (snake_case) - RealAdminApiService will map it
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        data: users[userIndex],  // Raw backend format
        message: '用戶更新成功'
      })
    );
  }),

  // DELETE /admin/users/:id - Delete user
  rest.delete('/admin/users/:id', (req, res, ctx) => {
    const { id } = req.params;
    const userIndex = users.findIndex(u => u.id === parseInt(id as string));

    if (userIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ success: false, message: '用戶不存在' })
      );
    }

    users.splice(userIndex, 1);

    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        message: '用戶刪除成功',
        data: {
          deleted_user_id: id,
          deleted_at: new Date().toISOString()
        }
      })
    );
  })
];

// Reset function for tests
export function resetMockUsers() {
  users = [...mockBackendUsers];
  nextId = 5;
}
