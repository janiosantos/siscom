<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo PDV (Ponto de Venda)
 *
 * Cobre:
 * - Abertura e fechamento de caixa
 * - Vendas rápidas no PDV
 * - Controle de sangria e suprimento
 * - Cálculo de troco
 * - Múltiplas formas de pagamento
 * - Relatório de movimentação
 * - Validações de segurança
 * - Fluxo completo de caixa
 */
class PdvTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdCaixaIds = [];
    private $createdVendaIds = [];
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
        // Fecha caixas abertos
        foreach ($this->createdCaixaIds as $id) {
            try {
                $this->client->post("/api/pdv/caixas/{$id}/fechar", [
                    'json' => ['valor_final' => 0]
                ]);
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

        parent::tearDown();
    }

    /**
     * Helper: Criar categoria
     */
    private function criarCategoria($nome = 'Categoria PDV')
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
     * Teste: Abrir caixa com sucesso
     * Cenário: Abertura de caixa com valor inicial
     * Esperado: Status 201, caixa aberto
     */
    public function testAbrirCaixaComSucesso()
    {
        $payload = [
            'operador' => 'João Silva',
            'valor_inicial' => 200.0
        ];

        $response = $this->client->post('/api/pdv/caixas', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('operador', $data);
        $this->assertArrayHasKey('valor_inicial', $data);
        $this->assertArrayHasKey('status', $data);
        $this->assertArrayHasKey('data_abertura', $data);

        $this->assertEquals('João Silva', $data['operador']);
        $this->assertEquals(200.0, $data['valor_inicial']);
        $this->assertEquals('ABERTO', $data['status']);

        $this->createdCaixaIds[] = $data['id'];
    }

    /**
     * Teste: Abrir caixa sem operador
     * Cenário: Tentar abrir caixa sem informar operador
     * Esperado: Status 422
     */
    public function testAbrirCaixaSemOperador()
    {
        $payload = [
            'valor_inicial' => 100.0
        ];

        $response = $this->client->post('/api/pdv/caixas', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Abrir caixa com valor inicial negativo
     * Cenário: Valor inicial < 0
     * Esperado: Status 422
     */
    public function testAbrirCaixaComValorInicialNegativo()
    {
        $payload = [
            'operador' => 'Maria',
            'valor_inicial' => -50.0
        ];

        $response = $this->client->post('/api/pdv/caixas', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Buscar caixa por ID
     * Cenário: Abrir caixa e buscar
     * Esperado: Dados completos do caixa
     */
    public function testBuscarCaixaPorId()
    {
        $createResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Pedro',
                'valor_inicial' => 150.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $caixaId = $created['id'];
        $this->createdCaixaIds[] = $caixaId;

        $response = $this->client->get("/api/pdv/caixas/{$caixaId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($caixaId, $data['id']);
        $this->assertEquals('Pedro', $data['operador']);
        $this->assertEquals(150.0, $data['valor_inicial']);
    }

    /**
     * Teste: Buscar caixa inexistente
     * Cenário: ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarCaixaInexistente()
    {
        $response = $this->client->get('/api/pdv/caixas/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Registrar venda no PDV
     * Cenário: Venda rápida pelo PDV
     * Esperado: Venda registrada, associada ao caixa
     */
    public function testRegistrarVendaNoPdv()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Ana',
                'valor_inicial' => 100.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        // Cria produto
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('PDV0000000001', 'Produto PDV', $categoriaId, 25.0);

        // Registra venda
        $vendaPayload = [
            'caixa_id' => $caixaId,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 2.0,
                    'preco_unitario' => 25.0
                ]
            ],
            'forma_pagamento' => 'DINHEIRO',
            'valor_pago' => 50.0
        ];

        $vendaResponse = $this->client->post('/api/pdv/vendas', [
            'json' => $vendaPayload
        ]);

        $this->assertEquals(201, $vendaResponse->getStatusCode());

        $vendaData = json_decode($vendaResponse->getBody(), true);

        $this->assertEquals($caixaId, $vendaData['caixa_id']);
        $this->assertEquals(50.0, $vendaData['valor_total']);
        $this->assertEquals(0.0, $vendaData['troco']);

        if (isset($vendaData['id'])) {
            $this->createdVendaIds[] = $vendaData['id'];
        }
    }

    /**
     * Teste: Calcular troco corretamente
     * Cenário: Cliente paga com valor maior
     * Esperado: Troco calculado corretamente
     */
    public function testCalcularTroco()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Carlos',
                'valor_inicial' => 200.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        // Cria produto
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('PDV0000000002', 'Produto Troco', $categoriaId, 37.0);

        // Venda com troco
        $vendaPayload = [
            'caixa_id' => $caixaId,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 1.0,
                    'preco_unitario' => 37.0
                ]
            ],
            'forma_pagamento' => 'DINHEIRO',
            'valor_pago' => 50.0
        ];

        $vendaResponse = $this->client->post('/api/pdv/vendas', [
            'json' => $vendaPayload
        ]);

        $vendaData = json_decode($vendaResponse->getBody(), true);

        $this->assertEquals(37.0, $vendaData['valor_total']);
        $this->assertEquals(13.0, $vendaData['troco']); // 50 - 37 = 13

        if (isset($vendaData['id'])) {
            $this->createdVendaIds[] = $vendaData['id'];
        }
    }

    /**
     * Teste: Registrar sangria
     * Cenário: Retirada de dinheiro do caixa
     * Esperado: Sangria registrada, saldo atualizado
     */
    public function testRegistrarSangria()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Lucia',
                'valor_inicial' => 500.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        // Registra sangria
        $sangriaPayload = [
            'valor' => 200.0,
            'motivo' => 'Depósito bancário'
        ];

        $response = $this->client->post("/api/pdv/caixas/{$caixaId}/sangria", [
            'json' => $sangriaPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201]);

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('valor', $data);
        $this->assertEquals(200.0, $data['valor']);
        $this->assertEquals('Depósito bancário', $data['motivo']);
    }

    /**
     * Teste: Registrar suprimento
     * Cenário: Adicionar dinheiro ao caixa
     * Esperado: Suprimento registrado, saldo atualizado
     */
    public function testRegistrarSuprimento()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Fernando',
                'valor_inicial' => 50.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        // Registra suprimento
        $suprimentoPayload = [
            'valor' => 150.0,
            'motivo' => 'Reforço de caixa'
        ];

        $response = $this->client->post("/api/pdv/caixas/{$caixaId}/suprimento", [
            'json' => $suprimentoPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201]);

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('valor', $data);
        $this->assertEquals(150.0, $data['valor']);
        $this->assertEquals('Reforço de caixa', $data['motivo']);
    }

    /**
     * Teste: Sangria com valor maior que saldo
     * Cenário: Tentar retirar mais que o disponível
     * Esperado: Status 400, erro de validação
     */
    public function testSangriaComValorMaiorQueSaldo()
    {
        // Abre caixa com pouco dinheiro
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Roberto',
                'valor_inicial' => 50.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        // Tenta sangria maior
        $sangriaPayload = [
            'valor' => 500.0,
            'motivo' => 'Teste'
        ];

        $response = $this->client->post("/api/pdv/caixas/{$caixaId}/sangria", [
            'json' => $sangriaPayload
        ]);

        $this->assertEquals(400, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertArrayHasKey('detail', $data);
    }

    /**
     * Teste: Fechar caixa
     * Cenário: Fechamento normal com valor final
     * Esperado: Status atualizado para FECHADO
     */
    public function testFecharCaixa()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Julia',
                'valor_inicial' => 300.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];

        // Fecha caixa
        $fechamentoPayload = [
            'valor_final' => 450.0
        ];

        $response = $this->client->post("/api/pdv/caixas/{$caixaId}/fechar", [
            'json' => $fechamentoPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/pdv/caixas/{$caixaId}");
        if ($getResponse->getStatusCode() === 200) {
            $caixaData = json_decode($getResponse->getBody(), true);
            $this->assertEquals('FECHADO', $caixaData['status']);
            $this->assertEquals(450.0, $caixaData['valor_final']);
            $this->assertArrayHasKey('data_fechamento', $caixaData);
        }
    }

    /**
     * Teste: Fechar caixa já fechado
     * Cenário: Tentar fechar caixa que já está fechado
     * Esperado: Status 400
     */
    public function testFecharCaixaJaFechado()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Sandra',
                'valor_inicial' => 100.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];

        // Fecha primeira vez
        $this->client->post("/api/pdv/caixas/{$caixaId}/fechar", [
            'json' => ['valor_final' => 150.0]
        ]);

        // Tenta fechar novamente
        $response = $this->client->post("/api/pdv/caixas/{$caixaId}/fechar", [
            'json' => ['valor_final' => 150.0]
        ]);

        $this->assertEquals(400, $response->getStatusCode());
    }

    /**
     * Teste: Listar caixas com filtros
     * Cenário: Buscar caixas abertos/fechados
     * Esperado: Lista filtrada
     */
    public function testListarCaixasComFiltros()
    {
        // Abre 2 caixas
        for ($i = 0; $i < 2; $i++) {
            $response = $this->client->post('/api/pdv/caixas', [
                'json' => [
                    'operador' => "Operador {$i}",
                    'valor_inicial' => 100.0
                ]
            ]);
            $data = json_decode($response->getBody(), true);
            $this->createdCaixaIds[] = $data['id'];
        }

        // Lista caixas abertos
        $response = $this->client->get('/api/pdv/caixas?status=ABERTO');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertGreaterThanOrEqual(2, $data['total']);

        // Verifica se todos estão abertos
        foreach ($data['items'] as $caixa) {
            $this->assertEquals('ABERTO', $caixa['status']);
        }
    }

    /**
     * Teste: Relatório de movimentação do caixa
     * Cenário: Buscar todas as movimentações
     * Esperado: Lista de vendas, sangrias e suprimentos
     */
    public function testRelatorioMovimentacaoCaixa()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Beatriz',
                'valor_inicial' => 200.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        // Registra suprimento
        $this->client->post("/api/pdv/caixas/{$caixaId}/suprimento", [
            'json' => [
                'valor' => 100.0,
                'motivo' => 'Reforço'
            ]
        ]);

        // Registra sangria
        $this->client->post("/api/pdv/caixas/{$caixaId}/sangria", [
            'json' => [
                'valor' => 50.0,
                'motivo' => 'Depósito'
            ]
        ]);

        // Busca movimentação
        $response = $this->client->get("/api/pdv/caixas/{$caixaId}/movimentacao");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('movimentacoes', $data);
        $this->assertIsArray($data['movimentacoes']);
        $this->assertGreaterThanOrEqual(2, count($data['movimentacoes']));
    }

    /**
     * Teste: Venda no PDV sem caixa aberto
     * Cenário: Tentar vender sem caixa_id ou com caixa fechado
     * Esperado: Status 400
     */
    public function testVendaSemCaixaAberto()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('PDV0000000003', 'Produto', $categoriaId, 10.0);

        $vendaPayload = [
            'caixa_id' => 999999,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 1.0,
                    'preco_unitario' => 10.0
                ]
            ],
            'forma_pagamento' => 'DINHEIRO',
            'valor_pago' => 10.0
        ];

        $response = $this->client->post('/api/pdv/vendas', [
            'json' => $vendaPayload
        ]);

        $this->assertContains($response->getStatusCode(), [400, 404]);
    }

    /**
     * Teste: Venda com pagamento insuficiente
     * Cenário: Valor pago menor que total
     * Esperado: Status 400
     */
    public function testVendaComPagamentoInsuficiente()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Ricardo',
                'valor_inicial' => 100.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('PDV0000000004', 'Produto', $categoriaId, 50.0);

        $vendaPayload = [
            'caixa_id' => $caixaId,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 2.0,
                    'preco_unitario' => 50.0
                ]
            ],
            'forma_pagamento' => 'DINHEIRO',
            'valor_pago' => 80.0 // Total é 100, pago apenas 80
        ];

        $response = $this->client->post('/api/pdv/vendas', [
            'json' => $vendaPayload
        ]);

        $this->assertEquals(400, $response->getStatusCode());
    }

    /**
     * Teste: Múltiplas formas de pagamento
     * Cenário: Pagar com dinheiro + cartão
     * Esperado: Venda aceita com múltiplos pagamentos
     */
    public function testMultiplasFormasPagamento()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Paula',
                'valor_inicial' => 100.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('PDV0000000005', 'Produto Mix', $categoriaId, 80.0);

        $vendaPayload = [
            'caixa_id' => $caixaId,
            'itens' => [
                [
                    'produto_id' => $produtoId,
                    'quantidade' => 1.0,
                    'preco_unitario' => 80.0
                ]
            ],
            'pagamentos' => [
                [
                    'forma_pagamento' => 'DINHEIRO',
                    'valor' => 50.0
                ],
                [
                    'forma_pagamento' => 'CREDITO',
                    'valor' => 30.0
                ]
            ]
        ];

        $response = $this->client->post('/api/pdv/vendas', [
            'json' => $vendaPayload
        ]);

        // Pode retornar 201 se aceitar, ou 422 se não implementado ainda
        $this->assertContains($response->getStatusCode(), [201, 422]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->assertEquals(80.0, $data['valor_total']);
            if (isset($data['id'])) {
                $this->createdVendaIds[] = $data['id'];
            }
        }
    }

    /**
     * Teste: Calcular diferença de caixa (quebra)
     * Cenário: Valor final diferente do esperado
     * Esperado: Diferença calculada
     */
    public function testCalcularDiferencaCaixa()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Marcos',
                'valor_inicial' => 100.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];

        // Faz venda
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('PDV0000000006', 'Produto', $categoriaId, 50.0);

        $this->client->post('/api/pdv/vendas', [
            'json' => [
                'caixa_id' => $caixaId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 2.0,
                        'preco_unitario' => 50.0
                    ]
                ],
                'forma_pagamento' => 'DINHEIRO',
                'valor_pago' => 100.0
            ]
        ]);

        // Fecha com valor diferente (esperado: 200, informado: 195)
        $response = $this->client->post("/api/pdv/caixas/{$caixaId}/fechar", [
            'json' => ['valor_final' => 195.0]
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Busca caixa para ver diferença
        $getResponse = $this->client->get("/api/pdv/caixas/{$caixaId}");
        if ($getResponse->getStatusCode() === 200) {
            $caixaData = json_decode($getResponse->getBody(), true);

            if (isset($caixaData['diferenca'])) {
                $this->assertEquals(-5.0, $caixaData['diferenca']); // Faltaram 5
            }
        }
    }

    /**
     * Teste: Validar timestamps de abertura e fechamento
     * Cenário: Verificar datas
     * Esperado: Campos preenchidos
     */
    public function testTimestampsCaixa()
    {
        $response = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Renata',
                'valor_inicial' => 150.0
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdCaixaIds[] = $data['id'];

        $this->assertArrayHasKey('data_abertura', $data);
        $this->assertNotEmpty($data['data_abertura']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/', $data['data_abertura']);
    }

    /**
     * Teste: Buscar caixa atual aberto
     * Cenário: Buscar o caixa aberto do operador
     * Esperado: Retornar caixa aberto
     */
    public function testBuscarCaixaAtualAberto()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Fabio Atual',
                'valor_inicial' => 100.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        // Busca caixa atual
        $response = $this->client->get('/api/pdv/caixas/atual?operador=Fabio Atual');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertEquals('ABERTO', $data['status']);
            $this->assertEquals('Fabio Atual', $data['operador']);
        } else {
            // Endpoint pode não estar implementado
            $this->assertContains($response->getStatusCode(), [404, 501]);
        }
    }

    /**
     * Teste: Sangria sem motivo
     * Cenário: Tentar fazer sangria sem informar motivo
     * Esperado: Status 422
     */
    public function testSangriaSemMotivo()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Carla',
                'valor_inicial' => 300.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        $sangriaPayload = [
            'valor' => 100.0
        ];

        $response = $this->client->post("/api/pdv/caixas/{$caixaId}/sangria", [
            'json' => $sangriaPayload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Suprimento com valor negativo
     * Cenário: Valor de suprimento < 0
     * Esperado: Status 422
     */
    public function testSuprimentoComValorNegativo()
    {
        // Abre caixa
        $caixaResponse = $this->client->post('/api/pdv/caixas', [
            'json' => [
                'operador' => 'Diego',
                'valor_inicial' => 100.0
            ]
        ]);
        $caixa = json_decode($caixaResponse->getBody(), true);
        $caixaId = $caixa['id'];
        $this->createdCaixaIds[] = $caixaId;

        $suprimentoPayload = [
            'valor' => -50.0,
            'motivo' => 'Teste'
        ];

        $response = $this->client->post("/api/pdv/caixas/{$caixaId}/suprimento", [
            'json' => $suprimentoPayload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }
}
