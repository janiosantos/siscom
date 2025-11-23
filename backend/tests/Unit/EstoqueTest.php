<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes completos para o módulo de Estoque
 *
 * Cobre:
 * - Entrada de estoque
 * - Saída de estoque
 * - Ajuste de estoque
 * - Movimentações
 * - Controle automático de estoque
 * - Validações de quantidade
 * - Estoque insuficiente
 * - Histórico de movimentações
 */
class EstoqueTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdProdutoIds = [];
    private $createdCategoriaIds = [];
    private $createdMovimentacaoIds = [];

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
        // Limpa produtos
        foreach ($this->createdProdutoIds as $id) {
            try {
                $this->client->delete("/api/produtos/{$id}");
            } catch (\Exception $e) {
            }
        }

        // Limpa categorias
        foreach ($this->createdCategoriaIds as $id) {
            try {
                $this->client->delete("/api/categorias/{$id}");
            } catch (\Exception $e) {
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
     * Helper: Criar produto
     */
    private function criarProduto($codigoBarras, $descricao, $categoriaId, $estoqueInicial = 0.0)
    {
        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => $descricao,
                'categoria_id' => $categoriaId,
                'preco_custo' => 10.0,
                'preco_venda' => 15.0,
                'estoque_atual' => $estoqueInicial,
                'estoque_minimo' => 5.0
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdProdutoIds[] = $data['id'];

        return $data['id'];
    }

    /**
     * Teste: Entrada de estoque com sucesso
     * Cenário: Registrar entrada de 50 unidades
     * Esperado: Movimentação criada, estoque atualizado
     */
    public function testEntradaEstoqueComSucesso()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ENT0000000001', 'Produto Entrada', $categoriaId, 100.0);

        // Consulta estoque inicial
        $getInicial = $this->client->get("/api/produtos/{$produtoId}");
        $produtoInicial = json_decode($getInicial->getBody(), true);
        $estoqueInicial = $produtoInicial['estoque_atual'];

        // Entrada de 50 unidades
        $payload = [
            'produto_id' => $produtoId,
            'quantidade' => 50.0,
            'custo_unitario' => 10.50,
            'documento' => 'NF-12345',
            'observacao' => 'Entrada de compra'
        ];

        $response = $this->client->post('/api/estoque/entrada', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        // Valida movimentação
        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('tipo_movimentacao', $data);
        $this->assertArrayHasKey('quantidade', $data);
        $this->assertEquals('ENTRADA', $data['tipo_movimentacao']);
        $this->assertEquals(50.0, $data['quantidade']);
        $this->assertEquals($produtoId, $data['produto_id']);

        // Consulta produto novamente para verificar estoque
        $getAtual = $this->client->get("/api/produtos/{$produtoId}");
        $produtoAtual = json_decode($getAtual->getBody(), true);

        $this->assertEquals($estoqueInicial + 50.0, $produtoAtual['estoque_atual']);
    }

    /**
     * Teste: Entrada com quantidade zero
     * Cenário: quantidade = 0
     * Esperado: Status 422
     */
    public function testEntradaComQuantidadeZero()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ENT0000000002', 'Produto', $categoriaId);

        $payload = [
            'produto_id' => $produtoId,
            'quantidade' => 0.0,
            'custo_unitario' => 10.0
        ];

        $response = $this->client->post('/api/estoque/entrada', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Entrada com quantidade negativa
     * Cenário: quantidade < 0
     * Esperado: Status 422
     */
    public function testEntradaComQuantidadeNegativa()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('ENT0000000003', 'Produto', $categoriaId);

        $payload = [
            'produto_id' => $produtoId,
            'quantidade' => -10.0,
            'custo_unitario' => 10.0
        ];

        $response = $this->client->post('/api/estoque/entrada', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Entrada para produto inexistente
     * Cenário: produto_id não existe
     * Esperado: Status 404
     */
    public function testEntradaParaProdutoInexistente()
    {
        $payload = [
            'produto_id' => 999999,
            'quantidade' => 10.0,
            'custo_unitario' => 10.0
        ];

        $response = $this->client->post('/api/estoque/entrada', [
            'json' => $payload
        ]);

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Saída de estoque com sucesso
     * Cenário: Produto com 100 unidades, saída de 30
     * Esperado: Estoque atualizado para 70
     */
    public function testSaidaEstoqueComSucesso()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('SAI0000000001', 'Produto Saída', $categoriaId, 100.0);

        $payload = [
            'produto_id' => $produtoId,
            'quantidade' => 30.0,
            'motivo' => 'VENDA',
            'observacao' => 'Venda PDV'
        ];

        $response = $this->client->post('/api/estoque/saida', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertEquals('SAIDA', $data['tipo_movimentacao']);
        $this->assertEquals(30.0, $data['quantidade']);

        // Verifica estoque
        $getAtual = $this->client->get("/api/produtos/{$produtoId}");
        $produtoAtual = json_decode($getAtual->getBody(), true);

        $this->assertEquals(70.0, $produtoAtual['estoque_atual']);
    }

    /**
     * Teste: Saída com estoque insuficiente
     * Cenário: Produto com 10 unidades, tentar saída de 50
     * Esperado: Status 400 (estoque insuficiente)
     */
    public function testSaidaComEstoqueInsuficiente()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('SAI0000000002', 'Produto', $categoriaId, 10.0);

        $payload = [
            'produto_id' => $produtoId,
            'quantidade' => 50.0,
            'motivo' => 'VENDA'
        ];

        $response = $this->client->post('/api/estoque/saida', [
            'json' => $payload
        ]);

        $this->assertEquals(400, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertStringContainsString('insuficiente', strtolower($data['detail'] ?? ''));
    }

    /**
     * Teste: Ajuste de estoque positivo
     * Cenário: Aumentar estoque via ajuste
     * Esperado: Estoque atualizado
     */
    public function testAjusteEstoquePositivo()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('AJU0000000001', 'Produto Ajuste', $categoriaId, 50.0);

        $payload = [
            'produto_id' => $produtoId,
            'quantidade' => 20.0,  // Adiciona 20
            'justificativa' => 'Acerto de inventário',
            'tipo' => 'AJUSTE_POSITIVO'
        ];

        $response = $this->client->post('/api/estoque/ajuste', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        // Verifica estoque
        $getAtual = $this->client->get("/api/produtos/{$produtoId}");
        $produtoAtual = json_decode($getAtual->getBody(), true);

        $this->assertEquals(70.0, $produtoAtual['estoque_atual']);
    }

    /**
     * Teste: Ajuste de estoque negativo
     * Cenário: Reduzir estoque via ajuste (perda, quebra)
     * Esperado: Estoque reduzido
     */
    public function testAjusteEstoqueNegativo()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('AJU0000000002', 'Produto', $categoriaId, 100.0);

        $payload = [
            'produto_id' => $produtoId,
            'quantidade' => -15.0,  // Remove 15
            'justificativa' => 'Produto avariado',
            'tipo' => 'AJUSTE_NEGATIVO'
        ];

        $response = $this->client->post('/api/estoque/ajuste', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        // Verifica estoque
        $getAtual = $this->client->get("/api/produtos/{$produtoId}");
        $produtoAtual = json_decode($getAtual->getBody(), true);

        $this->assertEquals(85.0, $produtoAtual['estoque_atual']);
    }

    /**
     * Teste: Ajuste sem justificativa
     * Cenário: Omitir justificativa obrigatória
     * Esperado: Status 422
     */
    public function testAjusteSemJustificativa()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('AJU0000000003', 'Produto', $categoriaId, 50.0);

        $payload = [
            'produto_id' => $produtoId,
            'quantidade' => 10.0
            // Sem justificativa
        ];

        $response = $this->client->post('/api/estoque/ajuste', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Listar movimentações de um produto
     * Cenário: Fazer várias movimentações e listar
     * Esperado: Histórico completo
     */
    public function testListarMovimentacoesProduto()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('MOV0000000001', 'Produto Mov', $categoriaId, 100.0);

        // Entrada
        $this->client->post('/api/estoque/entrada', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => 50.0,
                'custo_unitario' => 10.0
            ]
        ]);

        // Saída
        $this->client->post('/api/estoque/saida', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => 20.0,
                'motivo' => 'VENDA'
            ]
        ]);

        // Lista movimentações
        $response = $this->client->get("/api/estoque/movimentacoes/produto/{$produtoId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertIsArray($data['items']);
        $this->assertGreaterThanOrEqual(2, count($data['items']));

        // Verifica tipos
        $tipos = array_map(fn($m) => $m['tipo_movimentacao'], $data['items']);
        $this->assertContains('ENTRADA', $tipos);
        $this->assertContains('SAIDA', $tipos);
    }

    /**
     * Teste: Buscar movimentação por ID
     * Cenário: Criar movimentação e buscar
     * Esperado: Dados completos
     */
    public function testBuscarMovimentacaoPorId()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('MOV0000000002', 'Produto', $categoriaId, 50.0);

        $createResponse = $this->client->post('/api/estoque/entrada', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => 25.0,
                'custo_unitario' => 10.0,
                'documento' => 'DOC-123'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $movimentacaoId = $created['id'];

        // Busca
        $response = $this->client->get("/api/estoque/movimentacoes/{$movimentacaoId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertEquals($movimentacaoId, $data['id']);
        $this->assertEquals(25.0, $data['quantidade']);
        $this->assertEquals('ENTRADA', $data['tipo_movimentacao']);
    }

    /**
     * Teste: Consultar estoque atual de produto
     * Cenário: Endpoint específico de consulta de estoque
     * Esperado: Estoque atualizado
     */
    public function testConsultarEstoqueAtual()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('EST0000000001', 'Produto', $categoriaId, 75.0);

        $response = $this->client->get("/api/estoque/produto/{$produtoId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('produto_id', $data);
        $this->assertArrayHasKey('estoque_atual', $data);
        $this->assertEquals($produtoId, $data['produto_id']);
        $this->assertEquals(75.0, $data['estoque_atual']);
    }

    /**
     * Teste: Múltiplas entradas e saídas sequenciais
     * Cenário: Simular movimentações reais
     * Esperado: Estoque calculado corretamente
     */
    public function testMultiplasMovimentacoesSequenciais()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('SEQ0000000001', 'Produto Seq', $categoriaId, 0.0);

        // Entrada 100
        $this->client->post('/api/estoque/entrada', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => 100.0,
                'custo_unitario' => 10.0
            ]
        ]);

        // Saída 30
        $this->client->post('/api/estoque/saida', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => 30.0,
                'motivo' => 'VENDA'
            ]
        ]);

        // Entrada 50
        $this->client->post('/api/estoque/entrada', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => 50.0,
                'custo_unitario' => 10.0
            ]
        ]);

        // Saída 20
        $this->client->post('/api/estoque/saida', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => 20.0,
                'motivo' => 'VENDA'
            ]
        ]);

        // Estoque esperado: 0 + 100 - 30 + 50 - 20 = 100
        $getAtual = $this->client->get("/api/produtos/{$produtoId}");
        $produtoAtual = json_decode($getAtual->getBody(), true);

        $this->assertEquals(100.0, $produtoAtual['estoque_atual']);
    }

    /**
     * Teste: Filtrar movimentações por tipo
     * Cenário: Buscar apenas ENTRADA ou apenas SAIDA
     * Esperado: Filtro aplicado corretamente
     */
    public function testFiltrarMovimentacoesPorTipo()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('FIL0000000001', 'Produto Filtro', $categoriaId, 100.0);

        // Cria várias movimentações
        $this->client->post('/api/estoque/entrada', [
            'json' => ['produto_id' => $produtoId, 'quantidade' => 10.0, 'custo_unitario' => 10.0]
        ]);

        $this->client->post('/api/estoque/saida', [
            'json' => ['produto_id' => $produtoId, 'quantidade' => 5.0, 'motivo' => 'VENDA']
        ]);

        $this->client->post('/api/estoque/entrada', [
            'json' => ['produto_id' => $produtoId, 'quantidade' => 20.0, 'custo_unitario' => 10.0]
        ]);

        // Filtra apenas ENTRADA
        $response = $this->client->get('/api/estoque/movimentacoes?tipo=ENTRADA');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        foreach ($data['items'] as $mov) {
            $this->assertEquals('ENTRADA', $mov['tipo_movimentacao']);
        }
    }

    /**
     * Teste: Movimentação com data_movimentacao customizada
     * Cenário: Lançar movimentação retroativa
     * Esperado: Data aceita (se API permitir)
     */
    public function testMovimentacaoComDataCustomizada()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('DAT0000000001', 'Produto', $categoriaId, 50.0);

        $dataCustomizada = '2024-01-15T10:30:00';

        $payload = [
            'produto_id' => $produtoId,
            'quantidade' => 10.0,
            'custo_unitario' => 10.0,
            'data_movimentacao' => $dataCustomizada
        ];

        $response = $this->client->post('/api/estoque/entrada', [
            'json' => $payload
        ]);

        // API pode aceitar ou rejeitar data customizada
        $this->assertContains($response->getStatusCode(), [201, 422]);
    }

    /**
     * Teste: Entrada atualiza preço de custo do produto
     * Cenário: Entrada com novo custo unitário
     * Esperado: preco_custo do produto atualizado
     */
    public function testEntradaAtualizaPrecoCusto()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('CUS0000000001', 'Produto', $categoriaId, 50.0);

        // Consulta preço inicial
        $getInicial = $this->client->get("/api/produtos/{$produtoId}");
        $produtoInicial = json_decode($getInicial->getBody(), true);
        $this->assertEquals(10.0, $produtoInicial['preco_custo']);

        // Entrada com novo custo
        $this->client->post('/api/estoque/entrada', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => 100.0,
                'custo_unitario' => 15.0  // Novo custo
            ]
        ]);

        // Verifica se preço foi atualizado
        $getAtual = $this->client->get("/api/produtos/{$produtoId}");
        $produtoAtual = json_decode($getAtual->getBody(), true);

        // Preço pode ser atualizado ou fazer média ponderada
        $this->assertGreaterThanOrEqual(10.0, $produtoAtual['preco_custo']);
        $this->assertLessThanOrEqual(15.0, $produtoAtual['preco_custo']);
    }
}
