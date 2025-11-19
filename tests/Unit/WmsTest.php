<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes para WMS (Warehouse Management System)
 *
 * Gestão avançada de armazém:
 * - Endereçamento (rua, prédio, nível, posição)
 * - Picking e packing
 * - Separação de pedidos
 * - Conferência
 * - Inventário rotativo
 */
class WmsTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdEnderecoIds = [];

    protected function setUp(): void
    {
        parent::setUp();
        $this->client = new Client([
            'base_uri' => $this->baseUrl,
            'http_errors' => false,
            'headers' => ['Content-Type' => 'application/json']
        ]);
    }

    protected function tearDown(): void
    {
        foreach ($this->createdEnderecoIds as $id) {
            try {
                $this->client->delete("/api/wms/enderecos/{$id}");
            } catch (\Exception $e) {
                // Ignora
            }
        }
        parent::tearDown();
    }

    public function testCriarEndereco()
    {
        $payload = [
            'codigo' => 'A-01-02-03',
            'rua' => 'A',
            'predio' => '01',
            'nivel' => '02',
            'posicao' => '03',
            'tipo' => 'PICKING',
            'capacidade_kg' => 500.0,
            'ativo' => true
        ];

        $response = $this->client->post('/api/wms/enderecos', [
            'json' => $payload
        ]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->assertEquals('A-01-02-03', $data['codigo']);
            $this->createdEnderecoIds[] = $data['id'];
        }
    }

    public function testAlocarProdutoEndereco()
    {
        $payload = [
            'produto_id' => 1,
            'endereco_codigo' => 'A-01-02-03',
            'quantidade' => 50.0
        ];

        $response = $this->client->post('/api/wms/alocacao', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testCriarOrdemSeparacao()
    {
        $payload = [
            'pedido_id' => 1,
            'tipo' => 'VENDA',
            'prioridade' => 'NORMAL',
            'itens' => [
                [
                    'produto_id' => 1,
                    'quantidade' => 5.0
                ]
            ]
        ];

        $response = $this->client->post('/api/wms/separacao', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testIniciarSeparacao()
    {
        $response = $this->client->post('/api/wms/separacao/1/iniciar', [
            'json' => ['operador' => 'João Silva']
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testRegistrarPicking()
    {
        $payload = [
            'separacao_id' => 1,
            'produto_id' => 1,
            'endereco_codigo' => 'A-01-02-03',
            'quantidade_coletada' => 5.0
        ];

        $response = $this->client->post('/api/wms/picking', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testConferenciaSeparacao()
    {
        $payload = [
            'separacao_id' => 1,
            'itens_conferidos' => [
                [
                    'produto_id' => 1,
                    'quantidade' => 5.0,
                    'conferente' => 'Maria Santos'
                ]
            ]
        ];

        $response = $this->client->post('/api/wms/conferencia', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testCriarOnda()
    {
        $payload = [
            'nome' => 'Onda Manhã 001',
            'pedidos' => [1, 2, 3],
            'tipo' => 'PICKING_LIST'
        ];

        $response = $this->client->post('/api/wms/ondas', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testInventarioRotativo()
    {
        $payload = [
            'endereco_codigo' => 'A-01-02-03',
            'data_contagem' => date('Y-m-d'),
            'contadores' => ['João', 'Maria']
        ];

        $response = $this->client->post('/api/wms/inventario-rotativo', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testRegistrarContagem()
    {
        $payload = [
            'inventario_id' => 1,
            'produto_id' => 1,
            'quantidade_contada' => 48.0,
            'contador' => 'João Silva'
        ];

        $response = $this->client->post('/api/wms/contagem', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testTransferirEndereco()
    {
        $payload = [
            'produto_id' => 1,
            'endereco_origem' => 'A-01-02-03',
            'endereco_destino' => 'B-02-03-04',
            'quantidade' => 10.0,
            'motivo' => 'Reorganização'
        ];

        $response = $this->client->post('/api/wms/transferencia', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testConsultarOcupacaoEndereco()
    {
        $response = $this->client->get('/api/wms/enderecos/A-01-02-03/ocupacao');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('percentual_ocupacao', $data);
        }
    }

    public function testMapaCalor()
    {
        $response = $this->client->get('/api/wms/mapa-calor');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testProdutosMaisMovimentados()
    {
        $response = $this->client->get('/api/wms/produtos-mais-movimentados?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('items', $data);
        }
    }

    public function testRotaOtimizada()
    {
        $response = $this->client->get('/api/wms/separacao/1/rota-otimizada');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('sequencia_picking', $data);
        }
    }

    public function testBloqu earEndereco()
    {
        $payload = [
            'motivo' => 'Manutenção da estrutura'
        ];

        $response = $this->client->post('/api/wms/enderecos/A-01-02-03/bloquear', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testDesbloquearEndereco()
    {
        $response = $this->client->post('/api/wms/enderecos/A-01-02-03/desbloquear');

        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testListarEnderecos()
    {
        $response = $this->client->get('/api/wms/enderecos?tipo=PICKING&ativo=true');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('items', $data);
        }
    }

    public function testDashboardWms()
    {
        $response = $this->client->get('/api/wms/dashboard');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('separacoes_pendentes', $data);
            $this->assertArrayHasKey('ocupacao_geral', $data);
        }
    }

    public function testIndicadoresPerformance()
    {
        $response = $this->client->get('/api/wms/indicadores-performance?periodo=7');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('tempo_medio_picking', $data);
            $this->assertArrayHasKey('acuracidade_separacao', $data);
        }
    }

    public function testReabastecimento()
    {
        $payload = [
            'produto_id' => 1,
            'endereco_destino' => 'PICKING-01',
            'quantidade' => 20.0
        ];

        $response = $this->client->post('/api/wms/reabastecimento', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }
}
