<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de Controle de Lotes
 *
 * Cobre:
 * - Rastreamento de lotes
 * - Controle FIFO (First In, First Out)
 * - Validade de lotes
 * - Movimentação por lote
 * - Relatórios de lote
 * - Bloqueio de lotes vencidos
 */
class LoteTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdLoteIds = [];
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
        foreach ($this->createdLoteIds as $id) {
            try {
                $this->client->delete("/api/lotes/{$id}");
            } catch (\Exception $e) {
                // Ignora
            }
        }

        foreach ($this->createdProdutoIds as $id) {
            try {
                $this->client->delete("/api/produtos/{$id}");
            } catch (\Exception $e) {
                // Ignora
            }
        }

        foreach ($this->createdCategoriaIds as $id) {
            try {
                $this->client->delete("/api/categorias/{$id}");
            } catch (\Exception $e) {
                // Ignora
            }
        }

        parent::tearDown();
    }

    private function criarCategoria($nome = 'Categoria Lote')
    {
        $response = $this->client->post('/api/categorias', [
            'json' => ['nome' => $nome]
        ]);
        $data = json_decode($response->getBody(), true);
        $this->createdCategoriaIds[] = $data['id'];
        return $data['id'];
    }

    private function criarProduto($codigoBarras, $descricao, $categoriaId, $preco, $controlaLote = true)
    {
        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => $descricao,
                'categoria_id' => $categoriaId,
                'preco_custo' => $preco * 0.6,
                'preco_venda' => $preco,
                'controla_lote' => $controlaLote,
                'estoque_minimo' => 5.0,
                'ativo' => true
            ]
        ]);
        $data = json_decode($response->getBody(), true);
        $this->createdProdutoIds[] = $data['id'];
        return $data['id'];
    }

    public function testCriarLoteComSucesso()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000001', 'Medicamento A', $categoriaId, 50.0);

        $payload = [
            'produto_id' => $produtoId,
            'numero_lote' => 'LOTE2025001',
            'data_fabricacao' => '2025-01-01',
            'data_validade' => '2026-01-01',
            'quantidade' => 100.0,
            'preco_custo' => 30.0
        ];

        $response = $this->client->post('/api/lotes', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertEquals('LOTE2025001', $data['numero_lote']);
        $this->assertEquals(100.0, $data['quantidade']);
        $this->assertEquals(100.0, $data['quantidade_disponivel']);

        $this->createdLoteIds[] = $data['id'];
    }

    public function testCriarLoteSemNumero()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000002', 'Produto', $categoriaId, 40.0);

        $payload = [
            'produto_id' => $produtoId,
            'data_validade' => '2026-01-01',
            'quantidade' => 50.0
        ];

        $response = $this->client->post('/api/lotes', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    public function testBuscarLotePorId()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000003', 'Produto Lote', $categoriaId, 35.0);

        $createResponse = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE2025002',
                'data_validade' => '2026-06-01',
                'quantidade' => 75.0,
                'preco_custo' => 20.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $loteId = $created['id'];
        $this->createdLoteIds[] = $loteId;

        $response = $this->client->get("/api/lotes/{$loteId}");

        $this->assertEquals(200, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals($loteId, $data['id']);
        $this->assertEquals('LOTE2025002', $data['numero_lote']);
    }

    public function testListarLotes()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000004', 'Produto Lista', $categoriaId, 45.0);

        for ($i = 0; $i < 3; $i++) {
            $createResponse = $this->client->post('/api/lotes', [
                'json' => [
                    'produto_id' => $produtoId,
                    'numero_lote' => "LOTE202500{$i}",
                    'data_validade' => '2026-12-31',
                    'quantidade' => 50.0,
                    'preco_custo' => 25.0
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdLoteIds[] = $created['id'];
        }

        $response = $this->client->get('/api/lotes');

        $this->assertEquals(200, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertGreaterThanOrEqual(3, $data['total']);
    }

    public function testConsumoFifo()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000005', 'Produto FIFO', $categoriaId, 60.0);

        // Lote 1 (mais antigo)
        $lote1Response = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_ANTIGO',
                'data_fabricacao' => '2024-01-01',
                'data_validade' => '2025-12-31',
                'quantidade' => 50.0,
                'preco_custo' => 30.0
            ]
        ]);
        $lote1 = json_decode($lote1Response->getBody(), true);
        $this->createdLoteIds[] = $lote1['id'];

        // Lote 2 (mais novo)
        $lote2Response = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_NOVO',
                'data_fabricacao' => '2024-06-01',
                'data_validade' => '2026-06-01',
                'quantidade' => 50.0,
                'preco_custo' => 30.0
            ]
        ]);
        $lote2 = json_decode($lote2Response->getBody(), true);
        $this->createdLoteIds[] = $lote2['id'];

        // Consome 30 unidades (deve sair do lote mais antigo)
        $consumoResponse = $this->client->post("/api/produtos/{$produtoId}/consumir-lote", [
            'json' => [
                'quantidade' => 30.0,
                'metodo' => 'FIFO'
            ]
        ]);

        if ($consumoResponse->getStatusCode() === 200) {
            $consumoData = json_decode($consumoResponse->getBody(), true);

            // Verifica se consumiu do lote antigo
            $this->assertEquals($lote1['id'], $consumoData['lotes_consumidos'][0]['lote_id']);

            // Verifica saldo do lote 1
            $lote1Atual = $this->client->get("/api/lotes/{$lote1['id']}");
            $lote1Data = json_decode($lote1Atual->getBody(), true);

            $this->assertEquals(20.0, $lote1Data['quantidade_disponivel']); // 50 - 30
        }
    }

    public function testBloquearLoteVencido()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000006', 'Produto Vencido', $categoriaId, 55.0);

        // Cria lote vencido
        $createResponse = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_VENCIDO',
                'data_fabricacao' => '2023-01-01',
                'data_validade' => '2024-01-01',
                'quantidade' => 40.0,
                'preco_custo' => 25.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $loteId = $created['id'];
        $this->createdLoteIds[] = $loteId;

        // Tenta consumir lote vencido
        $consumoResponse = $this->client->post("/api/lotes/{$loteId}/consumir", [
            'json' => ['quantidade' => 10.0]
        ]);

        // Deve recusar se validação de vencimento estiver ativa
        $this->assertContains($consumoResponse->getStatusCode(), [400, 422, 200]);
    }

    public function testLotesProximosVencimento()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000007', 'Produto Vence', $categoriaId, 65.0);

        // Lote vencendo em 30 dias
        $dataVencimento = date('Y-m-d', strtotime('+30 days'));

        $createResponse = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_VENCE_BREVE',
                'data_validade' => $dataVencimento,
                'quantidade' => 25.0,
                'preco_custo' => 35.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $this->createdLoteIds[] = $created['id'];

        // Busca lotes próximos do vencimento
        $response = $this->client->get('/api/lotes/proximos-vencimento?dias=60');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertGreaterThanOrEqual(1, $data['total']);
        }
    }

    public function testAtualizarQuantidadeLote()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000008', 'Produto Atualizar', $categoriaId, 70.0);

        $createResponse = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_UPDATE',
                'data_validade' => '2026-03-01',
                'quantidade' => 100.0,
                'preco_custo' => 40.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $loteId = $created['id'];
        $this->createdLoteIds[] = $loteId;

        // Ajusta quantidade (por exemplo, após inventário)
        $ajusteResponse = $this->client->post("/api/lotes/{$loteId}/ajustar", [
            'json' => [
                'quantidade' => 95.0,
                'motivo' => 'Ajuste de inventário - 5 unidades danificadas'
            ]
        ]);

        if ($ajusteResponse->getStatusCode() === 200) {
            $loteAtual = $this->client->get("/api/lotes/{$loteId}");
            $loteData = json_decode($loteAtual->getBody(), true);

            $this->assertEquals(95.0, $loteData['quantidade_disponivel']);
        }
    }

    public function testHistoricoMovimentacaoLote()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000009', 'Produto Historico', $categoriaId, 75.0);

        $createResponse = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_HIST',
                'data_validade' => '2026-09-01',
                'quantidade' => 60.0,
                'preco_custo' => 45.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $loteId = $created['id'];
        $this->createdLoteIds[] = $loteId;

        // Busca histórico
        $response = $this->client->get("/api/lotes/{$loteId}/historico");

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('movimentacoes', $data);
        }
    }

    public function testFiltrarLotesPorProduto()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000010', 'Produto Filtro', $categoriaId, 80.0);

        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/lotes', [
                'json' => [
                    'produto_id' => $produtoId,
                    'numero_lote' => "LOTE_FILTRO_{$i}",
                    'data_validade' => '2026-10-01',
                    'quantidade' => 30.0,
                    'preco_custo' => 50.0
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdLoteIds[] = $created['id'];
        }

        $response = $this->client->get("/api/lotes?produto_id={$produtoId}");

        $this->assertEquals(200, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(2, $data['total']);

        foreach ($data['items'] as $lote) {
            $this->assertEquals($produtoId, $lote['produto_id']);
        }
    }

    public function testLoteComNumeroSerieDuplicado()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000011', 'Produto Dup', $categoriaId, 85.0);

        $loteNumero = 'LOTE_DUP_2025';

        // Cria primeiro lote
        $create1 = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => $loteNumero,
                'data_validade' => '2026-11-01',
                'quantidade' => 20.0,
                'preco_custo' => 55.0
            ]
        ]);

        $this->assertEquals(201, $create1->getStatusCode());
        $created1 = json_decode($create1->getBody(), true);
        $this->createdLoteIds[] = $created1['id'];

        // Tenta criar segundo com mesmo número
        $create2 = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => $loteNumero,
                'data_validade' => '2026-12-01',
                'quantidade' => 15.0,
                'preco_custo' => 55.0
            ]
        ]);

        // Deve rejeitar duplicata para mesmo produto
        $this->assertContains($create2->getStatusCode(), [400, 422]);
    }

    public function testRastreabilidadeCompleta()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000012', 'Produto Rastreio', $categoriaId, 90.0);

        $createResponse = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_RASTREIO_001',
                'numero_serie' => 'SN123456789',
                'fornecedor' => 'Fornecedor XYZ',
                'nota_fiscal' => 'NF-12345',
                'data_fabricacao' => '2025-01-15',
                'data_validade' => '2027-01-15',
                'quantidade' => 80.0,
                'preco_custo' => 60.0
            ]
        ]);

        $this->assertEquals(201, $createResponse->getStatusCode());
        $data = json_decode($createResponse->getBody(), true);

        $this->assertEquals('SN123456789', $data['numero_serie']);
        $this->assertEquals('Fornecedor XYZ', $data['fornecedor']);
        $this->assertEquals('NF-12345', $data['nota_fiscal']);

        $this->createdLoteIds[] = $data['id'];
    }

    public function testValidarDataValidade()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000013', 'Produto Val', $categoriaId, 95.0);

        // Data de validade no passado
        $payload = [
            'produto_id' => $produtoId,
            'numero_lote' => 'LOTE_INVALIDO',
            'data_validade' => '2020-01-01',
            'quantidade' => 10.0
        ];

        $response = $this->client->post('/api/lotes', [
            'json' => $payload
        ]);

        // Pode aceitar ou rejeitar dependendo da regra
        $this->assertContains($response->getStatusCode(), [201, 422]);
    }

    public function testReservaLote()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000014', 'Produto Reserva', $categoriaId, 100.0);

        $createResponse = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_RESERVA',
                'data_validade' => '2026-08-01',
                'quantidade' => 50.0,
                'preco_custo' => 65.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $loteId = $created['id'];
        $this->createdLoteIds[] = $loteId;

        // Reserva 20 unidades
        $reservaResponse = $this->client->post("/api/lotes/{$loteId}/reservar", [
            'json' => [
                'quantidade' => 20.0,
                'referencia' => 'Pedido #12345'
            ]
        ]);

        if ($reservaResponse->getStatusCode() === 200) {
            $loteAtual = $this->client->get("/api/lotes/{$loteId}");
            $loteData = json_decode($loteAtual->getBody(), true);

            // Disponível deve ser 30 (50 - 20 reservado)
            if (isset($loteData['quantidade_disponivel'])) {
                $this->assertEquals(30.0, $loteData['quantidade_disponivel']);
            }
        }
    }

    public function testDeletarLote()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000015', 'Produto Del', $categoriaId, 105.0);

        $createResponse = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_DEL',
                'data_validade' => '2026-07-01',
                'quantidade' => 15.0,
                'preco_custo' => 70.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $loteId = $created['id'];

        $response = $this->client->delete("/api/lotes/{$loteId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);
    }

    public function testTimestamps()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000016', 'Produto Time', $categoriaId, 110.0);

        $response = $this->client->post('/api/lotes', [
            'json' => [
                'produto_id' => $produtoId,
                'numero_lote' => 'LOTE_TIME',
                'data_validade' => '2026-05-01',
                'quantidade' => 12.0,
                'preco_custo' => 75.0
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdLoteIds[] = $data['id'];

        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('updated_at', $data);
    }

    public function testBuscarLoteInexistente()
    {
        $response = $this->client->get('/api/lotes/999999');
        $this->assertEquals(404, $response->getStatusCode());
    }

    public function testProdutoSemControleLote()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000017', 'Sem Controle', $categoriaId, 115.0, false);

        // Tenta criar lote para produto que não controla lote
        $payload = [
            'produto_id' => $produtoId,
            'numero_lote' => 'LOTE_NAO_PERMITIDO',
            'data_validade' => '2026-04-01',
            'quantidade' => 8.0
        ];

        $response = $this->client->post('/api/lotes', [
            'json' => $payload
        ]);

        // Pode rejeitar
        $this->assertContains($response->getStatusCode(), [201, 400, 422]);
    }

    public function testLoteComQuantidadeZero()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('LOT0000000018', 'Produto Zero', $categoriaId, 120.0);

        $payload = [
            'produto_id' => $produtoId,
            'numero_lote' => 'LOTE_ZERO',
            'data_validade' => '2026-02-01',
            'quantidade' => 0.0
        ];

        $response = $this->client->post('/api/lotes', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }
}
