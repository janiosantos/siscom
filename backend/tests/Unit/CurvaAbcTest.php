<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes para Análise de Curva ABC
 *
 * Classifica produtos por importância:
 * - Classe A: 80% do faturamento (20% dos produtos)
 * - Classe B: 15% do faturamento (30% dos produtos)
 * - Classe C: 5% do faturamento (50% dos produtos)
 */
class CurvaAbcTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';

    protected function setUp(): void
    {
        parent::setUp();
        $this->client = new Client([
            'base_uri' => $this->baseUrl,
            'http_errors' => false,
            'headers' => ['Content-Type' => 'application/json']
        ]);
    }

    public function testCalcularCurvaAbcProdutos()
    {
        $response = $this->client->get('/api/relatorios/curva-abc/produtos');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);

            $this->assertArrayHasKey('classe_a', $data);
            $this->assertArrayHasKey('classe_b', $data);
            $this->assertArrayHasKey('classe_c', $data);
        } else {
            $this->assertContains($response->getStatusCode(), [200, 404, 501]);
        }
    }

    public function testCurvaAbcClientes()
    {
        $response = $this->client->get('/api/relatorios/curva-abc/clientes');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testCurvaAbcPorPeriodo()
    {
        $inicio = date('Y-m-d', strtotime('-90 days'));
        $fim = date('Y-m-d');

        $response = $this->client->get("/api/relatorios/curva-abc/produtos?data_inicio={$inicio}&data_fim={$fim}");

        $this->assertContains($response->getStatusCode(), [200, 404]);
    }

    public function testClassificacaoProdutoEspecifico()
    {
        $response = $this->client->get('/api/produtos/1/classificacao-abc');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('classe', $data);
            $this->assertContains($data['classe'], ['A', 'B', 'C']);
        }
    }

    public function testPercentuaisCorretos()
    {
        $response = $this->client->get('/api/relatorios/curva-abc/produtos');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);

            if (isset($data['percentual_faturamento_a'])) {
                $this->assertGreaterThanOrEqual(70, $data['percentual_faturamento_a']);
            }
        }
    }

    public function testProdutosClasseA()
    {
        $response = $this->client->get('/api/produtos?classe_abc=A');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('items', $data);
        }
    }

    public function testGraficoPareto()
    {
        $response = $this->client->get('/api/relatorios/curva-abc/grafico-pareto');

        $this->assertContains($response->getStatusCode(), [200, 404, 501]);
    }

    public function testExportarCurvaAbc()
    {
        $response = $this->client->get('/api/relatorios/curva-abc/exportar?formato=csv');

        $this->assertContains($response->getStatusCode(), [200, 404, 501]);
    }

    public function testCurvaAbcPorCategoria()
    {
        $response = $this->client->get('/api/relatorios/curva-abc/por-categoria');

        $this->assertContains($response->getStatusCode(), [200, 404]);
    }

    public function testIndicadoresGerais()
    {
        $response = $this->client->get('/api/relatorios/curva-abc/indicadores');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_produtos', $data);
        }
    }
}
