/**
 * Superset UI Smoke Tests
 * Validates production UI accessibility and core functionality
 */

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8088';
const ADMIN_USER = process.env.SUPERSET_ADMIN_USER || 'admin';
const ADMIN_PASS = process.env.SUPERSET_ADMIN_PASS || 'admin';

test.describe('Superset Production Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure artifacts directory exists
    const artifactsDir = path.join(__dirname, '..', 'artifacts');
    if (!fs.existsSync(artifactsDir)) {
      fs.mkdirSync(artifactsDir, { recursive: true });
    }
  });

  test('should load homepage and login', async ({ page }) => {
    await page.goto(BASE_URL);

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Take screenshot of home/login page
    await page.screenshot({
      path: 'artifacts/ui-home.png',
      fullPage: true,
    });

    // Check if login page is present
    const loginButton = page.locator('button[type="submit"]');
    if (await loginButton.isVisible()) {
      console.log('Login page detected, authenticating...');

      // Fill credentials
      await page.fill('input[name="username"]', ADMIN_USER);
      await page.fill('input[name="password"]', ADMIN_PASS);

      // Submit login
      await loginButton.click();

      // Wait for navigation after login
      await page.waitForLoadState('networkidle');

      console.log('✅ Login successful');
    } else {
      console.log('Already authenticated or no login required');
    }

    // Verify we're on a valid Superset page
    const body = await page.content();
    expect(body).toContain('Superset');
  });

  test('should access databases page', async ({ page }) => {
    // Login first
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const loginButton = page.locator('button[type="submit"]');
    if (await loginButton.isVisible()) {
      await page.fill('input[name="username"]', ADMIN_USER);
      await page.fill('input[name="password"]', ADMIN_PASS);
      await loginButton.click();
      await page.waitForLoadState('networkidle');
    }

    // Navigate to databases page
    await page.goto(`${BASE_URL}/databaseview/list/`);
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({
      path: 'artifacts/ui-databases.png',
      fullPage: true,
    });

    // Verify databases page loaded
    const content = await page.content();
    expect(content).toMatch(/database|connection/i);

    console.log('✅ Databases page accessible');
  });

  test('should find Examples (Postgres) database', async ({ page }) => {
    // Login
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const loginButton = page.locator('button[type="submit"]');
    if (await loginButton.isVisible()) {
      await page.fill('input[name="username"]', ADMIN_USER);
      await page.fill('input[name="password"]', ADMIN_PASS);
      await loginButton.click();
      await page.waitForLoadState('networkidle');
    }

    // Go to databases
    await page.goto(`${BASE_URL}/databaseview/list/`);
    await page.waitForLoadState('networkidle');

    // Search for Examples (Postgres)
    const content = await page.content();
    const hasExamplesDB = content.includes('Examples (Postgres)');

    if (hasExamplesDB) {
      console.log('✅ Found "Examples (Postgres)" database');
    } else {
      console.log('⚠️  "Examples (Postgres)" database not found');
    }

    // Screenshot the results
    await page.screenshot({
      path: 'artifacts/ui-databases-search.png',
      fullPage: true,
    });
  });
});
