/**
 * Testes de Regressão Visual - Produtos
 *
 * Detecta mudanças visuais não intencionais em componentes
 */

import { test, expect } from '@playwright/test'

async function login(page: any) {
  await page.goto('/login')
  await page.getByLabel(/email/i).fill('admin@siscom.com')
  await page.getByLabel(/senha/i).fill('admin123')
  await page.getByRole('button', { name: /entrar/i }).click()
  await expect(page).toHaveURL(/dashboard/)
}

test.describe('Visual Regression - Produtos', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await page.goto('/produtos')
    // Aguardar página carregar completamente
    await page.waitForLoadState('networkidle')
  })

  test('should match produtos page screenshot', async ({ page }) => {
    // Screenshot da página completa
    await expect(page).toHaveScreenshot('produtos-page.png', {
      fullPage: true,
      animations: 'disabled',
    })
  })

  test('should match produtos table screenshot', async ({ page }) => {
    // Screenshot apenas da tabela
    const table = page.getByRole('table')
    await expect(table).toHaveScreenshot('produtos-table.png')
  })

  test('should match new produto modal screenshot', async ({ page }) => {
    await page.getByRole('button', { name: /novo produto/i }).click()

    const modal = page.getByRole('dialog')
    await expect(modal).toBeVisible()

    await expect(modal).toHaveScreenshot('produto-modal.png')
  })

  test('should match produtos page on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page).toHaveScreenshot('produtos-mobile.png', {
      fullPage: true,
    })
  })

  test('should match produtos page on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })

    await expect(page).toHaveScreenshot('produtos-tablet.png', {
      fullPage: true,
    })
  })

  test('should match empty state screenshot', async ({ page }) => {
    // Simular estado vazio (necessita mock do backend)
    await page.route('**/api/v1/produtos', route => {
      route.fulfill({ json: [] })
    })

    await page.reload()
    await page.waitForLoadState('networkidle')

    await expect(page).toHaveScreenshot('produtos-empty.png')
  })

  test('should match loading state screenshot', async ({ page }) => {
    // Interceptar e atrasar resposta para capturar loading
    await page.route('**/api/v1/produtos', route => {
      setTimeout(() => route.continue(), 2000)
    })

    await page.reload()

    // Capturar estado de loading
    const loadingIndicator = page.getByRole('status')
    await expect(loadingIndicator).toHaveScreenshot('produtos-loading.png')
  })

  test('should match error state screenshot', async ({ page }) => {
    // Simular erro
    await page.route('**/api/v1/produtos', route => {
      route.fulfill({ status: 500, json: { detail: 'Erro ao carregar' } })
    })

    await page.reload()
    await page.waitForLoadState('networkidle')

    await expect(page).toHaveScreenshot('produtos-error.png')
  })
})

test.describe('Visual Regression - Dark Mode', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
  })

  test('should match produtos page in dark mode', async ({ page }) => {
    // Ativar dark mode
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.goto('/produtos')
    await page.waitForLoadState('networkidle')

    await expect(page).toHaveScreenshot('produtos-dark.png', {
      fullPage: true,
    })
  })
})

test.describe('Visual Regression - Hover States', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await page.goto('/produtos')
    await page.waitForLoadState('networkidle')
  })

  test('should match button hover state', async ({ page }) => {
    const button = page.getByRole('button', { name: /novo produto/i })
    await button.hover()

    await expect(button).toHaveScreenshot('button-hover.png')
  })

  test('should match table row hover state', async ({ page }) => {
    const firstRow = page.getByRole('row').nth(1)
    await firstRow.hover()

    await expect(firstRow).toHaveScreenshot('table-row-hover.png')
  })
})
