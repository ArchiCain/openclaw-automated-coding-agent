import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';

// Load environment variables from root .env file
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });

// BASE_URL overrides everything (e.g., http://frontend.app.svc.cluster.local:8080)
// Falls back to localhost with FRONTEND_PORT from .env
const FRONTEND_PORT = process.env.FRONTEND_PORT || '3000';
const baseURL = process.env.BASE_URL || `http://localhost:${FRONTEND_PORT}`;
const isHTTPS = baseURL.startsWith('https://');

// Chromium launch args for remote/container environments
const chromiumArgs: string[] = [];
if (isHTTPS) {
  chromiumArgs.push('--ignore-certificate-errors');
}
// DNS_RESOLVE_RULES maps hostnames when container DNS can't resolve them
// e.g., "app.mac-mini:192.168.86.38,api.mac-mini:192.168.86.38"
if (process.env.DNS_RESOLVE_RULES) {
  const rules = process.env.DNS_RESOLVE_RULES.split(',')
    .map((r) => `MAP ${r.trim().replace(':', ' ')}`)
    .join(', ');
  chromiumArgs.push(`--host-resolver-rules=${rules}`);
}

export default defineConfig({
  testDir: './tests',

  // Test timeout settings
  timeout: 60000, // 60 seconds per test
  expect: {
    timeout: 10000, // 10 seconds for assertions
  },

  // Test execution settings
  fullyParallel: false, // Run tests sequentially to avoid auth conflicts
  forbidOnly: !!process.env.CI, // Fail CI if test.only is left in
  retries: process.env.CI ? 2 : 0, // Retry failed tests in CI
  workers: 1, // Single worker to avoid race conditions with shared auth state

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'], // Console output
  ],

  // Shared settings for all tests
  use: {
    baseURL,

    // Browser context settings
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: isHTTPS,

    // Tracing and debugging
    trace: 'retain-on-failure', // Keep trace only for failed tests
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',

    // Timeouts
    actionTimeout: 15000, // 15 seconds for actions like click, fill
    navigationTimeout: 30000, // 30 seconds for page navigation
  },

  // Browser projects to test against
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
          args: chromiumArgs.length > 0 ? chromiumArgs : undefined,
        },
      },
    },
  ],
});
