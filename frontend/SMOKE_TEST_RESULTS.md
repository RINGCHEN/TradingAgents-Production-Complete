# Phase 2 Smoke Test Results

**Date Started**: 2025-10-10
**Tester**: _pending manual execution_
**Environment**: Development (MSW Mock API)
**Browser**: _TBD_
**Dev Server**: http://localhost:3003

> ⚠️ 這份紀錄由自動化準備，目前尚未實際執行瀏覽器冒煙測試。請在完成手動測試後更新各情境的結果與備註。

---

## Test Execution Summary

| Category | Total Scenarios | Passed | Failed | Blocked | Notes |
|----------|----------------|--------|--------|---------|-------|
| 1. List Load & Pagination | 5 | - | - | - | Pending manual run |
| 2. Search & Filtering | 7 | - | - | - | Pending manual run |
| 3. CRUD Happy Paths | 4 | - | - | - | Pending manual run |
| 4. CRUD Error Paths | 5 | - | - | - | Pending manual run |
| 5. Data Integrity Checks | 5 | - | - | - | Pending manual run |
| **TOTAL** | **26** | **0** | **0** | **0** | Pending manual run |

---

## Environment Verification

### Prerequisites Check

- [x] Phase 1 branch `feature/admin-baseline` checked out
- [ ] Dependencies installed (`npm install`)
- [x] Dev server starts successfully (port 3003)
- [ ] MSW console log appears: `[MSW] Browser worker started (dev mode)`
- [ ] Network tab shows MSW interception
- [ ] Initial mock data loads (4 users visible)

### Console Output

```
[Paste dev server startup output here]
```

### MSW Verification

**Browser Console Screenshot/Log**:
```
[Paste MSW startup message here]
```

**Network Tab Verification**:
- [ ] Requests to `/admin/users` intercepted by MSW
- [ ] No real backend calls made
- [ ] Response shows mock data structure

---

## 1. List Load & Pagination Tests

### 1.1.1 Initial Page Load (P0)

**Expected**: Display 25 users (default page size)

**Steps**:
1. Navigate to `/admin/users`
2. Observe initial user list

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Console Logs** (if any issues):
```
[Paste relevant console output]
```

**Screenshots**:
- [ ] Attached: `1.1.1-initial-load.png`

---

### 1.1.2 Navigate to Page 2 (P0)

**Expected**: Display next 25 users

**Steps**:
1. Click "Next" or "Page 2" button
2. Verify URL parameter: `?page=2`
3. Verify different users displayed

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Network Request**:
- Request URL: `[e.g., /admin/users?page=2&limit=25]`
- MSW Intercepted: [ ] Yes [ ] No
- Response Status: `[e.g., 200]`

---

### 1.1.3 Change Page Size to 50 (P1)

**Expected**: Display 50 users per page

**Steps**:
1. Find page size selector
2. Change to 50
3. Verify `?limit=50` in URL

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

### 1.1.4 Empty Result Set (P1)

**Expected**: Show "No users found" message

**Steps**:
1. (May require MSW handler override to return empty `items`)
2. Navigate to page beyond available data
3. Or apply filter that matches no users

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

### 1.1.5 Total Count Display (P0)

**Expected**: Show "Showing 1-25 of 100" or similar

**Steps**:
1. Check pagination metadata display
2. Verify total count matches mock data

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

## 2. Search & Filtering Tests

### 2.2.1 Search by Email (P0)

**Expected**: Filter users matching email keyword

**Steps**:
1. Type "admin" in search box
2. Verify network request: `?keyword=admin`
3. Verify results filtered to matching users

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Network Request**:
- Parameter sent: `[e.g., keyword=admin]`
- MSW Handler response: `[Number of users returned]`

---

### 2.2.2 Search by Username (P0)

**Expected**: Filter users matching username

**Steps**:
1. Type "golduser" in search box
2. Verify filtering works

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

### 2.2.3 Search by Display Name (P0)

**Expected**: Filter users matching display name

**Steps**:
1. Type "Gold" in search box
2. Should match "Gold Member"

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

### 2.2.4 Case-Insensitive Search (P1)

**Expected**: "ADMIN" matches "admin@example.com"

**Steps**:
1. Type "ADMIN" (uppercase) in search box
2. Verify lowercase emails matched

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

### 2.2.5 Empty Search Results (P1)

**Expected**: Show "No matches found"

**Steps**:
1. Type nonsense keyword (e.g., "zzz999")
2. Verify empty state message

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

### 2.2.6 Filter by Status (P0)

**Expected**: Show only active/suspended users

**Steps**:
1. Select "Active" in status dropdown
2. Verify `?status=active` in network request
3. Verify only active users shown

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

### 2.2.7 Combined Filters (P1)

