/**
 * Stryker Mutation Testing Configuration
 *
 * Testa a qualidade dos testes introduzindo mutações no código
 */

/** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
const config = {
  // Usar Jest como test runner
  testRunner: 'jest',

  // Cobertura de código
  coverageAnalysis: 'perTest',

  // Arquivos para mutar
  mutate: [
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    'hooks/**/*.{ts,tsx}',
    'app/**/*.{ts,tsx}',
    '!**/*.test.{ts,tsx}',
    '!**/*.spec.{ts,tsx}',
    '!**/__tests__/**',
    '!**/node_modules/**',
    '!**/.next/**',
  ],

  // Reporters
  reporters: [
    'html',
    'clear-text',
    'progress',
    'dashboard',
  ],

  // Thresholds
  thresholds: {
    high: 80,
    low: 60,
    break: 50,
  },

  // Timeout
  timeoutMS: 60000,
  timeoutFactor: 2,

  // Concorrência
  concurrency: 4,

  // Plugins
  plugins: [
    '@stryker-mutator/jest-runner',
    '@stryker-mutator/typescript-checker',
  ],

  // TypeScript checker
  checkers: ['typescript'],
  tsconfigFile: 'tsconfig.json',

  // Mutators
  mutator: {
    plugins: ['typescript'],
    excludedMutations: [
      // Excluir mutações que geram muito ruído
      'StringLiteral', // Strings literais
      'ObjectLiteral', // Objetos literais
    ],
  },

  // Jest config
  jest: {
    configFile: 'jest.config.js',
    enableFindRelatedTests: true,
  },

  // Ignorar mutantes específicos
  ignorePatterns: [
    // Configurações
    '*.config.{js,ts,mjs}',

    // Setup files
    'jest.setup.js',
    'playwright.config.ts',

    // Types
    '*.d.ts',
    'types/**',

    // Mocks
    '__mocks__/**',
    '__tests__/mocks/**',

    // Stories (se usar Storybook)
    '*.stories.{ts,tsx}',
  ],

  // Dashboard reporter (opcional)
  dashboard: {
    // Necessita configuração de projeto em dashboard.stryker-mutator.io
    // project: 'github.com/seu-usuario/siscom',
    // version: 'main',
    // module: 'frontend',
  },
}

export default config
