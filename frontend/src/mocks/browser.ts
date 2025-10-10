/**
 * MSW Browser Setup
 * For use in development/browser environment
 */

import { setupWorker } from 'msw/browser';
import { adminUsersHandlers } from './handlers/adminUsers';

// Combine all handlers
const handlers = [
  ...adminUsersHandlers
];

// Setup MSW worker for browser
export const worker = setupWorker(...handlers);
