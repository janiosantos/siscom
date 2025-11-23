# SISCOM Frontend - Interface ERP

<div align="center">

![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)
![Tailwind](https://img.shields.io/badge/Tailwind-3-38bdf8.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Interface web moderna para o Sistema ERP SISCOM**

[Demo](#-demo) •
[Instalação](#-instalação) •
[Deploy](#-deploy) •
[Componentes](#-componentes)

</div>

---

## 📋 Sobre

Frontend do sistema ERP SISCOM desenvolvido com Next.js 14 (App Router), fornecendo interface moderna e responsiva para:

- 🏠 Dashboard com métricas em tempo real
- 📦 Gestão de produtos e estoque
- 💰 Vendas e orçamentos
- 📊 Relatórios e análises
- 💳 Pagamentos e financeiro
- 👥 Clientes e fornecedores
- 📄 Documentos fiscais (NF-e)
- ⚙️ Configurações e administração

---

## 🚀 Stack Tecnológica

- **Framework:** Next.js 14 (App Router)
- **React:** 18.x
- **TypeScript:** 5.x
- **Styling:** Tailwind CSS 3.x
- **UI Components:** Shadcn/ui + Radix UI
- **Data Fetching:** SWR (stale-while-revalidate)
- **Forms:** React Hook Form + Zod
- **Charts:** Recharts
- **Icons:** Lucide React
- **Testing:** Jest + React Testing Library
- **E2E:** Playwright
- **Mocks:** MSW (Mock Service Worker)

---

## 📁 Estrutura do Projeto

```
siscom-frontend/
├── app/                   # App Router (Next.js 14)
│   ├── (auth)/           # Rotas de autenticação
│   ├── (dashboard)/      # Rotas do dashboard
│   ├── layout.tsx        # Layout raiz
│   └── page.tsx          # Home page
├── components/            # Componentes React
│   ├── ui/               # Componentes base (Shadcn)
│   ├── navigation/       # Navegação
│   ├── forms/            # Formulários
│   └── charts/           # Gráficos
├── lib/                   # Bibliotecas e utilitários
│   ├── api-client.ts     # Cliente HTTP
│   ├── hooks/            # Custom hooks
│   └── validations/      # Schemas Zod
├── public/                # Arquivos estáticos
├── __tests__/             # Testes
└── e2e/                   # Testes E2E
```

---

## 🛠️ Instalação

### Pré-requisitos

- Node.js 18+
- npm ou yarn ou pnpm

### 1. Clonar Repositório

```bash
git clone https://github.com/janiosantos/siscom-frontend.git
cd siscom-frontend
```

### 2. Instalar Dependências

```bash
npm install
# ou
yarn install
# ou
pnpm install
```

### 3. Configurar Variáveis de Ambiente

```bash
cp .env.example .env.local
```

**.env.local:**
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# App Config
NEXT_PUBLIC_APP_NAME="SISCOM ERP"
NEXT_PUBLIC_APP_VERSION="1.0.0"
```

### 4. Executar Desenvolvimento

```bash
npm run dev
# ou
yarn dev
# ou
pnpm dev
```

Acesse: http://localhost:3000

---

## 🧪 Testes

```bash
# Testes unitários
npm test
npm run test:watch    # Watch mode
npm run test:coverage # Com cobertura

# Testes E2E
npm run test:e2e
npm run test:e2e:ui   # Com interface

# Lint
npm run lint
npm run lint:fix      # Corrigir automaticamente
```

---

## 🏗️ Build

### Desenvolvimento

```bash
npm run dev
```

### Produção

```bash
# Build
npm run build

# Preview
npm start
```

---

## 🐳 Docker

### Desenvolvimento

```bash
docker build -t siscom-frontend:dev .
docker run -p 3000:3000 siscom-frontend:dev
```

### Produção

```bash
docker build -t siscom-frontend:latest -f Dockerfile.prod .
docker run -p 3000:3000 siscom-frontend:latest
```

---

## 🚀 Deploy

### Vercel (Recomendado)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/janiosantos/siscom-frontend)

```bash
# CLI
vercel --prod
```

### Netlify

```bash
npm run build
netlify deploy --prod --dir=.next
```

### Docker + Nginx

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🎨 Componentes Principais

### Dashboard

```tsx
import { DashboardStats } from '@/components/dashboard/stats'

<DashboardStats />
```

**Features:**
- KPIs em tempo real
- Gráficos interativos
- Filtros por período
- Export para Excel/CSV

### Produtos

```tsx
import { ProdutosList } from '@/components/produtos/list'

<ProdutosList />
```

**Features:**
- Listagem com paginação
- Busca e filtros
- CRUD completo
- Upload de imagens

### Vendas

```tsx
import { VendasForm } from '@/components/vendas/form'

<VendasForm />
```

**Features:**
- Carrinho de compras
- Cálculo automático
- Múltiplas formas de pagamento
- Impressão de recibo

---

## 🔐 Autenticação

### Login

```tsx
import { useAuth } from '@/lib/hooks/use-auth'

const { login, user, isAuthenticated } = useAuth()

await login({ email, password })
```

### Proteger Rotas

```tsx
import { ProtectedRoute } from '@/components/auth/protected-route'

<ProtectedRoute requiredPermission="vendas.create">
  <VendasPage />
</ProtectedRoute>
```

### Permissões

```tsx
import { usePermissions } from '@/lib/hooks/use-permissions'

const { hasPermission, hasRole } = usePermissions()

if (hasPermission('produtos.delete')) {
  // Mostrar botão deletar
}
```

---

## 📡 API Client

### Uso Básico

```tsx
import { apiClient } from '@/lib/api-client'

// GET
const produtos = await apiClient.get('/produtos')

// POST
const novoProduto = await apiClient.post('/produtos', {
  codigo: 'PROD-001',
  descricao: 'Produto Teste',
  preco_venda: 100.00
})

// PUT
await apiClient.put('/produtos/1', { preco_venda: 120.00 })

// DELETE
await apiClient.delete('/produtos/1')
```

### Com SWR (Recomendado)

```tsx
import { useProdutos } from '@/lib/hooks/use-produtos'

const { produtos, isLoading, error, mutate } = useProdutos()

// Revalidar
mutate()
```

---

## 🎨 Temas

### Tema Claro/Escuro

```tsx
import { ThemeProvider } from '@/components/theme-provider'
import { ThemeToggle } from '@/components/theme-toggle'

// Provider (layout.tsx)
<ThemeProvider>
  {children}
</ThemeProvider>

// Toggle
<ThemeToggle />
```

---

## 📊 Charts

### Gráfico de Vendas

```tsx
import { VendasChart } from '@/components/charts/vendas-chart'

<VendasChart
  data={vendasPorDia}
  period="month"
/>
```

**Tipos disponíveis:**
- LineChart - Vendas por dia
- BarChart - Produtos mais vendidos
- PieChart - Vendas por categoria
- AreaChart - Faturamento

---

## 📋 Formulários

### Com Validação

```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { produtoSchema } from '@/lib/validations/produto-schema'

const form = useForm({
  resolver: zodResolver(produtoSchema)
})

const onSubmit = async (data) => {
  await apiClient.post('/produtos', data)
}
```

---

## 🧩 Custom Hooks

### useProdutos

```tsx
const {
  produtos,      // Lista de produtos
  isLoading,     // Loading state
  error,         // Error state
  mutate,        // Revalidar
  createProduto, // Criar
  updateProduto, // Atualizar
  deleteProduto  // Deletar
} = useProdutos()
```

### useVendas

```tsx
const {
  vendas,
  createVenda,
  getVenda,
  updateVenda
} = useVendas()
```

### useExport

```tsx
const { exportToCsv, exportToExcel } = useExport()

await exportToExcel({
  formato: 'excel',
  tipo: 'vendas',
  filtros: { data_inicio, data_fim }
})
```

---

## 🔧 Utilitários

### Formatação

```tsx
import { formatCurrency, formatDate } from '@/lib/utils'

formatCurrency(12999.99)  // "R$ 12.999,99"
formatDate(new Date())     // "23/11/2025"
```

### Validações

```tsx
import { validateCPF, validateCNPJ } from '@/lib/utils'

validateCPF('123.456.789-00')  // true/false
validateCNPJ('12.345.678/0001-90')  // true/false
```

---

## 🎯 Performance

### Otimizações Implementadas

- ✅ Server Components (Next.js 14)
- ✅ Code Splitting automático
- ✅ Image Optimization (next/image)
- ✅ Font Optimization (next/font)
- ✅ SWR para cache de dados
- ✅ Lazy Loading de componentes
- ✅ Memoização (useMemo, useCallback)

### Lighthouse Score

- Performance: 95+
- Accessibility: 100
- Best Practices: 100
- SEO: 100

---

## 📱 Responsividade

**Breakpoints:**
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

Todos os componentes são totalmente responsivos.

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add: nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT.

---

## 👥 Autores

- **Janio Santos** - [GitHub](https://github.com/janiosantos)

---

## 🔗 Links

- **Backend:** [siscom-backend](https://github.com/janiosantos/siscom-backend)
- **Design System:** [Shadcn/ui](https://ui.shadcn.com)
- **Next.js Docs:** [nextjs.org/docs](https://nextjs.org/docs)

---

<div align="center">

**Desenvolvido com ❤️ usando Next.js**

</div>
