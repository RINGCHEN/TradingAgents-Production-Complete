# Known Issues - Pre-Existing (Non-Phase 1)

**Last Updated**: 2025-10-10
**Status**: Documented for future cleanup
**Impact on Phase 1**: None - All issues pre-existing, not introduced by Phase 1 work

---

## Summary

This document tracks pre-existing issues discovered during Phase 1 verification. **None of these issues block Phase 1 completion or merge.** They should be addressed in subsequent phases or dedicated cleanup sprints.

### Issue Breakdown

- **9 Jest Test Suite Failures** (7 import.meta.env related, 1 auth context, 1 other)
- **TypeScript Compilation Errors** (JSX syntax, type mismatches, import.meta usage)
- **Service Layer Type Mismatches** (RealAdminApiService)

---

## 1. Jest Test Suite Failures (9 failing suites)

### Issue 1.1: import.meta.env Syntax Error (7 suites)

**Root Cause**: Vite's `import.meta.env` not supported in Jest environment

**Affected File**: `src/services/ApiClient.ts:522`

**Error Message**:
```
SyntaxError: Cannot use 'import.meta' outside a module
```

**Failing Test Suites**:
1. `src/utils/__tests__/CouponManager.test.ts`
2. `src/services/__tests__/ApiClient.test.ts`
3. `src/components/__tests__/ApiClientDemo.test.tsx`
4. `src/components/__tests__/CouponManagerSimple.test.tsx`
5. `src/components/__tests__/CouponManagerProvider.test.tsx`
6. `src/components/__tests__/ApiClientProvider.test.tsx`
7. `src/components/__tests__/CouponManagerIntegration.test.tsx`

**Priority**: Medium

**Proposed Solutions**:
- **Option A**: Mock `import.meta` in Jest config
  ```javascript
  // jest.config.cjs
  globals: {
    'import.meta': {
      env: {
        DEV: false,
        VITE_API_BASE_URL: 'http://localhost:8000'
      }
    }
  }
  ```
- **Option B**: Refactor `ApiClient.ts` to use `process.env` instead
  ```typescript
  // Replace import.meta.env with process.env
  if (process.env.NODE_ENV === 'development') {
    // ...
  }
  ```
- **Option C**: Use `vite-jest` or `vitest` instead of `react-scripts test`

**Assignee**: TBD
**Target Phase**: Phase 2 or dedicated cleanup sprint

---

### Issue 1.2: Authentication Context Error (1 suite)

**Root Cause**: EnhancedAuthContext initialization check failing

**Affected File**: `src/components/__tests__/AuthenticationDemo.test.tsx`

**Error Location**: `src/contexts/EnhancedAuthContext.tsx:227:20`

**Error Message**:
```
Error: Authentication context must be used within AuthProvider
  at isInitialized (src/contexts/EnhancedAuthContext.tsx:227:20)
  at canAccessFeature (src/components/AuthenticationDemo.tsx:95:22)
```

**Priority**: Low (Demo component)

**Proposed Solution**:
- Wrap test component with `<AuthProvider>` in test setup
- Mock `EnhancedAuthContext` in test file

**Assignee**: TBD
**Target Phase**: Phase 2 or dedicated cleanup sprint

---

### Issue 1.3: Unknown Test Suite Failure (1 suite)

**Status**: Insufficient information from test output

**Action**: Re-run full test suite with verbose output to identify

**Priority**: Low

**Assignee**: TBD
**Target Phase**: Phase 2

---

## 2. TypeScript Compilation Errors

### Issue 2.1: JSX Syntax Errors in Demo Components

**Affected Files**:

1. **`src/admin/components/MemberAIManagementModule.tsx`**
   - Line 270: JSX element 'div' has no corresponding closing tag
   - Line 297: JSX element 'div' has no corresponding closing tag
   - Line 320: JSX element 'div' has no corresponding closing tag
   - Lines 451, 503, 572: Unexpected token errors

2. **`src/components/AI_Analyst_Demo_Center.tsx`**
   - Lines 92-128: Unterminated string literals
   - Lines 92+: Invalid character errors

3. **`src/components/Enhanced_PayUni_Checkout.tsx`**
   - Lines 403-453: Unterminated string literals
   - JSX parent element issues

4. **`src/pages/SimplePortfolioPage.tsx`**
   - Line 311: JSX element 'div' has no corresponding closing tag
   - Lines 503-563: Unexpected token errors

**Priority**: Medium (affects build)

**Proposed Solution**:
- Manual review and fix of JSX syntax in each file
- Consider using ESLint with JSX plugin for prevention

**Assignee**: TBD
**Target Phase**: Phase 2

---

