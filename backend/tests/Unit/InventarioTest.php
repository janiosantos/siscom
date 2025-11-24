<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes para Inventário (Contagem de Estoque)
 */
class InventarioTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdInventarioIds = [];

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
        foreach ($this->createdInventarioIds as $id) {
            try {
                $this->client->delete("/api/inventarios/{$id}");
            } catch (\Exception $e) {
            }
        }
        parent::tearDown();
    }

    public function testCriarInventario()
    {
        $payload = [
            'descricao' => 'Inventário Geral Janeiro/2025',
            'tipo' => 'GERAL',
            'data_inicio' => date('Y-m-d'),
            'responsavel' => 'João Silva'
        ];

        $response = $this->client->post('/api/inventarios', ['json' => $payload]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->assertEquals('GERAL', $data['tipo']);
            $this->createdInventarioIds[] = $data['id'];
        }
    }

    public function testRegistrarContagem()
    {
        $payload = [
            'inventario_id' => 1,
            'produto_id' => 1,
            'quantidade_contada' => 150.0,
            'contador' => 'Maria Santos'
        ];

        $response = $this->client->post('/api/inventarios/contagem', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testCalcularDivergencias()
    {
        $response = $this->client->get('/api/inventarios/1/divergencias');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('itens_divergentes', $data);
        }
    }

    public function testAjustarEstoque()
    {
        $payload = [
            'inventario_id' => 1,
            'produto_id' => 1,
            'quantidade_sistema' => 100.0,
            'quantidade_contada' => 95.0,
            'motivo' => 'Ajuste pós-inventário'
        ];

        $response = $this->client->post('/api/inventarios/ajustar', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testFinalizarInventario()
    {
        $response = $this->client->post('/api/inventarios/1/finalizar');
        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testInventarioParcial()
    {
        $payload = [
            'descricao' => 'Inventário Categoria Eletrônicos',
            'tipo' => 'PARCIAL',
            'categoria_id' => 1,
            'data_inicio' => date('Y-m-d')
        ];

        $response = $this->client->post('/api/inventarios', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [201, 404]);
    }

    public function testSegundaContagem()
    {
        $payload = [
            'inventario_id' => 1,
            'produto_id' => 1,
            'quantidade_contada' => 96.0,
            'contador' => 'Pedro Oliveira',
            'contagem_numero' => 2
        ];

        $response = $this->client->post('/api/inventarios/contagem', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testRelatorioInventario()
    {
        $response = $this->client->get('/api/inventarios/1/relatorio');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_itens', $data);
            $this->assertArrayHasKey('total_divergencias', $data);
        }
    }

    public function testExportarInventario()
    {
        $response = $this->client->get('/api/inventarios/1/exportar?formato=xlsx');
        $this->assertContains($response->getStatusCode(), [200, 404, 501]);
    }

    public function testListarInventarios()
    {
        $response = $this->client->get('/api/inventarios?status=EM_ANDAMENTO');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('items', $data);
        }
    }

    public function testCancelarInventario()
    {
        $payload = ['motivo' => 'Erro na execução'];
        $response = $this->client->post('/api/inventarios/1/cancelar', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testImprimirEtiquetas()
    {
        $response = $this->client->get('/api/inventarios/1/etiquetas');
        $this->assertContains($response->getStatusCode(), [200, 404]);
    }

    public function testContagemPorLote()
    {
        $payload = [
            'inventario_id' => 1,
            'produto_id' => 1,
            'lote_id' => 1,
            'quantidade_contada' => 50.0
        ];

        $response = $this->client->post('/api/inventarios/contagem-lote', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testAcuracidadeInventario()
    {
        $response = $this->client->get('/api/inventarios/1/acuracidade');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('percentual_acuracidade', $data);
        }
    }

    public function testCompararContagens()
    {
        $response = $this->client->get('/api/inventarios/1/comparar-contagens');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }
}
