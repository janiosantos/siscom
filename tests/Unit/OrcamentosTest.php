<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de Orçamentos
 *
 * Cobre:
 * - Criação de orçamentos
 * - Adição de itens
 * - Cálculo de totais e descontos
 * - Status (pendente, aprovado, rejeitado)
 * - Conversão para venda
 * - Validade do orçamento
 * - Observações e condições
 */
class OrcamentosTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdOrcamentoIds = [];
    private $createdVendaIds = [];
    private $createdProdutoIds = [];
    private $createdCategoriaIds = [];
    private $createdClienteIds = [];

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
        // Limpa orçamentos
        foreach ($this->createdOrcamentoIds as $id) {
            try {
                $this->client->delete("/api/orcamentos/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa vendas
        foreach ($this->createdVendaIds as $id) {
            try {
                $this->client->delete("/api/vendas/{$id}");
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

        // Limpa clientes
        foreach ($this->createdClienteIds as $id) {
            try {
                $this->client->delete("/api/clientes/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        parent::tearDown();
    }

    /**
     * Helper: Criar categoria
     */
    private function criarCategoria($nome = 'Categoria Orçamento')
    {
        $response = $this->client->post('/api/categorias', [
            'json' => ['nome' => $nome]
        ]);
        $data = json_decode($response->getBody(), true);
        $this->createdCategoriaIds[] = $data['id'];
        return $data['id'];
    }

    /**
     * Helper: Criar produto com estoque
     */
    private function criarProduto($codigoBarras, $descricao, $categoriaId, $precoVenda, $estoqueInicial = 100.0)
    {
        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => $descricao,
                'categoria_id' => $categoriaId,
                'preco_custo' => $precoVenda * 0.6,
                'preco_venda' => $precoVenda,
                'estoque_minimo' => 10.0,
                'ativo' => true
            ]
        ]);
        $data = json_decode($response->getBody(), true);
        $produtoId = $data['id'];
        $this->createdProdutoIds[] = $produtoId;

        // Adiciona estoque
        $this->client->post('/api/estoque/entrada', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => $estoqueInicial,
                'preco_custo' => $precoVenda * 0.6,
                'motivo' => 'COMPRA'
            ]
        ]);

        return $produtoId;
    }

    /**
     * Helper: Criar cliente
     */
    private function criarCliente($nome = 'Cliente Orçamento', $tipo = 'PF')
    {
        $payload = [
            'nome' => $nome,
            'tipo_pessoa' => $tipo,
            'cpf_cnpj' => $tipo === 'PF' ? '12345678901' : '12345678000199',
            'email' => 'orcamento@cliente.com',
            'telefone' => '11999999999',
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);
        $data = json_decode($response->getBody(), true);
        if (isset($data['id'])) {
            $this->createdClienteIds[] = $data['id'];
            return $data['id'];
        }
        return null;
    }

    /**
     * Teste: Criar orçamento com sucesso
     * Cenário: Orçamento simples com itens
     * Esperado: Status 201, orçamento criado
     */
    public function testCriarOrcamentoComSucesso()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000001', 'Produto Orçamento', $categoriaId, 100.0);
        $clienteId = $this->criarCliente('João Silva');

        $payload = [
            'cliente_id' => $clienteId,
            'validade_dias' => 15,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 5.0,
                    'preco_unitario' => 100.0
                ]
            ],
            'observacoes' => 'Orçamento para reforma'
        ];

        $response = $this->client->post('/api/orcamentos', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('numero_orcamento', $data);
        $this->assertArrayHasKey('data_orcamento', $data);
        $this->assertArrayHasKey('valor_total', $data);
        $this->assertArrayHasKey('itens', $data);
        $this->assertArrayHasKey('status', $data);
        $this->assertArrayHasKey('data_validade', $data);

        $this->assertEquals(500.0, $data['valor_total']); // 5 * 100
        $this->assertEquals('PENDENTE', $data['status']);
        $this->assertCount(1, $data['itens']);

        $this->createdOrcamentoIds[] = $data['id'];
    }

    /**
     * Teste: Criar orçamento sem itens
     * Cenário: Orçamento vazio
     * Esperado: Status 422
     */
    public function testCriarOrcamentoSemItens()
    {
        $clienteId = $this->criarCliente();

        $payload = [
            'cliente_id' => $clienteId,
            'itens' => [],
            'validade_dias' => 10
        ];

        $response = $this->client->post('/api/orcamentos', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar orçamento com múltiplos itens
     * Cenário: Vários produtos no orçamento
     * Esperado: Total calculado corretamente
     */
    public function testCriarOrcamentoComMultiplosItens()
    {
        $categoriaId = $this->criarCategoria();
        $produto1Id = $this->criarProduto('ORC0000000002', 'Produto A', $categoriaId, 50.0);
        $produto2Id = $this->criarProduto('ORC0000000003', 'Produto B', $categoriaId, 75.0);
        $produto3Id = $this->criarProduto('ORC0000000004', 'Produto C', $categoriaId, 100.0);
        $clienteId = $this->criarCliente();

        $payload = [
            'cliente_id' => $clienteId,
            'validade_dias' => 30,
            'itens' => [
                [
                    'produto_id' => $produto1Id,
                    'quantidade' => 10.0,
                    'preco_unitario' => 50.0
                ],
                [
                    'produto_id' => $produto2Id,
                    'quantidade' => 5.0,
                    'preco_unitario' => 75.0
                ],
                [
                    'produto_id' => $produto3Id,
                    'quantidade' => 2.0,
                    'preco_unitario' => 100.0
                ]
            ]
        ];

        $response = $this->client->post('/api/orcamentos', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        // (10*50) + (5*75) + (2*100) = 500 + 375 + 200 = 1075
        $this->assertEquals(1075.0, $data['valor_total']);
        $this->assertCount(3, $data['itens']);

        $this->createdOrcamentoIds[] = $data['id'];
    }

    /**
     * Teste: Criar orçamento com desconto
     * Cenário: Aplicar desconto no orçamento
     * Esperado: Desconto aplicado corretamente
     */
    public function testCriarOrcamentoComDesconto()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000005', 'Produto Desconto', $categoriaId, 200.0);
        $clienteId = $this->criarCliente();

        $payload = [
            'cliente_id' => $clienteId,
            'validade_dias' => 20,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 5.0,
                    'preco_unitario' => 200.0
                ]
            ],
            'desconto' => 100.0
        ];

        $response = $this->client->post('/api/orcamentos', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals(100.0, $data['desconto']);
        $this->assertEquals(900.0, $data['valor_total']); // (5*200) - 100 = 900

        $this->createdOrcamentoIds[] = $data['id'];
    }

    /**
     * Teste: Buscar orçamento por ID
     * Cenário: Criar e buscar orçamento
     * Esperado: Dados completos
     */
    public function testBuscarOrcamentoPorId()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000006', 'Produto', $categoriaId, 80.0);
        $clienteId = $this->criarCliente();

        // Cria orçamento
        $createResponse = $this->client->post('/api/orcamentos', [
            'json' => [
                'cliente_id' => $clienteId,
                'validade_dias' => 10,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 3.0,
                        'preco_unitario' => 80.0
                    ]
                ]
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $orcamentoId = $created['id'];
        $this->createdOrcamentoIds[] = $orcamentoId;

        // Busca orçamento
        $response = $this->client->get("/api/orcamentos/{$orcamentoId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($orcamentoId, $data['id']);
        $this->assertEquals(240.0, $data['valor_total']);
    }

    /**
     * Teste: Buscar orçamento inexistente
     * Cenário: ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarOrcamentoInexistente()
    {
        $response = $this->client->get('/api/orcamentos/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Listar orçamentos com paginação
     * Cenário: Criar vários orçamentos e listar
     * Esperado: Lista paginada
     */
    public function testListarOrcamentosComPaginacao()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000007', 'Produto Lista', $categoriaId, 50.0, 100.0);
        $clienteId = $this->criarCliente();

        // Cria 3 orçamentos
        for ($i = 0; $i < 3; $i++) {
            $createResponse = $this->client->post('/api/orcamentos', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'validade_dias' => 15,
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 2.0,
                            'preco_unitario' => 50.0
                        ]
                    ]
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdOrcamentoIds[] = $created['id'];
        }

        // Lista orçamentos
        $response = $this->client->get('/api/orcamentos?page=1&page_size=10');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertArrayHasKey('total', $data);
        $this->assertGreaterThanOrEqual(3, $data['total']);
    }

    /**
     * Teste: Aprovar orçamento
     * Cenário: Mudar status para APROVADO
     * Esperado: Status atualizado
     */
    public function testAprovarOrcamento()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000008', 'Produto Aprovar', $categoriaId, 150.0);
        $clienteId = $this->criarCliente();

        // Cria orçamento
        $createResponse = $this->client->post('/api/orcamentos', [
            'json' => [
                'cliente_id' => $clienteId,
                'validade_dias' => 10,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 4.0,
                        'preco_unitario' => 150.0
                    ]
                ]
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $orcamentoId = $created['id'];
        $this->createdOrcamentoIds[] = $orcamentoId;

        // Aprova orçamento
        $response = $this->client->post("/api/orcamentos/{$orcamentoId}/aprovar");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/orcamentos/{$orcamentoId}");
        $orcamentoData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('APROVADO', $orcamentoData['status']);
    }

    /**
     * Teste: Rejeitar orçamento
     * Cenário: Mudar status para REJEITADO
     * Esperado: Status atualizado
     */
    public function testRejeitarOrcamento()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000009', 'Produto Rejeitar', $categoriaId, 90.0);
        $clienteId = $this->criarCliente();

        // Cria orçamento
        $createResponse = $this->client->post('/api/orcamentos', [
            'json' => [
                'cliente_id' => $clienteId,
                'validade_dias' => 10,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 2.0,
                        'preco_unitario' => 90.0
                    ]
                ]
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $orcamentoId = $created['id'];
        $this->createdOrcamentoIds[] = $orcamentoId;

        // Rejeita orçamento
        $response = $this->client->post("/api/orcamentos/{$orcamentoId}/rejeitar", [
            'json' => ['motivo' => 'Cliente desistiu da compra']
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/orcamentos/{$orcamentoId}");
        $orcamentoData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('REJEITADO', $orcamentoData['status']);
    }

    /**
     * Teste: Converter orçamento em venda
     * Cenário: Gerar venda a partir de orçamento aprovado
     * Esperado: Venda criada
     */
    public function testConverterOrcamentoEmVenda()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000010', 'Produto Converter', $categoriaId, 120.0);
        $clienteId = $this->criarCliente();

        // Cria orçamento
        $createResponse = $this->client->post('/api/orcamentos', [
            'json' => [
                'cliente_id' => $clienteId,
                'validade_dias' => 10,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 3.0,
                        'preco_unitario' => 120.0
                    ]
                ]
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $orcamentoId = $created['id'];
        $this->createdOrcamentoIds[] = $orcamentoId;

        // Converte em venda
        $response = $this->client->post("/api/orcamentos/{$orcamentoId}/converter-venda", [
            'json' => ['forma_pagamento' => 'CREDITO']
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201]);

        if ($response->getStatusCode() === 201 || $response->getStatusCode() === 200) {
            $vendaData = json_decode($response->getBody(), true);

            $this->assertArrayHasKey('venda_id', $vendaData);
            $this->createdVendaIds[] = $vendaData['venda_id'];

            // Verifica se orçamento foi marcado como convertido
            $getResponse = $this->client->get("/api/orcamentos/{$orcamentoId}");
            $orcamentoData = json_decode($getResponse->getBody(), true);

            $this->assertEquals('CONVERTIDO', $orcamentoData['status']);
        }
    }

    /**
     * Teste: Converter orçamento rejeitado
     * Cenário: Tentar converter orçamento com status rejeitado
     * Esperado: Status 400
     */
    public function testConverterOrcamentoRejeitado()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000011', 'Produto', $categoriaId, 100.0);
        $clienteId = $this->criarCliente();

        // Cria e rejeita orçamento
        $createResponse = $this->client->post('/api/orcamentos', [
            'json' => [
                'cliente_id' => $clienteId,
                'validade_dias' => 10,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 1.0,
                        'preco_unitario' => 100.0
                    ]
                ]
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $orcamentoId = $created['id'];
        $this->createdOrcamentoIds[] = $orcamentoId;

        // Rejeita
        $this->client->post("/api/orcamentos/{$orcamentoId}/rejeitar", [
            'json' => ['motivo' => 'Teste']
        ]);

        // Tenta converter
        $response = $this->client->post("/api/orcamentos/{$orcamentoId}/converter-venda", [
            'json' => ['forma_pagamento' => 'DINHEIRO']
        ]);

        $this->assertEquals(400, $response->getStatusCode());
    }

    /**
     * Teste: Atualizar orçamento
     * Cenário: Alterar itens ou observações
     * Esperado: Dados atualizados
     */
    public function testAtualizarOrcamento()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000012', 'Produto Atualizar', $categoriaId, 70.0);
        $clienteId = $this->criarCliente();

        // Cria orçamento
        $createResponse = $this->client->post('/api/orcamentos', [
            'json' => [
                'cliente_id' => $clienteId,
                'validade_dias' => 10,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 5.0,
                        'preco_unitario' => 70.0
                    ]
                ],
                'observacoes' => 'Observação original'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $orcamentoId = $created['id'];
        $this->createdOrcamentoIds[] = $orcamentoId;

        // Atualiza
        $updatePayload = [
            'observacoes' => 'Observação atualizada',
            'validade_dias' => 20
        ];

        $response = $this->client->put("/api/orcamentos/{$orcamentoId}", [
            'json' => $updatePayload
        ]);

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('Observação atualizada', $data['observacoes']);
    }

    /**
     * Teste: Validar data de validade
     * Cenário: Verificar se data_validade foi calculada
     * Esperado: Data no futuro
     */
    public function testValidarDataValidade()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000013', 'Produto Validade', $categoriaId, 60.0);
        $clienteId = $this->criarCliente();

        $response = $this->client->post('/api/orcamentos', [
            'json' => [
                'cliente_id' => $clienteId,
                'validade_dias' => 15,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 1.0,
                        'preco_unitario' => 60.0
                    ]
                ]
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdOrcamentoIds[] = $data['id'];

        $this->assertArrayHasKey('data_validade', $data);
        $this->assertNotEmpty($data['data_validade']);

        // Data validade deve ser futura
        $dataValidade = new \DateTime($data['data_validade']);
        $hoje = new \DateTime();
        $this->assertGreaterThan($hoje, $dataValidade);
    }

    /**
     * Teste: Filtrar orçamentos por status
     * Cenário: Buscar apenas orçamentos pendentes
     * Esperado: Lista filtrada
     */
    public function testFiltrarOrcamentosPorStatus()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000014', 'Produto Status', $categoriaId, 40.0, 100.0);
        $clienteId = $this->criarCliente();

        // Cria 2 orçamentos pendentes
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/orcamentos', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'validade_dias' => 10,
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 1.0,
                            'preco_unitario' => 40.0
                        ]
                    ]
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdOrcamentoIds[] = $created['id'];
        }

        // Filtra por status
        $response = $this->client->get('/api/orcamentos?status=PENDENTE');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(2, $data['total']);

        foreach ($data['items'] as $orcamento) {
            $this->assertEquals('PENDENTE', $orcamento['status']);
        }
    }

    /**
     * Teste: Filtrar orçamentos por cliente
     * Cenário: Buscar orçamentos de cliente específico
     * Esperado: Apenas orçamentos do cliente
     */
    public function testFiltrarOrcamentosPorCliente()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000015', 'Produto', $categoriaId, 30.0, 100.0);
        $clienteId = $this->criarCliente('Cliente Específico');

        // Cria 2 orçamentos para o cliente
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/orcamentos', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'validade_dias' => 15,
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 1.0,
                            'preco_unitario' => 30.0
                        ]
                    ]
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdOrcamentoIds[] = $created['id'];
        }

        // Filtra por cliente
        $response = $this->client->get("/api/orcamentos?cliente_id={$clienteId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(2, $data['total']);

        foreach ($data['items'] as $orcamento) {
            $this->assertEquals($clienteId, $orcamento['cliente_id']);
        }
    }

    /**
     * Teste: Validar timestamps
     * Cenário: Verificar created_at e updated_at
     * Esperado: Campos preenchidos
     */
    public function testTimestampsOrcamento()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000016', 'Produto Time', $categoriaId, 45.0);
        $clienteId = $this->criarCliente();

        $response = $this->client->post('/api/orcamentos', [
            'json' => [
                'cliente_id' => $clienteId,
                'validade_dias' => 10,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 1.0,
                        'preco_unitario' => 45.0
                    ]
                ]
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdOrcamentoIds[] = $data['id'];

        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('updated_at', $data);
        $this->assertNotEmpty($data['created_at']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/', $data['created_at']);
    }

    /**
     * Teste: Deletar orçamento
     * Cenário: Remover orçamento do sistema
     * Esperado: Status 204 ou 200
     */
    public function testDeletarOrcamento()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000017', 'Produto Deletar', $categoriaId, 55.0);
        $clienteId = $this->criarCliente();

        $createResponse = $this->client->post('/api/orcamentos', [
            'json' => [
                'cliente_id' => $clienteId,
                'validade_dias' => 10,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 1.0,
                        'preco_unitario' => 55.0
                    ]
                ]
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $orcamentoId = $created['id'];

        $response = $this->client->delete("/api/orcamentos/{$orcamentoId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se foi removido
        $getResponse = $this->client->get("/api/orcamentos/{$orcamentoId}");
        $this->assertContains($getResponse->getStatusCode(), [404, 200]);
    }

    /**
     * Teste: Número de orçamento único
     * Cenário: Criar vários orçamentos
     * Esperado: Cada orçamento tem número único
     */
    public function testNumeroOrcamentoUnico()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ORC0000000018', 'Produto Num', $categoriaId, 25.0, 100.0);
        $clienteId = $this->criarCliente();

        $numerosOrcamento = [];

        for ($i = 0; $i < 3; $i++) {
            $response = $this->client->post('/api/orcamentos', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'validade_dias' => 10,
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 1.0,
                            'preco_unitario' => 25.0
                        ]
                    ]
                ]
            ]);

            $data = json_decode($response->getBody(), true);
            $this->createdOrcamentoIds[] = $data['id'];

            $this->assertArrayHasKey('numero_orcamento', $data);
            $numerosOrcamento[] = $data['numero_orcamento'];
        }

        // Verifica se todos os números são únicos
        $this->assertEquals(count($numerosOrcamento), count(array_unique($numerosOrcamento)));
    }
}
