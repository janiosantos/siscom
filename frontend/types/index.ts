// ========== Auth Types ==========

export interface User {
  id: number
  username: string
  email: string
  nome_completo: string
  ativo: boolean
  role_id: number
  role: Role
  created_at: string
  updated_at: string
}

export interface Role {
  id: number
  name: string
  description: string
  permissions: Permission[]
}

export interface Permission {
  id: number
  name: string
  description: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// ========== Produto Types ==========

export interface Produto {
  id: number
  codigo_barras: string
  descricao: string
  categoria_id: number
  categoria?: Categoria
  preco_custo: number
  preco_venda: number
  estoque_atual: number
  estoque_minimo: number
  unidade: string
  ncm?: string
  controla_lote: boolean
  controla_serie: boolean
  ativo: boolean
  created_at: string
  updated_at: string
}

export interface ProdutoCreate {
  codigo_barras: string
  descricao: string
  categoria_id: number
  preco_custo: number
  preco_venda: number
  estoque_atual?: number
  estoque_minimo?: number
  unidade?: string
  ncm?: string
  ativo?: boolean
}

export interface ProdutoUpdate extends Partial<ProdutoCreate> {}

// ========== Cliente Types ==========

export interface Cliente {
  id: number
  nome: string
  razao_social?: string
  cpf_cnpj: string
  email?: string
  telefone?: string
  endereco?: string
  numero?: string
  complemento?: string
  bairro?: string
  cidade?: string
  estado?: string
  cep?: string
  ativo: boolean
  created_at: string
  updated_at: string
}

export interface ClienteCreate {
  nome: string
  razao_social?: string
  cpf_cnpj: string
  email?: string
  telefone?: string
  endereco?: string
  numero?: string
  complemento?: string
  bairro?: string
  cidade?: string
  estado?: string
  cep?: string
  ativo?: boolean
}

export interface ClienteUpdate extends Partial<ClienteCreate> {}

// ========== Categoria Types ==========

export interface Categoria {
  id: number
  nome: string
  descricao?: string
  ativa: boolean
  created_at: string
  updated_at: string
}

// ========== Venda Types ==========

export enum StatusVenda {
  PENDENTE = "PENDENTE",
  FINALIZADA = "FINALIZADA",
  CANCELADA = "CANCELADA",
}

export interface ItemVenda {
  id: number
  venda_id: number
  produto_id: number
  produto?: Produto
  quantidade: number
  preco_unitario: number
  desconto_item: number
  subtotal_item: number
  total_item: number
  created_at: string
}

export interface Venda {
  id: number
  cliente_id?: number
  cliente?: { id: number; nome: string }
  vendedor_id: number
  data_venda: string
  subtotal: number
  desconto: number
  valor_total: number
  total_produtos: number
  total_final: number
  forma_pagamento: string
  status: StatusVenda
  observacoes?: string
  itens: ItemVenda[]
  created_at: string
  updated_at: string
}

export interface VendaCreate {
  cliente_id?: number
  vendedor_id: number
  forma_pagamento: string
  desconto?: number
  observacoes?: string
  itens: ItemVendaCreate[]
}

export interface VendaUpdate extends Partial<VendaCreate> {}

export interface ItemVendaCreate {
  produto_id: number
  quantidade: number
  preco_unitario: number
  desconto_item?: number
}

export type VendaItemCreate = ItemVendaCreate

// ========== Estoque Types ==========

export enum TipoMovimentacao {
  ENTRADA = "ENTRADA",
  SAIDA = "SAIDA",
  AJUSTE = "AJUSTE",
  TRANSFERENCIA = "TRANSFERENCIA",
}

export interface MovimentacaoEstoque {
  id: number
  produto_id: number
  produto?: Produto
  tipo: TipoMovimentacao
  quantidade: number
  custo_unitario?: number
  valor_total?: number
  observacao?: string
  usuario_id: number
  data_movimentacao: string
  created_at: string
}

export interface MovimentacaoEstoqueCreate {
  produto_id: number
  tipo: TipoMovimentacao
  quantidade: number
  custo_unitario?: number
  valor_total?: number
  observacao?: string
}

// ========== Financeiro Types ==========

export enum StatusFinanceiro {
  PENDENTE = "PENDENTE",
  PAGO = "PAGO",
  CANCELADO = "CANCELADO",
  VENCIDO = "VENCIDO",
}

export interface ContaPagar {
  id: number
  fornecedor_id: number
  descricao: string
  valor_original: number
  valor_pago: number
  valor?: number
  venda_id?: number
  data_emissao: string
  data_vencimento: string
  data_pagamento?: string
  status: StatusFinanceiro
  documento?: string
  categoria_financeira?: string
  observacoes?: string
  created_at: string
  updated_at: string
}

export interface ContaPagarCreate {
  fornecedor_id: number
  descricao: string
  valor_original: number
  data_emissao: string
  data_vencimento: string
  documento?: string
  categoria_financeira?: string
  observacoes?: string
}

export interface ContaReceber {
  id: number
  cliente_id?: number
  descricao: string
  valor_original: number
  valor_recebido: number
  valor?: number
  venda_id?: number
  data_emissao: string
  data_vencimento: string
  data_recebimento?: string
  data_pagamento?: string
  status: StatusFinanceiro
  documento?: string
  categoria_financeira?: string
  observacoes?: string
  created_at: string
  updated_at: string
}

export interface ContaReceberCreate {
  cliente_id?: number
  descricao: string
  valor_original: number
  data_emissao: string
  data_vencimento: string
  documento?: string
  categoria_financeira?: string
  observacoes?: string
}

// ========== Pagination Types ==========

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

// ========== API Error Types ==========

export interface ApiError {
  detail: string | ValidationError[]
}

export interface ValidationError {
  loc: (string | number)[]
  msg: string
  type: string
}
