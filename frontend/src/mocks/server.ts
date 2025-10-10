/**
 * MSW Server Setup
 * For use in Node.js test environment (Jest)
 *
 * Note: Polyfills are handled in ../jest.polyfills.ts (loaded via setupTests.ts)
 */

import { setupServer } from 'msw/node';
import { adminUsersHandlers } from './handlers/adminUsers';

// Combine all handlers
const handlers = [
  ...adminUsersHandlers
];

// Setup MSW server for Node.js tests
export const server = setupServer(...handlers);