**Expected**: Search + status filter work together

**Steps**:
1. Type search keyword
2. Select status filter
3. Verify both parameters in request: `?keyword=...&status=...`

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

## 3. CRUD Happy Paths

### 3.3.1 Create User (P0)

**Expected**: User successfully created and appears in list

**Steps**:
1. Click "Add User" button
2. Fill form:
   - Email: test@example.com
   - Username: testuser
   - Display Name: Test User
   - Membership Tier: free
   - Auth Provider: email
   - Status: active
   - Email Verified: checked
3. Submit form
4. Verify success notification
5. Verify new user in list

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Network Request**:
- Method: POST
- Endpoint: /admin/users/
- Request Body Format: `[camelCase or snake_case?]`
- Response Status: `[e.g., 201]`

**Data Mapping Verification**:
- Frontend sends: `{ email, username, displayName, membershipTier, ... }` (camelCase)
- MSW receives: `[Verify in Network tab]`
- MSW stores: `{ email, username, display_name, membership_tier, ... }` (snake_case)

---

### 3.3.2 View User Details (P0)

**Expected**: Modal/page opens with user details

**Steps**:
1. Click on a user row (e.g., admin@example.com)
2. Verify GET request: `/admin/users/1`
3. Verify all fields displayed correctly

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Data Displayed**:
- Email: `[value]`
- Username: `[value]`
- Display Name: `[value]`
- Membership Tier: `[value]`
- Role Badge: `[Should be "USER"]`
- Status: `[value]`
- Timestamps: `[Format: readable date?]`

---

### 3.3.3 Update User (P0)

**Expected**: User successfully updated

**Steps**:
1. Click "Edit" on a user
2. Modify Display Name: "Updated Name"
3. Modify Membership Tier: gold
4. Save changes
5. Verify success notification
6. Verify changes reflected in list

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Network Request**:
- Method: PUT
- Endpoint: /admin/users/:id
- Request Body: `[Partial update or full object?]`
- Response Status: `[e.g., 200]`

---

### 3.3.4 Delete User (P0)

**Expected**: User successfully deleted

**Steps**:
1. Click "Delete" on a user
2. Confirm deletion in dialog
3. Verify success notification
4. Verify user removed from list

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Network Request**:
- Method: DELETE
- Endpoint: /admin/users/:id
- Response Status: `[e.g., 200]`

---

## 4. CRUD Error Paths

### 4.4.1 Network Failure (P0)

**Expected**: Show error toast, retry button

**Steps**:
1. (May require MSW handler override to return 500)
2. Attempt to create/update/delete user
3. Observe error handling

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Error Message Shown**: `[e.g., "Request failed. Please try again."]`

---

### 4.4.2 Validation Error (P0)

**Expected**: Show field error, prevent submission

**Steps**:
1. Click "Add User"
2. Leave required fields empty (e.g., email)
3. Attempt to submit
4. Verify validation error displayed

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Validation Messages**: `[e.g., "Email is required"]`

---

### 4.4.3 Duplicate User (P1)

**Expected**: Show "Email already exists" error

**Steps**:
1. Try to create user with email: admin@example.com (existing)
2. Verify appropriate error message

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

### 4.4.4 Not Found (P1)

**Expected**: Show 404 error message

**Steps**:
1. (May require manual URL manipulation or MSW override)
2. Try to edit user ID that doesn't exist
3. Verify 404 handling

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

### 4.4.5 Unauthorized (P0)

**Expected**: Redirect to login or show auth error

**Steps**:
1. (May require MSW handler override to return 401)
2. Attempt any operation
3. Verify auth handling

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

---

## 5. Data Integrity Checks

### 5.5.1 Role Badge Always "USER" (P0)

**Expected**: All users show "USER" role badge

**Steps**:
1. View user list
2. Check all role badges
3. Create new user, verify role badge
4. Update user, verify role badge unchanged

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Role Values Observed**: `[e.g., All showing "USER"]`

---

### 5.5.2 Timestamp Warnings (P1)

**Expected**: Check console for invalid timestamp warnings

**Steps**:
1. Open browser console
2. Perform CRUD operations
3. Look for timestamp-related warnings

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Console Warnings** (if any):
```
[Paste console warnings here]
```

---

### 5.5.3 Snake_case → camelCase Mapping (P0)

**Expected**: All fields correctly mapped in UI

**Steps**:
1. View user details
2. Check Network tab response (snake_case)
3. Verify UI displays correct values (from camelCase)

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Mapping Verification**:
- Backend sends: `{ display_name, membership_tier, auth_provider, email_verified, ... }`
- UI displays: `{ displayName, membershipTier, authProvider, emailVerified, ... }`

