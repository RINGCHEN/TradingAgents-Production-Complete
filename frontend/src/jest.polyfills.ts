/**
 * Jest Polyfills for MSW v2
 * Must be loaded before any MSW imports
 */

import { TextEncoder, TextDecoder } from 'util';

// @ts-ignore
global.TextEncoder = TextEncoder;
// @ts-ignore
global.TextDecoder = TextDecoder;

// Export to ensure this module executes
export {};
