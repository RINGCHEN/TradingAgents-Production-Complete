// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// MSW (Mock Service Worker) setup for API mocking in tests
// Note: Polyfills are loaded via jest.config.cjs setupFiles

// TODO Phase 2: Enable MSW after resolving Jest module resolution issues
// MSW v2 uses conditional exports that Jest 29 can't handle properly
// Options: Upgrade Jest 30, downgrade to MSW v1, or use Jest ESM transformer
//
// import { server } from './mocks/server';
// import { resetMockUsers } from './mocks/handlers/adminUsers';
//
// beforeAll(() => {
//   server.listen({ onUnhandledRequest: 'warn' });
// });
//
// afterEach(() => {
//   server.resetHandlers();
//   resetMockUsers();
// });
//
// afterAll(() => {
//   server.close();
// });