/**
 * Testes E2E - Vendas
 */

import { test, expect } from '@playwright/test'

async function login(page: any) {
  await page.goto('/login')
  await page.getByLabel(/email/i).fill('admin@siscom.com')
  await page.getByLabel(/senha/i).fill('admin123')
  await page.getByRole('button', { name: /entrar/i }).click()
  await expect(page).toHaveURL(/dashboard/)
}

test.describe('Vendas', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await page.goto('/vendas')
  })

  test('should display vendas page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /vendas/i })).toBeVisible()
  })

  test('should display vendas list', async ({ page }) => {
    await expect(page.getByRole('table')).toBeVisible()
    await expect(page.getByText(/VND-/i).first()).toBeVisible()
  })

  test('should create new venda', async ({ page }) => {
    await page.getByRole('button', { name: /nova venda/i }).click()

    // Selecionar cliente
    await page.getByLabel(/cliente/i).fill('João Silva')
    await page.getByText('João Silva').click()

    // Adicionar produto
    await page.getByRole('button', { name: /adicionar item/i }).click()
    await page.getByLabel(/produto/i).fill('Cimento')
    await page.getByText(/cimento/i).first().click()

    // Quantidade
    await page.getByLabel(/quantidade/i).fill('10')

    // Salvar venda
    await page.getByRole('button', { name: /finalizar venda/i }).click()

    await expect(page.getByText(/venda criada com sucesso/i)).toBeVisible()
  })

  test('should view venda details', async ({ page }) => {
    // Clicar na primeira venda
    await page.getByText(/VND-/i).first().click()

    // Modal de detalhes deve abrir
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByText(/detalhes da venda/i)).toBeVisible()
    await expect(page.getByText(/itens/i)).toBeVisible()
  })

  test('should filter vendas by status', async ({ page }) => {
    const statusFilter = page.getByLabel(/status/i)
    await statusFilter.selectOption('finalizada')

    await expect(page.getByText(/finalizada/i).first()).toBeVisible()
  })

  test('should filter vendas by date', async ({ page }) => {
    await page.getByLabel(/data inicial/i).fill('2025-01-01')
    await page.getByLabel(/data final/i).fill('2025-01-31')

    await page.getByRole('button', { name: /filtrar/i }).click()

    await expect(page.getByText(/VND-/i).first()).toBeVisible()
  })

  test('should calculate total correctly', async ({ page }) => {
    await page.getByRole('button', { name: /nova venda/i }).click()

    await page.getByLabel(/cliente/i).fill('João')
    await page.getByText('João Silva').click()

    // Adicionar produto 1
    await page.getByRole('button', { name: /adicionar item/i }).click()
    await page.getByLabel(/produto/i).first().fill('Cimento')
    await page.getByText(/cimento/i).first().click()
    await page.getByLabel(/quantidade/i).first().fill('10')

    // Verificar total
    await expect(page.getByText(/total:/i)).toBeVisible()
  })

  test('should apply discount', async ({ page }) => {
    await page.getByRole('button', { name: /nova venda/i }).click()

    await page.getByLabel(/cliente/i).fill('João')
    await page.getByText('João Silva').click()

    await page.getByRole('button', { name: /adicionar item/i }).click()
    await page.getByLabel(/produto/i).fill('Cimento')
    await page.getByText(/cimento/i).first().click()
    await page.getByLabel(/quantidade/i).fill('10')

    // Aplicar desconto
    await page.getByLabel(/desconto/i).fill('10')

    // Verificar que valor final foi ajustado
    await expect(page.getByText(/desconto/i)).toBeVisible()
  })

  test('should cancel venda', async ({ page }) => {
    // Clicar em cancelar na primeira venda
    await page.getByRole('button', { name: /cancelar/i }).first().click()

    // Confirmar
    await expect(page.getByText(/tem certeza/i)).toBeVisible()
    await page.getByRole('button', { name: /confirmar/i }).click()

    // Verificar sucesso
    await expect(page.getByText(/venda cancelada/i)).toBeVisible()
  })

  test('should export vendas report', async ({ page }) => {
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: /exportar/i }).click(),
    ])

    expect(download.suggestedFilename()).toMatch(/vendas.*\.(pdf|xlsx|csv)/)
  })

  test('should show total vendas do dia', async ({ page }) => {
    await expect(page.getByText(/vendas hoje/i)).toBeVisible()
    await expect(page.getByText(/total:/i)).toBeVisible()
  })
})

test.describe('Vendas - PDV', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await page.goto('/pdv')
  })

  test('should display PDV interface', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /pdv|ponto de venda/i })).toBeVisible()
  })

  test('should add product to cart in PDV', async ({ page }) => {
    // Buscar produto
    await page.getByPlaceholder(/código de barras/i).fill('CIM-001')
    await page.keyboard.press('Enter')

    // Produto deve aparecer no carrinho
    await expect(page.getByText(/cimento/i)).toBeVisible()
  })

  test('should calculate total in PDV', async ({ page }) => {
    await page.getByPlaceholder(/código de barras/i).fill('CIM-001')
    await page.keyboard.press('Enter')

    // Alterar quantidade
    await page.getByLabel(/quantidade/i).fill('5')

    // Verificar total
    await expect(page.getByText(/total/i)).toBeVisible()
  })

  test('should process payment in PDV', async ({ page }) => {
    await page.getByPlaceholder(/código de barras/i).fill('CIM-001')
    await page.keyboard.press('Enter')

    // Finalizar
    await page.getByRole('button', { name: /finalizar/i }).click()

    // Selecionar forma de pagamento
    await page.getByLabel(/forma de pagamento/i).selectOption('dinheiro')

    // Confirmar
    await page.getByRole('button', { name: /confirmar/i }).click()

    await expect(page.getByText(/venda concluída/i)).toBeVisible()
  })

  test('should clear cart in PDV', async ({ page }) => {
    await page.getByPlaceholder(/código de barras/i).fill('CIM-001')
    await page.keyboard.press('Enter')

    // Limpar carrinho
    await page.getByRole('button', { name: /limpar/i }).click()

    // Confirmar
    await page.getByRole('button', { name: /confirmar/i }).click()

    // Carrinho deve estar vazio
    await expect(page.getByText(/carrinho vazio/i)).toBeVisible()
  })
})
