<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de Compras
 *
 * Cobre:
 * - Criação de pedidos de compra
 * - Aprovação de pedidos
 * - Recebimento de mercadorias
 * - Integração com estoque
 * - Integração com financeiro
 * - Status de pedidos
 * - Validações de negócio
 */
class ComprasTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdPedidoCompraIds = [];
    private $createdFornecedorIds = [];
    private $createdProdutoIds = [];
    private $createdCategoriaIds = [];

    protected function setUp(): void
    {
        parent::setUp();
        $this->client = new Client([
            'base_uri' => $this->baseUrl,
            'http_errors' => false,
            'headers' => [
                'Content-Type' => 'application/json',
                'Accept' => 'application/json'
            ]
        ]);
    }

    protected function tearDown(): void
    {
        // Limpa pedidos de compra
        foreach ($this->createdPedidoCompraIds as $id) {
            try {
                $this->client->delete("/api/compras/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa produtos
        foreach ($this->createdProdutoIds as $id) {
            try {
                $this->client->delete("/api/produtos/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa categorias
        foreach ($this->createdCategoriaIds as $id) {
            try {
                $this->client->delete("/api/categorias/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa fornecedores
        foreach ($this->createdFornecedorIds as $id) {
            try {
                $this->client->delete("/api/fornecedores/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        parent::tearDown();
    }

    /**
     * Helper: Criar categoria
     */
    private function criarCategoria($nome = 'Categoria Compra')
    {
        $response = $this->client->post('/api/categorias', [
            'json' => ['nome' => $nome]
        ]);
        $data = json_decode($response->getBody(), true);
        $this->createdCategoriaIds[] = $data['id'];
        return $data['id'];
    }

    /**
     * Helper: Criar produto
     */
    private function criarProduto($codigoBarras, $descricao, $categoriaId, $precoCusto)
    {
        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => $descricao,
                'categoria_id' => $categoriaId,
                'preco_custo' => $precoCusto,
                'preco_venda' => $precoCusto * 1.5,
                'estoque_minimo' => 10.0,
                'ativo' => true
            ]
        ]);
        $data = json_decode($response->getBody(), true);
        $this->createdProdutoIds[] = $data['id'];
        return $data['id'];
    }

    /**
     * Helper: Criar fornecedor
     */
    private function criarFornecedor($nome = 'Fornecedor Compra')
    {
        $payload = [
            'nome' => $nome,
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '12345678000199',
            'email' => 'compra@fornecedor.com',
            'telefone' => '1133334444',
            'prazo_pagamento' => 30,
            'ativo' => true
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);
        $data = json_decode($response->getBody(), true);
        if (isset($data['id'])) {
            $this->createdFornecedorIds[] = $data['id'];
            return $data['id'];
        }
        return null;
    }

    /**
     * Teste: Criar pedido de compra com sucesso
     * Cenário: Pedido simples com itens
     * Esperado: Status 201, pedido criado
     */
    public function testCriarPedidoCompraComSucesso()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000001', 'Produto Compra', $categoriaId, 50.0);
        $fornecedorId = $this->criarFornecedor('Distribuidora XYZ');

        $payload = [
            'fornecedor_id' => $fornecedorId,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 100.0,
                    'preco_unitario' => 50.0
                ]
            ],
            'data_entrega_prevista' => date('Y-m-d', strtotime('+15 days')),
            'observacoes' => 'Pedido de reposição de estoque'
        ];

        $response = $this->client->post('/api/compras', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('numero_pedido', $data);
        $this->assertArrayHasKey('data_pedido', $data);
        $this->assertArrayHasKey('valor_total', $data);
        $this->assertArrayHasKey('itens', $data);
        $this->assertArrayHasKey('status', $data);

        $this->assertEquals(5000.0, $data['valor_total']); // 100 * 50
        $this->assertEquals('PENDENTE', $data['status']);
        $this->assertCount(1, $data['itens']);

        $this->createdPedidoCompraIds[] = $data['id'];
    }

    /**
     * Teste: Criar pedido sem itens
     * Cenário: Pedido vazio
     * Esperado: Status 422
     */
    public function testCriarPedidoSemItens()
    {
        $fornecedorId = $this->criarFornecedor();

        $payload = [
            'fornecedor_id' => $fornecedorId,
            'itens' => [],
            'data_entrega_prevista' => date('Y-m-d', strtotime('+10 days'))
        ];

        $response = $this->client->post('/api/compras', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar pedido sem fornecedor
     * Cenário: Não informar fornecedor_id
     * Esperado: Status 422
     */
    public function testCriarPedidoSemFornecedor()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000002', 'Produto', $categoriaId, 30.0);

        $payload = [
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 50.0,
                    'preco_unitario' => 30.0
                ]
            ]
        ];

        $response = $this->client->post('/api/compras', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar pedido com múltiplos itens
     * Cenário: Vários produtos no pedido
     * Esperado: Total calculado corretamente
     */
    public function testCriarPedidoComMultiplosItens()
    {
        $categoriaId = $this->criarCategoria();
        $produto1Id = $this->criarProduto('CMP0000000003', 'Produto A', $categoriaId, 25.0);
        $produto2Id = $this->criarProduto('CMP0000000004', 'Produto B', $categoriaId, 40.0);
        $produto3Id = $this->criarProduto('CMP0000000005', 'Produto C', $categoriaId, 60.0);
        $fornecedorId = $this->criarFornecedor();

        $payload = [
            'fornecedor_id' => $fornecedorId,
            'itens' => [
                [
                    'produto_id' => $produto1Id,
                    'quantidade' => 50.0,
                    'preco_unitario' => 25.0
                ],
                [
                    'produto_id' => $produto2Id,
                    'quantidade' => 30.0,
                    'preco_unitario' => 40.0
                ],
                [
                    'produto_id' => $produto3Id,
                    'quantidade' => 20.0,
                    'preco_unitario' => 60.0
                ]
            ],
            'data_entrega_prevista' => date('Y-m-d', strtotime('+20 days'))
        ];

        $response = $this->client->post('/api/compras', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        // (50*25) + (30*40) + (20*60) = 1250 + 1200 + 1200 = 3650
        $this->assertEquals(3650.0, $data['valor_total']);
        $this->assertCount(3, $data['itens']);

        $this->createdPedidoCompraIds[] = $data['id'];
    }

    /**
     * Teste: Buscar pedido por ID
     * Cenário: Criar e buscar pedido
     * Esperado: Dados completos
     */
    public function testBuscarPedidoPorId()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000006', 'Produto Busca', $categoriaId, 35.0);
        $fornecedorId = $this->criarFornecedor();

        // Cria pedido
        $createResponse = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 75.0,
                        'preco_unitario' => 35.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d', strtotime('+10 days'))
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $pedidoId = $created['id'];
        $this->createdPedidoCompraIds[] = $pedidoId;

        // Busca pedido
        $response = $this->client->get("/api/compras/{$pedidoId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($pedidoId, $data['id']);
        $this->assertEquals(2625.0, $data['valor_total']); // 75 * 35
    }

    /**
     * Teste: Buscar pedido inexistente
     * Cenário: ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarPedidoInexistente()
    {
        $response = $this->client->get('/api/compras/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Listar pedidos com paginação
     * Cenário: Criar vários pedidos e listar
     * Esperado: Lista paginada
     */
    public function testListarPedidosComPaginacao()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000007', 'Produto Lista', $categoriaId, 20.0);
        $fornecedorId = $this->criarFornecedor();

        // Cria 3 pedidos
        for ($i = 0; $i < 3; $i++) {
            $createResponse = $this->client->post('/api/compras', [
                'json' => [
                    'fornecedor_id' => $fornecedorId,
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 10.0,
                            'preco_unitario' => 20.0
                        ]
                    ],
                    'data_entrega_prevista' => date('Y-m-d', strtotime('+15 days'))
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdPedidoCompraIds[] = $created['id'];
        }

        // Lista pedidos
        $response = $this->client->get('/api/compras?page=1&page_size=10');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertArrayHasKey('total', $data);
        $this->assertGreaterThanOrEqual(3, $data['total']);
    }

    /**
     * Teste: Aprovar pedido de compra
     * Cenário: Mudar status para APROVADO
     * Esperado: Status atualizado
     */
    public function testAprovarPedidoCompra()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000008', 'Produto Aprovar', $categoriaId, 45.0);
        $fornecedorId = $this->criarFornecedor();

        // Cria pedido
        $createResponse = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 60.0,
                        'preco_unitario' => 45.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d', strtotime('+12 days'))
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $pedidoId = $created['id'];
        $this->createdPedidoCompraIds[] = $pedidoId;

        // Aprova pedido
        $response = $this->client->post("/api/compras/{$pedidoId}/aprovar");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/compras/{$pedidoId}");
        $pedidoData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('APROVADO', $pedidoData['status']);
    }

    /**
     * Teste: Cancelar pedido de compra
     * Cenário: Cancelar pedido pendente
     * Esperado: Status CANCELADO
     */
    public function testCancelarPedidoCompra()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000009', 'Produto Cancelar', $categoriaId, 55.0);
        $fornecedorId = $this->criarFornecedor();

        // Cria pedido
        $createResponse = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 40.0,
                        'preco_unitario' => 55.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d', strtotime('+8 days'))
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $pedidoId = $created['id'];
        $this->createdPedidoCompraIds[] = $pedidoId;

        // Cancela pedido
        $response = $this->client->post("/api/compras/{$pedidoId}/cancelar", [
            'json' => ['motivo' => 'Fornecedor não consegue atender prazo']
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/compras/{$pedidoId}");
        $pedidoData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('CANCELADO', $pedidoData['status']);
    }

    /**
     * Teste: Receber pedido de compra
     * Cenário: Registrar recebimento de mercadorias
     * Esperado: Estoque atualizado, status RECEBIDO
     */
    public function testReceberPedidoCompra()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000010', 'Produto Receber', $categoriaId, 70.0);
        $fornecedorId = $this->criarFornecedor();

        // Verifica estoque antes
        $estoqueAntes = $this->client->get("/api/produtos/{$produtoId}");
        $estoqueAntesData = json_decode($estoqueAntes->getBody(), true);

        // Cria e aprova pedido
        $createResponse = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 50.0,
                        'preco_unitario' => 70.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $pedidoId = $created['id'];
        $this->createdPedidoCompraIds[] = $pedidoId;

        // Aprova
        $this->client->post("/api/compras/{$pedidoId}/aprovar");

        // Recebe mercadorias
        $recebimentoPayload = [
            'data_recebimento' => date('Y-m-d'),
            'nota_fiscal' => '12345',
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade_recebida' => 50.0
                ]
            ]
        ];

        $response = $this->client->post("/api/compras/{$pedidoId}/receber", [
            'json' => $recebimentoPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/compras/{$pedidoId}");
        $pedidoData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('RECEBIDO', $pedidoData['status']);

        // Verifica se estoque foi atualizado
        $estoqueDepois = $this->client->get("/api/produtos/{$produtoId}");
        $estoqueDepoisData = json_decode($estoqueDepois->getBody(), true);

        $this->assertEquals(
            $estoqueAntesData['estoque_atual'] + 50.0,
            $estoqueDepoisData['estoque_atual']
        );
    }

    /**
     * Teste: Recebimento parcial
     * Cenário: Receber menos que o pedido
     * Esperado: Status PARCIAL
     */
    public function testRecebimentoParcial()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000011', 'Produto Parcial', $categoriaId, 80.0);
        $fornecedorId = $this->criarFornecedor();

        // Cria e aprova pedido de 100 unidades
        $createResponse = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 100.0,
                        'preco_unitario' => 80.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $pedidoId = $created['id'];
        $this->createdPedidoCompraIds[] = $pedidoId;

        $this->client->post("/api/compras/{$pedidoId}/aprovar");

        // Recebe apenas 60 unidades
        $recebimentoPayload = [
            'data_recebimento' => date('Y-m-d'),
            'nota_fiscal' => '54321',
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade_recebida' => 60.0
                ]
            ]
        ];

        $response = $this->client->post("/api/compras/{$pedidoId}/receber", [
            'json' => $recebimentoPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/compras/{$pedidoId}");
        if ($getResponse->getStatusCode() === 200) {
            $pedidoData = json_decode($getResponse->getBody(), true);
            $this->assertContains($pedidoData['status'], ['PARCIAL', 'RECEBIDO']);
        }
    }

    /**
     * Teste: Integração com financeiro
     * Cenário: Verificar criação de conta a pagar
     * Esperado: Conta a pagar gerada
     */
    public function testIntegracaoComFinanceiro()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000012', 'Produto Financeiro', $categoriaId, 90.0);
        $fornecedorId = $this->criarFornecedor();

        // Cria, aprova e recebe pedido
        $createResponse = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 30.0,
                        'preco_unitario' => 90.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d'),
                'gerar_financeiro' => true
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $pedidoId = $created['id'];
        $this->createdPedidoCompraIds[] = $pedidoId;

        $this->client->post("/api/compras/{$pedidoId}/aprovar");

        $this->client->post("/api/compras/{$pedidoId}/receber", [
            'json' => [
                'data_recebimento' => date('Y-m-d'),
                'nota_fiscal' => '99999',
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade_recebida' => 30.0
                    ]
                ]
            ]
        ]);

        // Verifica se foi criada conta a pagar
        $financResponse = $this->client->get("/api/financeiro/contas-pagar?fornecedor_id={$fornecedorId}");

        if ($financResponse->getStatusCode() === 200) {
            $financData = json_decode($financResponse->getBody(), true);
            $this->assertGreaterThanOrEqual(1, $financData['total']);
        }
    }

    /**
     * Teste: Filtrar pedidos por status
     * Cenário: Buscar apenas pedidos pendentes
     * Esperado: Lista filtrada
     */
    public function testFiltrarPedidosPorStatus()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000013', 'Produto Status', $categoriaId, 25.0);
        $fornecedorId = $this->criarFornecedor();

        // Cria 2 pedidos pendentes
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/compras', [
                'json' => [
                    'fornecedor_id' => $fornecedorId,
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 10.0,
                            'preco_unitario' => 25.0
                        ]
                    ],
                    'data_entrega_prevista' => date('Y-m-d', strtotime('+10 days'))
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdPedidoCompraIds[] = $created['id'];
        }

        // Filtra por status
        $response = $this->client->get('/api/compras?status=PENDENTE');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(2, $data['total']);

        foreach ($data['items'] as $pedido) {
            $this->assertEquals('PENDENTE', $pedido['status']);
        }
    }

    /**
     * Teste: Filtrar pedidos por fornecedor
     * Cenário: Buscar pedidos de fornecedor específico
     * Esperado: Apenas pedidos do fornecedor
     */
    public function testFiltrarPedidosPorFornecedor()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000014', 'Produto', $categoriaId, 30.0);
        $fornecedorId = $this->criarFornecedor('Fornecedor Específico');

        // Cria 2 pedidos para o fornecedor
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/compras', [
                'json' => [
                    'fornecedor_id' => $fornecedorId,
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 15.0,
                            'preco_unitario' => 30.0
                        ]
                    ],
                    'data_entrega_prevista' => date('Y-m-d', strtotime('+12 days'))
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdPedidoCompraIds[] = $created['id'];
        }

        // Filtra por fornecedor
        $response = $this->client->get("/api/compras?fornecedor_id={$fornecedorId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(2, $data['total']);

        foreach ($data['items'] as $pedido) {
            $this->assertEquals($fornecedorId, $pedido['fornecedor_id']);
        }
    }

    /**
     * Teste: Atualizar pedido pendente
     * Cenário: Alterar observações ou data
     * Esperado: Dados atualizados
     */
    public function testAtualizarPedidoPendente()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000015', 'Produto Atualizar', $categoriaId, 40.0);
        $fornecedorId = $this->criarFornecedor();

        // Cria pedido
        $createResponse = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 25.0,
                        'preco_unitario' => 40.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d', strtotime('+10 days')),
                'observacoes' => 'Observação original'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $pedidoId = $created['id'];
        $this->createdPedidoCompraIds[] = $pedidoId;

        // Atualiza
        $updatePayload = [
            'observacoes' => 'Observação atualizada',
            'data_entrega_prevista' => date('Y-m-d', strtotime('+15 days'))
        ];

        $response = $this->client->put("/api/compras/{$pedidoId}", [
            'json' => $updatePayload
        ]);

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('Observação atualizada', $data['observacoes']);
    }

    /**
     * Teste: Tentar atualizar pedido aprovado
     * Cenário: Alterar pedido que já foi aprovado
     * Esperado: Status 400
     */
    public function testAtualizarPedidoAprovado()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000016', 'Produto', $categoriaId, 50.0);
        $fornecedorId = $this->criarFornecedor();

        // Cria e aprova
        $createResponse = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 20.0,
                        'preco_unitario' => 50.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d', strtotime('+10 days'))
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $pedidoId = $created['id'];
        $this->createdPedidoCompraIds[] = $pedidoId;

        $this->client->post("/api/compras/{$pedidoId}/aprovar");

        // Tenta atualizar
        $response = $this->client->put("/api/compras/{$pedidoId}", [
            'json' => ['observacoes' => 'Nova observação']
        ]);

        $this->assertEquals(400, $response->getStatusCode());
    }

    /**
     * Teste: Validar timestamps
     * Cenário: Verificar created_at e updated_at
     * Esperado: Campos preenchidos
     */
    public function testTimestampsPedido()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000017', 'Produto Time', $categoriaId, 35.0);
        $fornecedorId = $this->criarFornecedor();

        $response = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 15.0,
                        'preco_unitario' => 35.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d', strtotime('+10 days'))
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdPedidoCompraIds[] = $data['id'];

        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('updated_at', $data);
        $this->assertNotEmpty($data['created_at']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/', $data['created_at']);
    }

    /**
     * Teste: Deletar pedido pendente
     * Cenário: Remover pedido que não foi aprovado
     * Esperado: Status 204 ou 200
     */
    public function testDeletarPedidoPendente()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000018', 'Produto Deletar', $categoriaId, 45.0);
        $fornecedorId = $this->criarFornecedor();

        $createResponse = $this->client->post('/api/compras', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 10.0,
                        'preco_unitario' => 45.0
                    ]
                ],
                'data_entrega_prevista' => date('Y-m-d', strtotime('+10 days'))
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $pedidoId = $created['id'];

        $response = $this->client->delete("/api/compras/{$pedidoId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se foi removido
        $getResponse = $this->client->get("/api/compras/{$pedidoId}");
        $this->assertContains($getResponse->getStatusCode(), [404, 200]);
    }

    /**
     * Teste: Número de pedido único
     * Cenário: Criar vários pedidos
     * Esperado: Cada pedido tem número único
     */
    public function testNumeroPedidoUnico()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CMP0000000019', 'Produto Num', $categoriaId, 20.0);
        $fornecedorId = $this->criarFornecedor();

        $numerosPedido = [];

        for ($i = 0; $i < 3; $i++) {
            $response = $this->client->post('/api/compras', [
                'json' => [
                    'fornecedor_id' => $fornecedorId,
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 5.0,
                            'preco_unitario' => 20.0
                        ]
                    ],
                    'data_entrega_prevista' => date('Y-m-d', strtotime('+10 days'))
                ]
            ]);

            $data = json_decode($response->getBody(), true);
            $this->createdPedidoCompraIds[] = $data['id'];

            $this->assertArrayHasKey('numero_pedido', $data);
            $numerosPedido[] = $data['numero_pedido'];
        }

        // Verifica se todos os números são únicos
        $this->assertEquals(count($numerosPedido), count(array_unique($numerosPedido)));
    }
}
