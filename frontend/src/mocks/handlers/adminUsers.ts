/**
 * MSW Handlers for Admin User Management APIs
 * Phase 1: Uses mapBackendUserToFrontend for proper data transformation
 */

import { http, HttpResponse } from 'msw';
import { mapBackendUserToFrontend, mapFrontendUserToBackend } from '../../admin/utils/userDataMapper';
import { User, UserRole, UserStatus, MembershipTier, AuthProvider } from '../../admin/types/AdminTypes';

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
  http.get('/admin/users', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '25');
    const search = url.searchParams.get('search');
    const role = url.searchParams.get('role');
    const status = url.searchParams.get('status');

    // Filter users
    let filtered = [...users];

    if (search) {
      const searchLower = search.toLowerCase();
      filtered = filtered.filter(u =>
        u.email.toLowerCase().includes(searchLower) ||
        u.username.toLowerCase().includes(searchLower) ||
        u.display_name?.toLowerCase().includes(searchLower)
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

    // Transform to frontend format using mapper
    const transformedUsers = paginatedUsers.map(mapBackendUserToFrontend);

    return HttpResponse.json({
      users: transformedUsers,
      total,
      page,
      limit
    });
  }),

  // GET /admin/users/:id - Get single user
  http.get('/admin/users/:id', ({ params }) => {
    const { id } = params;
    const user = users.find(u => u.id === parseInt(id as string));

    if (!user) {
      return HttpResponse.json(
        { success: false, message: '用戶不存在' },
        { status: 404 }
      );
    }

    const transformedUser = mapBackendUserToFrontend(user);

    return HttpResponse.json({
      success: true,
      data: transformedUser,
      message: '獲取用戶成功'
    });
  }),

  // POST /admin/users - Create user
  http.post('/admin/users/', async ({ request }) => {
    const frontendUserData = await request.json() as Partial<User>;

    // Transform to backend format using mapper
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

    // Transform back to frontend format
    const transformedUser = mapBackendUserToFrontend(newBackendUser);

    return HttpResponse.json({
      success: true,
      data: transformedUser,
      message: '用戶創建成功'
    }, { status: 201 });
  }),

  // PUT /admin/users/:id - Update user
  http.put('/admin/users/:id', async ({ params, request }) => {
    const { id } = params;
    const frontendUserData = await request.json() as Partial<User>;

    const userIndex = users.findIndex(u => u.id === parseInt(id as string));

    if (userIndex === -1) {
      return HttpResponse.json(
        { success: false, message: '用戶不存在' },
        { status: 404 }
      );
    }

    // Transform to backend format
    const backendUpdateData = mapFrontendUserToBackend(frontendUserData);

    // Update user
    users[userIndex] = {
      ...users[userIndex],
      ...backendUpdateData,
      updated_at: new Date().toISOString()
    };

    // Transform back to frontend format
    const transformedUser = mapBackendUserToFrontend(users[userIndex]);

    return HttpResponse.json({
      success: true,
      data: transformedUser,
      message: '用戶更新成功'
    });
  }),

  // DELETE /admin/users/:id - Delete user
  http.delete('/admin/users/:id', ({ params }) => {
    const { id } = params;
    const userIndex = users.findIndex(u => u.id === parseInt(id as string));

    if (userIndex === -1) {
      return HttpResponse.json(
        { success: false, message: '用戶不存在' },
        { status: 404 }
      );
    }

    users.splice(userIndex, 1);

    return HttpResponse.json({
      success: true,
      message: '用戶刪除成功',
      data: {
        deleted_user_id: id,
        deleted_at: new Date().toISOString()
      }
    });
  })
];

// Reset function for tests
export function resetMockUsers() {
  users = [...mockBackendUsers];
  nextId = 5;
}
