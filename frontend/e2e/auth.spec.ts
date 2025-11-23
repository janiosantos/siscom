/**
 * Testes E2E - Autenticação
 */

import { test, expect } from '@playwright/test'

test.describe('Autenticação', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login')

    await expect(page).toHaveTitle(/login/i)
    await expect(page.getByRole('heading', { name: /login/i })).toBeVisible()
  })

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto('/login')

    // Preencher formulário
    await page.getByLabel(/email/i).fill('admin@siscom.com')
    await page.getByLabel(/senha/i).fill('admin123')

    // Submeter
    await page.getByRole('button', { name: /entrar/i }).click()

    // Verificar redirecionamento para dashboard
    await expect(page).toHaveURL(/dashboard/)
    await expect(page.getByText(/bem-vindo/i)).toBeVisible()
  })

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel(/email/i).fill('wrong@email.com')
    await page.getByLabel(/senha/i).fill('wrongpassword')
    await page.getByRole('button', { name: /entrar/i }).click()

    await expect(page.getByText(/credenciais inválidas/i)).toBeVisible()
  })

  test('should validate required fields', async ({ page }) => {
    await page.goto('/login')

    await page.getByRole('button', { name: /entrar/i }).click()

    await expect(page.getByText(/email é obrigatório/i)).toBeVisible()
    await expect(page.getByText(/senha é obrigatória/i)).toBeVisible()
  })

  test('should logout successfully', async ({ page }) => {
    // Login primeiro
    await page.goto('/login')
    await page.getByLabel(/email/i).fill('admin@siscom.com')
    await page.getByLabel(/senha/i).fill('admin123')
    await page.getByRole('button', { name: /entrar/i }).click()

    await expect(page).toHaveURL(/dashboard/)

    // Logout
    await page.getByRole('button', { name: /logout|sair/i }).click()

    await expect(page).toHaveURL(/login/)
  })

  test('should redirect to login if not authenticated', async ({ page }) => {
    await page.goto('/dashboard')

    await expect(page).toHaveURL(/login/)
  })

  test('should have password visibility toggle', async ({ page }) => {
    await page.goto('/login')

    const passwordInput = page.getByLabel(/senha/i)
    await expect(passwordInput).toHaveAttribute('type', 'password')

    // Clicar no botão de mostrar senha
    await page.getByRole('button', { name: /mostrar senha/i }).click()

    await expect(passwordInput).toHaveAttribute('type', 'text')
  })
})
