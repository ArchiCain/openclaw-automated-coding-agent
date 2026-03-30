/**
 * Test Data and Fixtures for E2E Tests
 *
 * Contains test credentials, URLs, and helper data used across tests.
 */

/**
 * Test user credentials
 * These match the admin user configured in Keycloak realm
 */
export const testUser = {
  username: 'admin',
  password: 'admin',
};

/**
 * Application URLs
 *
 * Resolved from environment variables when running against a remote deployment
 * (e.g., K8s via OpenClaw), or falls back to localhost for local dev.
 *
 * Env vars: BASE_URL, E2E_BACKEND_URL, E2E_KEYCLOAK_URL
 */
export const urls = {
  frontend: process.env.BASE_URL || 'http://localhost:3000',
  backend: process.env.E2E_BACKEND_URL || 'http://localhost:8085',
  keycloak: process.env.E2E_KEYCLOAK_URL || 'http://localhost:8081',
};

/**
 * Page paths for navigation
 */
export const paths = {
  home: '/',
  login: '/login',
  conversationalAi: '/', // ConversationalAI is the index route
};

/**
 * Test messages for chat testing
 */
export const testMessages = {
  simple: 'Hello, AI assistant!',
  question: 'What is the capital of France?',
  longText: 'This is a longer test message that contains multiple sentences. It is used to test how the chat interface handles longer inputs. The interface should properly display and process this message.',
};

/**
 * Timeout configurations
 */
export const timeouts = {
  short: 5000,     // 5 seconds
  medium: 15000,   // 15 seconds
  long: 30000,     // 30 seconds
  streaming: 45000, // 45 seconds for AI streaming responses
};
