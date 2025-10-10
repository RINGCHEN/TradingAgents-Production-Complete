/**
 * MSW Server Setup
 * For use in Node.js test environment (Jest)
 * Using MSW v1.3.2 for Jest 29 compatibility
 */

import { setupServer } from 'msw/node';
import { adminUsersHandlers } from './handlers/adminUsers';

// Combine all handlers
const handlers = [
  ...adminUsersHandlers
];

// Setup MSW server for Node.js tests
export const server = setupServer(...handlers);
