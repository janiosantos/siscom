# Frontend - ERP Materiais de Construção

Frontend moderno e interativo para o sistema ERP, construído com as melhores tecnologias do mercado.

## 🚀 Stack Tecnológica

- **Framework**: Next.js 14 (App Router)
- **Linguagem**: TypeScript
- **Estilização**: Tailwind CSS
- **Componentes**: shadcn/ui
- **Data Fetching**: TanStack React Query
- **State Management**: Zustand
- **Formulários**: React Hook Form + Zod
- **HTTP Client**: Axios
- **Ícones**: Lucide React
- **Notificações**: Sonner
- **Gráficos**: Recharts

## 📁 Estrutura do Projeto

```
frontend/
├── app/                      # App Router (Next.js 14)
│   ├── (auth)/              # Rotas de autenticação
│   │   └── login/
│   ├── (dashboard)/         # Rotas do dashboard
│   │   ├── vendas/
│   │   ├── produtos/
│   │   ├── estoque/
│   │   └── financeiro/
│   ├── layout.tsx           # Layout raiz
│   ├── page.tsx             # Página inicial
│   └── globals.css          # Estilos globais
│
├── components/              # Componentes reutilizáveis
│   ├── ui/                  # Componentes UI (shadcn)
│   ├── forms/               # Componentes de formulário
│   ├── tables/              # Componentes de tabela
│   └── layouts/             # Layouts compartilhados
│
├── lib/                     # Bibliotecas e utilitários
│   ├── api/                 # Cliente API e services
│   ├── hooks/               # Custom React Hooks
│   ├── store/               # State management (Zustand)
│   └── utils/               # Funções utilitárias
│
├── types/                   # TypeScript types/interfaces
│
└── public/                  # Arquivos estáticos

```

## 🎨 Características

### ✅ Implementado

- ✅ Configuração Next.js 14 com App Router
- ✅ TypeScript configurado
- ✅ Tailwind CSS + shadcn/ui
- ✅ Sistema de autenticação (login)
- ✅ Cliente API com interceptors
- ✅ Componentes UI básicos (Button, Card, Input, Label)
- ✅ Página de login responsiva
- ✅ Tratamento de erros e notificações
- ✅ Types TypeScript para todas as entidades

### 🚧 Em Desenvolvimento

- Layout de dashboard com sidebar
- Páginas de módulos (Vendas, Produtos, Estoque, Financeiro)
- Tabelas com paginação e filtros
- Formulários de CRUD completos
- Dashboards com gráficos e KPIs
- Modo escuro (dark mode)
- Responsividade completa

## 🔧 Instalação

### Pré-requisitos

- Node.js >= 18.0.0
- npm >= 9.0.0
- Backend FastAPI rodando em `http://localhost:8000`

### Passo a Passo

1. **Instalar dependências**

```bash
cd frontend
npm install
```

2. **Configurar variáveis de ambiente**

```bash
cp .env.example .env.local
```

Edite `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

3. **Executar em modo de desenvolvimento**

```bash
npm run dev
```

O frontend estará disponível em: `http://localhost:3000`

4. **Build para produção**

```bash
npm run build
npm start
```

## 🔐 Autenticação

O sistema usa JWT (JSON Web Tokens) para autenticação:

- **Access Token**: Armazenado em `localStorage`
- **Refresh Token**: Armazenado em `localStorage`
- **Auto-refresh**: Renovação automática do token quando expira
- **Proteção de rotas**: Middleware de autenticação

### Credenciais de Teste

```
Usuário: admin
Senha: senha123
```

## 📡 Integração com API

### Cliente API

O cliente API (`lib/api/client.ts`) fornece:

- Interceptors para autenticação automática
- Tratamento de erros centralizado
- Renovação automática de tokens
- Tipagem TypeScript completa

### Exemplo de Uso

```typescript
import { apiClient } from "@/lib/api/client"
import { Produto } from "@/types"

// GET request
const produtos = await apiClient.get<Produto[]>("/produtos")

// POST request
const novoProduto = await apiClient.post<Produto>("/produtos", {
  codigo_barras: "7891234567890",
  descricao: "Cimento CP-II 50kg",
  categoria_id: 1,
  preco_custo: 25.50,
  preco_venda: 32.90,
})
```

## 🎯 Componentes Principais

### Button

```tsx
import { Button } from "@/components/ui/button"

<Button variant="default" size="lg">
  Clique aqui
</Button>
```

### Card

```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

<Card>
  <CardHeader>
    <CardTitle>Título</CardTitle>
  </CardHeader>
  <CardContent>
    Conteúdo
  </CardContent>
</Card>
```

### Input

```tsx
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

<div>
  <Label htmlFor="email">Email</Label>
  <Input id="email" type="email" placeholder="email@exemplo.com" />
</div>
```

## 🌈 Temas e Cores

O sistema usa o Tailwind CSS com variáveis CSS para suportar temas:

- **Light Mode**: Fundo claro, texto escuro
- **Dark Mode**: Fundo escuro, texto claro (em desenvolvimento)

Cores principais:
- Primary: Azul (#3B82F6)
- Secondary: Cinza
- Destructive: Vermelho (erros e exclusões)
- Muted: Cinza claro (elementos desabilitados)

## 📝 Scripts Disponíveis

```bash
# Desenvolvimento
npm run dev          # Inicia servidor de desenvolvimento

# Build
npm run build        # Cria build de produção
npm start            # Inicia servidor de produção

# Qualidade de Código
npm run lint         # Executa ESLint
npm run type-check   # Verifica tipos TypeScript
```

## 🔄 Próximas Implementações

1. **Dashboard Principal**
   - KPIs de vendas, estoque e financeiro
   - Gráficos interativos (Recharts)
   - Alertas e notificações

2. **Módulo de Vendas**
   - Listagem com filtros e paginação
   - Formulário de nova venda
   - Detalhes da venda
   - Cancelamento e finalização

3. **Módulo de Produtos**
   - CRUD completo
   - Upload de imagens
   - Controle de estoque
   - Alertas de estoque mínimo

4. **Módulo de Estoque**
   - Movimentações
   - Inventário
   - Relatórios

5. **Módulo Financeiro**
   - Contas a pagar/receber
   - Fluxo de caixa
   - Relatórios financeiros

## 🤝 Contribuindo

1. Clone o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.

## 📞 Suporte

Para dúvidas ou sugestões, entre em contato:
- Email: suporte@erp.com
- GitHub: [Issues](https://github.com/seu-usuario/siscom/issues)

---

**Desenvolvido com ❤️ usando Next.js 14 + TypeScript + Tailwind CSS**
