/**
 * Lighthouse CI Configuration
 *
 * Performance budgets e thresholds para Core Web Vitals
 */

module.exports = {
  ci: {
    collect: {
      // URLs para testar
      url: [
        'http://localhost:3000',
        'http://localhost:3000/login',
        'http://localhost:3000/dashboard',
        'http://localhost:3000/produtos',
        'http://localhost:3000/vendas',
      ],
      // Número de execuções para média
      numberOfRuns: 3,
      // Configurações do servidor
      startServerCommand: 'npm run start',
      startServerReadyPattern: 'ready',
      startServerReadyTimeout: 60000,
    },
    assert: {
      // Thresholds mínimos
      assertions: {
        // Performance Score
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],

        // Core Web Vitals
        'first-contentful-paint': ['warn', { maxNumericValue: 1800 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
        'speed-index': ['warn', { maxNumericValue: 3400 }],
        'interactive': ['warn', { maxNumericValue: 3800 }],

        // Métricas específicas
        'max-potential-fid': ['warn', { maxNumericValue: 130 }],
        'server-response-time': ['warn', { maxNumericValue: 600 }],
        'first-meaningful-paint': ['warn', { maxNumericValue: 1600 }],

        // Network
        'network-requests': ['warn', { maxNumericValue: 50 }],
        'network-rtt': ['warn', { maxNumericValue: 150 }],
        'network-server-latency': ['warn', { maxNumericValue: 100 }],

        // JavaScript
        'bootup-time': ['warn', { maxNumericValue: 3500 }],
        'mainthread-work-breakdown': ['warn', { maxNumericValue: 4000 }],

        // Resources
        'total-byte-weight': ['warn', { maxNumericValue: 1000000 }], // 1MB
        'dom-size': ['warn', { maxNumericValue: 1500 }],

        // Images
        'modern-image-formats': 'warn',
        'uses-optimized-images': 'warn',
        'uses-responsive-images': 'warn',
        'offscreen-images': 'warn',

        // Assets
        'uses-text-compression': 'warn',
        'unminified-css': 'warn',
        'unminified-javascript': 'warn',
        'unused-css-rules': 'warn',
        'unused-javascript': 'warn',

        // Acessibilidade
        'aria-allowed-attr': 'error',
        'aria-required-attr': 'error',
        'aria-valid-attr': 'error',
        'button-name': 'error',
        'color-contrast': 'warn',
        'duplicate-id-active': 'error',
        'html-has-lang': 'error',
        'image-alt': 'error',
        'label': 'error',
        'link-name': 'error',

        // Best Practices
        'errors-in-console': 'warn',
        'no-document-write': 'error',
        'uses-http2': 'warn',
        'uses-passive-event-listeners': 'warn',

        // SEO
        'meta-description': 'warn',
        'document-title': 'error',
        'viewport': 'error',
      },
    },
    upload: {
      // Opcional: Upload para servidor Lighthouse CI
      // target: 'lhci',
      // serverBaseUrl: 'https://your-lhci-server.com',
      // token: process.env.LHCI_TOKEN,

      // Ou upload para storage temporário
      target: 'temporary-public-storage',
    },
  },
}
