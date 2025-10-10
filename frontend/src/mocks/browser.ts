/**
 * MSW Browser Setup
 * For use in development/browser environment
 * Using MSW v1.3.2 API
 */

import { setupWorker } from 'msw';
import { adminUsersHandlers } from './handlers/adminUsers';

// Combine all handlers
const handlers = [
  ...adminUsersHandlers
];

// Setup MSW worker for browser
export const worker = setupWorker(...handlers);
