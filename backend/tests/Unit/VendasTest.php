<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de Vendas
 *
 * Cobre:
 * - Criação de vendas com itens
 * - Baixa automática de estoque
 * - Cálculo de totais e descontos
 * - Cancelamento de vendas
 * - Reversão de estoque ao cancelar
 * - Integração com clientes
 * - Integração com financeiro
 * - Validações de negócio
 * - Métodos de pagamento
 */
class VendasTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
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
        // Limpa vendas criadas
        foreach ($this->createdVendaIds as $id) {
            try {
                $this->client->delete("/api/vendas/{$id}");
            } catch (\Exception $e) {
                // Ignora erros na limpeza
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
    private function criarCategoria($nome = 'Categoria Teste')
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
        // Cria produto
        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => $descricao,
                'categoria_id' => $categoriaId,
                'preco_custo' => $precoVenda * 0.6,
                'preco_venda' => $precoVenda,
                'estoque_minimo' => 10.0,
                'estoque_maximo' => 500.0,
                'ativo' => true
            ]
        ]);
        $data = json_decode($response->getBody(), true);
        $produtoId = $data['id'];
        $this->createdProdutoIds[] = $produtoId;

        // Adiciona estoque inicial
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
    private function criarCliente($nome = 'Cliente Teste', $tipo = 'PF')
    {
        $payload = [
            'nome' => $nome,
            'tipo_pessoa' => $tipo,
            'cpf_cnpj' => $tipo === 'PF' ? '12345678901' : '12345678000199',
            'email' => 'cliente@teste.com',
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
     * Teste: Criar venda simples com sucesso
     * Cenário: Venda com 1 item
     * Esperado: Status 201, venda criada, estoque baixado
     */
    public function testCriarVendaSimplesComSucesso()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000001', 'Produto Venda 1', $categoriaId, 50.0, 100.0);

        // Verifica estoque antes
        $estoqueAntes = $this->client->get("/api/produtos/{$produtoId}");
        $estoqueAntesData = json_decode($estoqueAntes->getBody(), true);

        $payload = [
            'cliente_id' => null,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 5.0,
                    'preco_unitario' => 50.0
                ]
            ],
            'forma_pagamento' => 'DINHEIRO',
            'observacoes' => 'Venda teste'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('numero_venda', $data);
        $this->assertArrayHasKey('data_venda', $data);
        $this->assertArrayHasKey('valor_total', $data);
        $this->assertArrayHasKey('itens', $data);
        $this->assertArrayHasKey('status', $data);

        $this->assertEquals(250.0, $data['valor_total']); // 5 * 50
        $this->assertEquals('DINHEIRO', $data['forma_pagamento']);
        $this->assertCount(1, $data['itens']);
        $this->assertEquals('FINALIZADA', $data['status']);

        $this->createdVendaIds[] = $data['id'];

        // Verifica se estoque foi baixado
        $estoqueDepois = $this->client->get("/api/produtos/{$produtoId}");
        $estoqueDepoisData = json_decode($estoqueDepois->getBody(), true);

        $this->assertEquals(
            $estoqueAntesData['estoque_atual'] - 5.0,
            $estoqueDepoisData['estoque_atual']
        );
    }

    /**
     * Teste: Criar venda com múltiplos itens
     * Cenário: Venda com 3 produtos diferentes
     * Esperado: Status 201, total calculado corretamente
     */
    public function testCriarVendaComMultiplosItens()
    {
        $categoriaId = $this->criarCategoria();
        $produto1Id = $this->criarProduto('VEN0000000002', 'Produto A', $categoriaId, 10.0, 50.0);
        $produto2Id = $this->criarProduto('VEN0000000003', 'Produto B', $categoriaId, 20.0, 50.0);
        $produto3Id = $this->criarProduto('VEN0000000004', 'Produto C', $categoriaId, 30.0, 50.0);

        $payload = [
            'itens' => [
                [
                    'produto_id' => $produto1Id,
                    'quantidade' => 2.0,
                    'preco_unitario' => 10.0
                ],
                [
                    'produto_id' => $produto2Id,
                    'quantidade' => 3.0,
                    'preco_unitario' => 20.0
                ],
                [
                    'produto_id' => $produto3Id,
                    'quantidade' => 1.0,
                    'preco_unitario' => 30.0
                ]
            ],
            'forma_pagamento' => 'CREDITO'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        // (2*10) + (3*20) + (1*30) = 20 + 60 + 30 = 110
        $this->assertEquals(110.0, $data['valor_total']);
        $this->assertCount(3, $data['itens']);

        $this->createdVendaIds[] = $data['id'];
    }

    /**
     * Teste: Criar venda com desconto
     * Cenário: Aplicar desconto na venda
     * Esperado: Desconto aplicado corretamente
     */
    public function testCriarVendaComDesconto()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000005', 'Produto Desconto', $categoriaId, 100.0, 50.0);

        $payload = [
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 2.0,
                    'preco_unitario' => 100.0
                ]
            ],
            'desconto' => 20.0,
            'forma_pagamento' => 'DINHEIRO'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals(20.0, $data['desconto']);
        $this->assertEquals(180.0, $data['valor_total']); // (2*100) - 20 = 180

        $this->createdVendaIds[] = $data['id'];
    }

    /**
     * Teste: Criar venda com desconto percentual
     * Cenário: Desconto de 10% sobre o total
     * Esperado: Cálculo correto
     */
    public function testCriarVendaComDescontoPercentual()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000006', 'Produto %', $categoriaId, 100.0, 50.0);

        $payload = [
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 5.0,
                    'preco_unitario' => 100.0
                ]
            ],
            'desconto_percentual' => 10.0,
            'forma_pagamento' => 'PIX'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        // 5*100 = 500, 10% = 50, total = 450
        $this->assertEquals(450.0, $data['valor_total']);

        $this->createdVendaIds[] = $data['id'];
    }

    /**
     * Teste: Criar venda sem itens
     * Cenário: Enviar venda sem itens
     * Esperado: Status 422, erro de validação
     */
    public function testCriarVendaSemItens()
    {
        $payload = [
            'itens' => [],
            'forma_pagamento' => 'DINHEIRO'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertArrayHasKey('detail', $data);
    }

    /**
     * Teste: Criar venda com quantidade inválida
     * Cenário: Quantidade zero ou negativa
     * Esperado: Status 422
     */
    public function testCriarVendaComQuantidadeInvalida()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000007', 'Produto', $categoriaId, 50.0);

        $payload = [
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => -5.0,
                    'preco_unitario' => 50.0
                ]
            ],
            'forma_pagamento' => 'DINHEIRO'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar venda com estoque insuficiente
     * Cenário: Tentar vender mais que o estoque disponível
     * Esperado: Status 400, mensagem de estoque insuficiente
     */
    public function testCriarVendaComEstoqueInsuficiente()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000008', 'Produto Pouco Estoque', $categoriaId, 50.0, 10.0);

        $payload = [
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 50.0, // Estoque tem apenas 10
                    'preco_unitario' => 50.0
                ]
            ],
            'forma_pagamento' => 'DINHEIRO'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(400, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertArrayHasKey('detail', $data);
        $this->assertStringContainsString('insuficiente', strtolower($data['detail']));
    }

    /**
     * Teste: Criar venda com produto inexistente
     * Cenário: produto_id que não existe
     * Esperado: Status 404
     */
    public function testCriarVendaComProdutoInexistente()
    {
        $payload = [
            'itens' => [
                [
                    'produto_id' => 999999,
                    'quantidade' => 1.0,
                    'preco_unitario' => 10.0
                ]
            ],
            'forma_pagamento' => 'DINHEIRO'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [400, 404]);
    }

    /**
     * Teste: Buscar venda por ID
     * Cenário: Criar venda e buscar pelo ID
     * Esperado: Status 200, dados completos
     */
    public function testBuscarVendaPorId()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000009', 'Produto Busca', $categoriaId, 25.0);

        $createResponse = $this->client->post('/api/vendas', [
            'json' => [
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 2.0,
                        'preco_unitario' => 25.0
                    ]
                ],
                'forma_pagamento' => 'DEBITO'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $vendaId = $created['id'];
        $this->createdVendaIds[] = $vendaId;

        // Busca venda
        $response = $this->client->get("/api/vendas/{$vendaId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($vendaId, $data['id']);
        $this->assertEquals(50.0, $data['valor_total']);
        $this->assertArrayHasKey('itens', $data);
        $this->assertCount(1, $data['itens']);
    }

    /**
     * Teste: Buscar venda inexistente
     * Cenário: Buscar ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarVendaInexistente()
    {
        $response = $this->client->get('/api/vendas/999999');

        $this->assertEquals(404, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertArrayHasKey('detail', $data);
    }

    /**
     * Teste: Listar vendas com paginação
     * Cenário: Criar várias vendas e listar
     * Esperado: Lista paginada
     */
    public function testListarVendasComPaginacao()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000010', 'Produto Lista', $categoriaId, 10.0, 100.0);

        // Cria 3 vendas
        for ($i = 0; $i < 3; $i++) {
            $createResponse = $this->client->post('/api/vendas', [
                'json' => [
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 1.0,
                            'preco_unitario' => 10.0
                        ]
                    ],
                    'forma_pagamento' => 'DINHEIRO'
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdVendaIds[] = $created['id'];
        }

        // Lista vendas
        $response = $this->client->get('/api/vendas?page=1&page_size=10');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertArrayHasKey('total', $data);
        $this->assertArrayHasKey('page', $data);
        $this->assertArrayHasKey('page_size', $data);

        $this->assertGreaterThanOrEqual(3, $data['total']);
    }

    /**
     * Teste: Cancelar venda
     * Cenário: Cancelar venda existente
     * Esperado: Status atualizado, estoque devolvido
     */
    public function testCancelarVenda()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000011', 'Produto Cancelar', $categoriaId, 30.0, 50.0);

        // Verifica estoque antes
        $estoqueAntes = $this->client->get("/api/produtos/{$produtoId}");
        $estoqueAntesData = json_decode($estoqueAntes->getBody(), true);

        // Cria venda
        $createResponse = $this->client->post('/api/vendas', [
            'json' => [
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 10.0,
                        'preco_unitario' => 30.0
                    ]
                ],
                'forma_pagamento' => 'DINHEIRO'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $vendaId = $created['id'];

        // Verifica estoque depois da venda
        $estoqueDepoisVenda = $this->client->get("/api/produtos/{$produtoId}");
        $estoqueDepoisVendaData = json_decode($estoqueDepoisVenda->getBody(), true);

        $this->assertEquals(
            $estoqueAntesData['estoque_atual'] - 10.0,
            $estoqueDepoisVendaData['estoque_atual']
        );

        // Cancela venda
        $cancelResponse = $this->client->post("/api/vendas/{$vendaId}/cancelar");

        $this->assertContains($cancelResponse->getStatusCode(), [200, 204]);

        // Verifica se estoque foi devolvido
        $estoqueDepoisCancelamento = $this->client->get("/api/produtos/{$produtoId}");
        $estoqueDepoisCancelamentoData = json_decode($estoqueDepoisCancelamento->getBody(), true);

        $this->assertEquals(
            $estoqueAntesData['estoque_atual'],
            $estoqueDepoisCancelamentoData['estoque_atual']
        );

        // Verifica status da venda
        $vendaResponse = $this->client->get("/api/vendas/{$vendaId}");
        if ($vendaResponse->getStatusCode() === 200) {
            $vendaData = json_decode($vendaResponse->getBody(), true);
            $this->assertEquals('CANCELADA', $vendaData['status']);
        }
    }

    /**
     * Teste: Cancelar venda inexistente
     * Cenário: Tentar cancelar ID que não existe
     * Esperado: Status 404
     */
    public function testCancelarVendaInexistente()
    {
        $response = $this->client->post('/api/vendas/999999/cancelar');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Criar venda com cliente
     * Cenário: Venda vinculada a cliente
     * Esperado: Status 201, cliente associado
     */
    public function testCriarVendaComCliente()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000012', 'Produto Cliente', $categoriaId, 40.0);
        $clienteId = $this->criarCliente('João Silva', 'PF');

        $payload = [
            'cliente_id' => $clienteId,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 3.0,
                    'preco_unitario' => 40.0
                ]
            ],
            'forma_pagamento' => 'CREDITO'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($clienteId, $data['cliente_id']);
        $this->assertEquals(120.0, $data['valor_total']);

        $this->createdVendaIds[] = $data['id'];
    }

    /**
     * Teste: Criar venda com cliente inexistente
     * Cenário: cliente_id que não existe
     * Esperado: Status 404 ou 400
     */
    public function testCriarVendaComClienteInexistente()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000013', 'Produto', $categoriaId, 10.0);

        $payload = [
            'cliente_id' => 999999,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 1.0,
                    'preco_unitario' => 10.0
                ]
            ],
            'forma_pagamento' => 'DINHEIRO'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [400, 404]);
    }

    /**
     * Teste: Validar formas de pagamento aceitas
     * Cenário: Testar diferentes formas de pagamento
     * Esperado: Aceitar formas válidas
     */
    public function testFormasPagamentoValidas()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000014', 'Produto Pgto', $categoriaId, 15.0, 100.0);

        $formasPagamento = ['DINHEIRO', 'DEBITO', 'CREDITO', 'PIX', 'BOLETO'];

        foreach ($formasPagamento as $forma) {
            $response = $this->client->post('/api/vendas', [
                'json' => [
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 1.0,
                            'preco_unitario' => 15.0
                        ]
                    ],
                    'forma_pagamento' => $forma
                ]
            ]);

            $this->assertEquals(201, $response->getStatusCode(), "Forma de pagamento {$forma} não foi aceita");

            $data = json_decode($response->getBody(), true);
            $this->assertEquals($forma, $data['forma_pagamento']);
            $this->createdVendaIds[] = $data['id'];
        }
    }

    /**
     * Teste: Forma de pagamento inválida
     * Cenário: Enviar forma de pagamento não aceita
     * Esperado: Status 422
     */
    public function testFormaPagamentoInvalida()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000015', 'Produto', $categoriaId, 10.0);

        $payload = [
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 1.0,
                    'preco_unitario' => 10.0
                ]
            ],
            'forma_pagamento' => 'CHEQUE_VOADOR'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Validar timestamps da venda
     * Cenário: Verificar created_at e data_venda
     * Esperado: Campos preenchidos com formato correto
     */
    public function testTimestampsVenda()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000016', 'Produto Time', $categoriaId, 20.0);

        $response = $this->client->post('/api/vendas', [
            'json' => [
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 1.0,
                        'preco_unitario' => 20.0
                    ]
                ],
                'forma_pagamento' => 'DINHEIRO'
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdVendaIds[] = $data['id'];

        $this->assertArrayHasKey('data_venda', $data);
        $this->assertArrayHasKey('created_at', $data);
        $this->assertNotEmpty($data['data_venda']);
        $this->assertNotEmpty($data['created_at']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}/', $data['data_venda']);
    }

    /**
     * Teste: Filtrar vendas por data
     * Cenário: Buscar vendas em período específico
     * Esperado: Retornar apenas vendas do período
     */
    public function testFiltrarVendasPorData()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000017', 'Produto Data', $categoriaId, 10.0, 100.0);

        // Cria vendas
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/vendas', [
                'json' => [
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 1.0,
                            'preco_unitario' => 10.0
                        ]
                    ],
                    'forma_pagamento' => 'DINHEIRO'
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdVendaIds[] = $created['id'];
        }

        $dataHoje = date('Y-m-d');
        $response = $this->client->get("/api/vendas?data_inicio={$dataHoje}&data_fim={$dataHoje}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertArrayHasKey('items', $data);
        $this->assertGreaterThanOrEqual(2, $data['total']);
    }

    /**
     * Teste: Filtrar vendas por cliente
     * Cenário: Buscar vendas de cliente específico
     * Esperado: Retornar apenas vendas do cliente
     */
    public function testFiltrarVendasPorCliente()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000018', 'Produto', $categoriaId, 10.0, 100.0);
        $clienteId = $this->criarCliente('Maria Santos', 'PF');

        // Cria vendas para o cliente
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/vendas', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 1.0,
                            'preco_unitario' => 10.0
                        ]
                    ],
                    'forma_pagamento' => 'DINHEIRO'
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdVendaIds[] = $created['id'];
        }

        $response = $this->client->get("/api/vendas?cliente_id={$clienteId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertGreaterThanOrEqual(2, $data['total']);

        // Verifica se todas as vendas são do cliente
        foreach ($data['items'] as $venda) {
            $this->assertEquals($clienteId, $venda['cliente_id']);
        }
    }

    /**
     * Teste: Calcular valor total com múltiplos itens e desconto
     * Cenário: Venda complexa com cálculos
     * Esperado: Total correto
     */
    public function testCalculoValorTotalComplexo()
    {
        $categoriaId = $this->criarCategoria();
        $produto1Id = $this->criarProduto('VEN0000000019', 'Produto 1', $categoriaId, 25.0, 100.0);
        $produto2Id = $this->criarProduto('VEN0000000020', 'Produto 2', $categoriaId, 35.0, 100.0);

        $payload = [
            'itens' => [
                [
                    'produto_id' => $produto1Id,
                    'quantidade' => 4.0,
                    'preco_unitario' => 25.0
                ],
                [
                    'produto_id' => $produto2Id,
                    'quantidade' => 2.0,
                    'preco_unitario' => 35.0
                ]
            ],
            'desconto' => 30.0,
            'forma_pagamento' => 'PIX'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $data = json_decode($response->getBody(), true);

        // (4*25) + (2*35) = 100 + 70 = 170
        // 170 - 30 = 140
        $this->assertEquals(140.0, $data['valor_total']);
        $this->assertEquals(30.0, $data['desconto']);

        $this->createdVendaIds[] = $data['id'];
    }

    /**
     * Teste: Número de venda único
     * Cenário: Criar múltiplas vendas
     * Esperado: Cada venda tem número único
     */
    public function testNumeroVendaUnico()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000021', 'Produto Num', $categoriaId, 10.0, 100.0);

        $numerosVenda = [];

        for ($i = 0; $i < 3; $i++) {
            $response = $this->client->post('/api/vendas', [
                'json' => [
                    'itens' => [
                        [
                            'produto_id' => $produtoId,
                            'quantidade' => 1.0,
                            'preco_unitario' => 10.0
                        ]
                    ],
                    'forma_pagamento' => 'DINHEIRO'
                ]
            ]);

            $data = json_decode($response->getBody(), true);
            $this->createdVendaIds[] = $data['id'];

            $this->assertArrayHasKey('numero_venda', $data);
            $numerosVenda[] = $data['numero_venda'];
        }

        // Verifica se todos os números são únicos
        $this->assertEquals(count($numerosVenda), count(array_unique($numerosVenda)));
    }

    /**
     * Teste: Preço unitário diferente do cadastrado
     * Cenário: Vender com preço promocional
     * Esperado: Aceitar preço informado
     */
    public function testPrecoUnitarioDiferente()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('VEN0000000022', 'Produto Promo', $categoriaId, 100.0);

        $payload = [
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 2.0,
                    'preco_unitario' => 80.0 // Preço promocional
                ]
            ],
            'forma_pagamento' => 'DINHEIRO'
        ];

        $response = $this->client->post('/api/vendas', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals(160.0, $data['valor_total']); // 2 * 80
        $this->assertEquals(80.0, $data['itens'][0]['preco_unitario']);

        $this->createdVendaIds[] = $data['id'];
    }
}
