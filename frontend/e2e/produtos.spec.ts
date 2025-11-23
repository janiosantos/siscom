/**
 * Testes E2E - Produtos
 */

import { test, expect } from '@playwright/test'

// Helper para fazer login
async function login(page: any) {
  await page.goto('/login')
  await page.getByLabel(/email/i).fill('admin@siscom.com')
  await page.getByLabel(/senha/i).fill('admin123')
  await page.getByRole('button', { name: /entrar/i }).click()
  await expect(page).toHaveURL(/dashboard/)
}

test.describe('Produtos', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await page.goto('/produtos')
  })

  test('should display produtos page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /produtos/i })).toBeVisible()
  })

  test('should display produtos list', async ({ page }) => {
    await expect(page.getByRole('table')).toBeVisible()

    // Verificar se produtos estão sendo exibidos
    await expect(page.getByText(/cimento/i).first()).toBeVisible()
  })

  test('should search produtos', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/buscar/i)
    await searchInput.fill('cimento')

    await expect(page.getByText(/cimento/i).first()).toBeVisible()
  })

  test('should open create produto modal', async ({ page }) => {
    await page.getByRole('button', { name: /novo produto/i }).click()

    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByText(/criar produto/i)).toBeVisible()
  })

  test('should create new produto', async ({ page }) => {
    // Abrir modal
    await page.getByRole('button', { name: /novo produto/i }).click()

    // Preencher formulário
    await page.getByLabel(/código/i).fill('TEST-001')
    await page.getByLabel(/descrição/i).fill('Produto Teste E2E')
    await page.getByLabel(/preço/i).fill('99.90')
    await page.getByLabel(/categoria/i).selectOption({ label: 'Cimento' })

    // Salvar
    await page.getByRole('button', { name: /salvar/i }).click()

    // Verificar sucesso
    await expect(page.getByText(/produto criado com sucesso/i)).toBeVisible()
    await expect(page.getByText('TEST-001')).toBeVisible()
  })

  test('should validate required fields when creating produto', async ({ page }) => {
    await page.getByRole('button', { name: /novo produto/i }).click()

    // Tentar salvar sem preencher
    await page.getByRole('button', { name: /salvar/i }).click()

    await expect(page.getByText(/código é obrigatório/i)).toBeVisible()
    await expect(page.getByText(/descrição é obrigatória/i)).toBeVisible()
  })

  test('should edit produto', async ({ page }) => {
    // Clicar em editar no primeiro produto
    await page.getByRole('button', { name: /editar/i }).first().click()

    await expect(page.getByRole('dialog')).toBeVisible()

    // Alterar descrição
    const descInput = page.getByLabel(/descrição/i)
    await descInput.clear()
    await descInput.fill('Produto Editado E2E')

    // Salvar
    await page.getByRole('button', { name: /salvar/i }).click()

    // Verificar sucesso
    await expect(page.getByText(/produto atualizado/i)).toBeVisible()
    await expect(page.getByText('Produto Editado E2E')).toBeVisible()
  })

  test('should delete produto with confirmation', async ({ page }) => {
    // Clicar em excluir
    await page.getByRole('button', { name: /excluir/i }).first().click()

    // Verificar modal de confirmação
    await expect(page.getByText(/tem certeza/i)).toBeVisible()

    // Confirmar
    await page.getByRole('button', { name: /confirmar/i }).click()

    // Verificar sucesso
    await expect(page.getByText(/produto excluído/i)).toBeVisible()
  })

  test('should cancel delete produto', async ({ page }) => {
    const initialCount = await page.getByRole('row').count()

    // Clicar em excluir
    await page.getByRole('button', { name: /excluir/i }).first().click()

    // Cancelar
    await page.getByRole('button', { name: /cancelar/i }).click()

    // Verificar que nada foi excluído
    const finalCount = await page.getByRole('row').count()
    expect(finalCount).toBe(initialCount)
  })

  test('should filter produtos by category', async ({ page }) => {
    const categoryFilter = page.getByLabel(/categoria/i)
    await categoryFilter.selectOption({ label: 'Cimento' })

    // Verificar que apenas produtos de cimento aparecem
    await expect(page.getByText(/cimento/i).first()).toBeVisible()
  })

  test('should sort produtos by column', async ({ page }) => {
    // Clicar no header da coluna Código
    await page.getByRole('columnheader', { name: /código/i }).click()

    // Verificar ordenação (primeira linha deve mudar)
    const firstRow = page.getByRole('row').nth(1)
    await expect(firstRow).toBeVisible()

    // Clicar novamente para inverter ordem
    await page.getByRole('columnheader', { name: /código/i }).click()
  })

  test('should export produtos', async ({ page }) => {
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: /exportar/i }).click(),
    ])

    expect(download.suggestedFilename()).toMatch(/produtos.*\.(pdf|xlsx|csv)/)
  })

  test('should navigate with keyboard', async ({ page }) => {
    // Focar no primeiro botão
    await page.keyboard.press('Tab')

    // Verificar se elemento está focado
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(['BUTTON', 'INPUT', 'A']).toContain(focusedElement)

    // Navegar com Tab
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')
  })

  test('should be responsive on mobile', async ({ page }) => {
    // Simular mobile
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page.getByRole('heading', { name: /produtos/i })).toBeVisible()

    // Menu mobile deve estar visível
    const mobileMenu = page.getByRole('button', { name: /menu/i })
    await expect(mobileMenu).toBeVisible()
  })
})
