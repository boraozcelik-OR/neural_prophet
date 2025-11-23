export const ENV = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  appEnv: import.meta.env.MODE || 'development',
  enableMock: import.meta.env.VITE_ENABLE_MOCK === 'true',
  sentryDsn: import.meta.env.VITE_SENTRY_DSN || '',
};
