/**
 * Environment helper that works in both browser (Vite) and Node (Jest) contexts.
 *
 * Vite injects variables on `import.meta.env`, but Jest/Node do not define
 * `import.meta`. This module normalises access so shared code can read values
 * without unsafe references that break tests.
 */

type MaybeBoolean = boolean | string | undefined;

interface NormalisedEnv {
  isDev: boolean;
  apiBaseUrl: string;
  apiTimeout: number;
  environment: string;
}

const booleanFrom = (value: MaybeBoolean, fallback: boolean): boolean => {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    return value.toLowerCase() === 'true';
  }
  return fallback;
};

const stringFrom = (...values: Array<string | undefined>): string | undefined => {
  for (const value of values) {
    if (typeof value === 'string' && value.trim().length > 0) {
      return value;
    }
  }
  return undefined;
};

const numberFrom = (value: string | undefined, fallback: number): number => {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
};

const getImportMetaEnv = (): Record<string, any> | undefined => {
  try {
    // Using Function constructor avoids TypeScript parse errors when import.meta is unavailable.
    return Function('return import.meta.env')();
  } catch {
    return undefined;
  }
};

const getProcessEnv = (): NodeJS.ProcessEnv => {
  if (typeof process !== 'undefined' && typeof process.env !== 'undefined') {
    return process.env;
  }
  return {};
};

const importMetaEnv = getImportMetaEnv();
const processEnv = getProcessEnv();

const resolveEnv = (): NormalisedEnv => {
  const isDev = booleanFrom(
    importMetaEnv?.DEV ?? processEnv.VITE_DEV ?? processEnv.DEV,
    (processEnv.NODE_ENV ?? 'development') !== 'production'
  );

  const apiBaseUrl =
    stringFrom(
      importMetaEnv?.VITE_API_BASE_URL,
      processEnv.VITE_API_BASE_URL,
      processEnv.API_BASE_URL
    ) ?? '';

  const apiTimeout = numberFrom(
    stringFrom(importMetaEnv?.VITE_API_TIMEOUT, processEnv.VITE_API_TIMEOUT, processEnv.API_TIMEOUT),
    10000
  );

  const environment =
    stringFrom(
      importMetaEnv?.VITE_ENVIRONMENT,
      processEnv.VITE_ENVIRONMENT,
      processEnv.NODE_ENV
    ) ?? 'development';

  return {
    isDev,
    apiBaseUrl,
    apiTimeout,
    environment
  };
};

export const env = resolveEnv();