**Fields Checked**:
- [ ] display_name → displayName
- [ ] membership_tier → membershipTier
- [ ] auth_provider → authProvider
- [ ] email_verified → emailVerified
- [ ] avatar_url → avatarUrl
- [ ] created_at → createdAt
- [ ] updated_at → updatedAt
- [ ] last_login → lastLogin
- [ ] daily_api_quota → dailyApiQuota
- [ ] api_calls_today → apiCallsToday
- [ ] total_analyses → totalAnalyses
- [ ] is_premium → isPremium
- [ ] login_count → loginCount

---

### 5.5.4 CamelCase → snake_case Submission (P0)

**Expected**: Form submissions send correct format

**Steps**:
1. Create or update user
2. Check Network tab request body
3. Verify camelCase sent from frontend
4. Verify MSW handler receives and converts to snake_case

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Request Body Verification**:
- Frontend sends: `{ displayName, membershipTier, ... }` (camelCase)
- MSW stores as: `{ display_name, membership_tier, ... }` (snake_case)

---

### 5.5.5 Default Values (P1)

**Expected**: Empty tier becomes "free" in mapper

**Steps**:
1. Create user without selecting membership tier
2. Verify default value applied
3. Check mapper logic handling

**Result**: [ ] PASS [ ] FAIL [ ] BLOCKED

**Actual Behavior**:
```
[Describe what happened]
```

**Default Values Observed**:
- Empty tier → `[e.g., "free"]`
- Other defaults: `[list any observed]`

---

## Summary & Findings

### Overall Status

**Test Execution Date**: [Date completed]
**Total Scenarios**: 26
**Passed**: [X]
**Failed**: [X]
**Blocked**: [X]
**Pass Rate**: [X]%

### Critical Issues Found

1. **[Issue Title]**
   - **Severity**: Critical/High/Medium/Low
   - **Scenario**: [Test ID]
   - **Description**: [What went wrong]
   - **Expected**: [What should happen]
   - **Actual**: [What actually happened]
   - **Workaround**: [If any]
   - **Action Required**: [What needs to be fixed]

### Non-Critical Issues Found

1. **[Issue Title]**
   - **Severity**: Low/Cosmetic
   - **Scenario**: [Test ID]
   - **Description**: [Minor issue description]
   - **Recommendation**: [Optional improvement]

### Deviations from Expected Behavior

- [List any differences between expected and actual behavior]
- [Note any MSW handler adjustments needed]
- [Note any UI behavior adjustments needed]

### Blocked Scenarios

- **[Scenario ID]**: [Reason blocked]
- **[Scenario ID]**: [Reason blocked]

### Performance Notes

- Page load time: `[e.g., < 1s]`
- API response time (MSW): `[e.g., instant]`
- Large list rendering: `[Any lag observed?]`

### Browser Compatibility Notes

- Chrome: `[Version tested, any issues?]`
- Firefox: `[If tested]`
- Safari: `[If tested]`

### Screenshots Attached

- [ ] Initial page load
- [ ] Pagination controls
- [ ] Search functionality
- [ ] Create user form
- [ ] User details view
- [ ] Update user flow
- [ ] Delete confirmation
- [ ] Error states
- [ ] Role badge display
- [ ] Data mapping verification

---

## Recommendations for Next Phase

### Must Fix Before Production

1. [Critical issue that must be resolved]
2. [Another blocking issue]

### Should Fix Soon

1. [Important but not blocking]
2. [Quality improvement]

### Nice to Have

1. [Optional enhancement]
2. [Future consideration]

### MSW Handler Adjustments Needed

- [ ] [Specific handler change]
- [ ] [Another adjustment]

### UI Behavior Adjustments Needed

- [ ] [Specific UI fix]
- [ ] [Another change]

---

## Sign-Off

**Tester**: [Name]
**Date**: [Date]
**Status**: [ ] All scenarios complete [ ] Partially complete [ ] Blocked

**Ready for**: [ ] Backend cleanup phase [ ] Additional testing [ ] Production deployment

---

## Appendix: Test Data Used

### Mock Users (from adminUsers.ts)

1. **Admin User** (ID: 1)
   - Email: admin@example.com
   - Username: admin
   - Tier: diamond
   - Status: active

2. **Gold Member** (ID: 2)
   - Email: gold@example.com
   - Username: golduser
   - Tier: gold
   - Status: active

3. **Free User** (ID: 3)
   - Email: free@example.com
   - Username: freeuser
   - Tier: free
   - Status: active

4. **Suspended User** (ID: 4)
   - Email: suspended@example.com
   - Username: suspendeduser
   - Tier: free
   - Status: suspended

### Test Data Created During Testing

- [List any users created during testing]
- [Note their IDs and key properties]
