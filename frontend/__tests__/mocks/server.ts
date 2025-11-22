/**
 * MSW Server Setup (Node)
 *
 * Configuração do MSW para ambientes Node (Jest)
 */

import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// Setup server com handlers
export const server = setupServer(...handlers)

// Configuração global para testes
beforeAll(() => {
  // Iniciar servidor antes de todos os testes
  server.listen({ onUnhandledRequest: 'warn' })
})

afterEach(() => {
  // Resetar handlers após cada teste
  server.resetHandlers()
})

afterAll(() => {
  // Fechar servidor após todos os testes
  server.close()
})
