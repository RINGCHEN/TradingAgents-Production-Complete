// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// MSW (Mock Service Worker) setup for API mocking in tests
// Using MSW v1.3.2 for Jest 29 compatibility
import { server } from './mocks/server';
import { resetMockUsers } from './mocks/handlers/adminUsers';

// Start MSW server before all tests
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'warn' // Warn about unhandled requests instead of erroring
  });
});

// Reset handlers and mock data after each test to ensure test isolation
afterEach(() => {
  server.resetHandlers();
  resetMockUsers(); // Reset user fixture data
});

// Clean up MSW server after all tests complete
afterAll(() => {
  server.close();
});