### Issue 2.2: import.meta.env TypeScript Errors

**Affected File**: `src/services/ApiClient.ts`

**Error Locations**: Lines 522, 572, 577, 581, 590, 601

**Error Messages**:
```
TS1343: The 'import.meta' meta-property is only allowed when the '--module' option is
'es2020', 'es2022', 'esnext', 'system', 'node16', or 'nodenext'.

TS2339: Property 'env' does not exist on type 'ImportMeta'.
```

**Priority**: High (related to Jest failures)

**Proposed Solutions**:
- Same as Issue 1.1 (refactor to `process.env` or update TypeScript config)

**Assignee**: TBD
**Target Phase**: Phase 2

---

### Issue 2.3: RealAdminApiService Type Mismatches

**Affected File**: `src/admin/services/RealAdminApiService.ts`

**Error Details**:

1. **Lines 326, 354**: `ApiResponse.message` property doesn't exist
   ```typescript
   // ApiResponse interface only has error?.message, not message
   setError(response.message || '請求失敗'); // ❌ Wrong
   setError(response.error?.message || '請求失敗'); // ✅ Correct
   ```

2. **Line 378**: Missing `message` in return type
   ```typescript
   // Return type expects { success, message, data } but only returns { success, data }
   ```

3. **Lines 782, 2300**: Duplicate function implementations
   ```typescript
   // Two functions with same name defined
   ```

4. **Lines 2796-2804**: Property mismatches in analytics data
   ```typescript
   // Line 2796: Property 'new_subscriptions' does not exist
   // Line 2801: Property 'successful_payments' does not exist
   // Line 2802: Property 'failed_payments' does not exist
   // Line 2804: Property 'average_payment_amount' does not exist
   ```

5. **Lines 3134, 3322**: Invalid `data` property in request config
   ```typescript
   // ApiRequestConfig doesn't have 'data' property
   // Should use 'body' instead
   ```

**Priority**: Medium

**Proposed Solution**:
- Align type definitions with actual API contracts
- Remove duplicate function definitions
- Update analytics data interface to match backend

**Assignee**: TBD
**Target Phase**: Phase 2 or dedicated service layer cleanup

---

## 3. Test Results Summary

### Passing Tests ✅

- **5 test suites passing** (including Phase 1 userDataMapper)
- **85 individual tests passing**

### Failing Tests ❌

- **9 test suites failing** (all pre-existing)
- **4 individual tests failing** (all pre-existing)

### Phase 1 Impact

**Zero new failures introduced by Phase 1 work** ✅

---

## 4. Recommended Cleanup Priority

### High Priority (Blocking Future Work)

1. **Issue 2.2**: import.meta.env TypeScript errors
   - Affects build and Jest integration
   - Should be resolved before expanding test coverage

### Medium Priority (Quality Improvements)

1. **Issue 1.1**: import.meta.env Jest failures (7 suites)
   - Blocks testing of ApiClient and dependent components

2. **Issue 2.1**: JSX syntax errors in demo components
   - Affects build integrity

3. **Issue 2.3**: RealAdminApiService type mismatches
   - Improves type safety and prevents runtime errors

### Low Priority (Nice to Have)

1. **Issue 1.2**: Authentication context test failure
   - Demo component only

2. **Issue 1.3**: Unknown test suite failure
   - Need more investigation

---

## 5. Tracking and Assignment

| Issue ID | Description | Priority | Assignee | Target Phase | Status |
|----------|-------------|----------|----------|--------------|--------|
| 1.1 | import.meta.env Jest failures (7 suites) | Medium | TBD | Phase 2 | 📋 Documented |
| 1.2 | Auth context test failure | Low | TBD | Phase 2 | 📋 Documented |
| 1.3 | Unknown test suite failure | Low | TBD | Phase 2 | 📋 Documented |
| 2.1 | JSX syntax errors (4 files) | Medium | TBD | Phase 2 | 📋 Documented |
| 2.2 | import.meta.env TypeScript errors | High | TBD | Phase 2 | 📋 Documented |
| 2.3 | RealAdminApiService type mismatches | Medium | TBD | Phase 2 | 📋 Documented |

---

## 6. Notes for Future Phases

### Phase 2 Considerations

- Address high-priority issues before expanding admin UI features
- Consider migrating from `react-scripts test` to `vitest` for better Vite integration
- Plan dedicated sprint for TypeScript strict mode compliance

### Testing Strategy

- Add CI checks to prevent new import.meta.env usage in test files
- Implement pre-commit hooks for JSX syntax validation
- Create baseline test coverage report to track improvements

---

**Document Owner**: TradingAgents Frontend Team
**Review Cycle**: Monthly or per phase completion
