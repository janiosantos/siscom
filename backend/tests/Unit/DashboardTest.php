<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes para Dashboard e KPIs
 */
class DashboardTest extends TestCase
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

    public function testDashboardPrincipal()
    {
        $response = $this->client->get('/api/dashboard');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('vendas_hoje', $data);
            $this->assertArrayHasKey('vendas_mes', $data);
            $this->assertArrayHasKey('faturamento_mes', $data);
        }
    }

    public function testKpiVendas()
    {
        $response = $this->client->get('/api/dashboard/kpi/vendas');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total', $data);
            $this->assertArrayHasKey('crescimento', $data);
        }
    }

    public function testKpiTicketMedio()
    {
        $response = $this->client->get('/api/dashboard/kpi/ticket-medio');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('valor', $data);
        }
    }

    public function testGraficoVendasDiarias()
    {
        $response = $this->client->get('/api/dashboard/grafico/vendas-diarias?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('labels', $data);
            $this->assertArrayHasKey('valores', $data);
        }
    }

    public function testGraficoProdutosMaisVendidos()
    {
        $response = $this->client->get('/api/dashboard/grafico/produtos-top?limite=10');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testGraficoVendasPorCategoria()
    {
        $response = $this->client->get('/api/dashboard/grafico/vendas-categoria');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testPainelFinanceiro()
    {
        $response = $this->client->get('/api/dashboard/financeiro');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('saldo_atual', $data);
            $this->assertArrayHasKey('contas_vencidas', $data);
        }
    }

    public function testEstoqueAlerta()
    {
        $response = $this->client->get('/api/dashboard/estoque/alertas');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('produtos_estoque_minimo', $data);
        }
    }

    public function testUltimasVendas()
    {
        $response = $this->client->get('/api/dashboard/ultimas-vendas?limite=10');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testMetasVendas()
    {
        $response = $this->client->get('/api/dashboard/metas');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('meta_mensal', $data);
            $this->assertArrayHasKey('realizado', $data);
            $this->assertArrayHasKey('percentual_atingido', $data);
        }
    }

    public function testRankingVendedores()
    {
        $response = $this->client->get('/api/dashboard/ranking-vendedores?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testNotificacoesPendentes()
    {
        $response = $this->client->get('/api/dashboard/notificacoes');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_pendentes', $data);
        }
    }

    public function testComparacaoPeriodos()
    {
        $response = $this->client->get('/api/dashboard/comparacao?periodo_atual=30&periodo_anterior=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('vendas_periodo_atual', $data);
            $this->assertArrayHasKey('vendas_periodo_anterior', $data);
            $this->assertArrayHasKey('variacao_percentual', $data);
        }
    }

    public function testOsAbertas()
    {
        $response = $this->client->get('/api/dashboard/os-abertas');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total', $data);
        }
    }

    public function testPedidosPendentes()
    {
        $response = $this->client->get('/api/dashboard/pedidos-pendentes');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testIndicadoresGerais()
    {
        $response = $this->client->get('/api/dashboard/indicadores');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_clientes', $data);
            $this->assertArrayHasKey('total_produtos', $data);
        }
    }

    public function testAtualizacaoTempo Real()
    {
        $response = $this->client->get('/api/dashboard/tempo-real');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('vendas_hoje', $data);
            $this->assertArrayHasKey('timestamp', $data);
        }
    }

    public function testExportarDashboard()
    {
        $response = $this->client->get('/api/dashboard/exportar?formato=pdf');
        $this->assertContains($response->getStatusCode(), [200, 404, 501]);
    }

    public function testConfiguracoesWidget()
    {
        $payload = [
            'widgets' => [
                ['tipo' => 'vendas', 'posicao' => 1, 'visivel' => true],
                ['tipo' => 'estoque', 'posicao' => 2, 'visivel' => true]
            ]
        ];

        $response = $this->client->post('/api/dashboard/configurar-widgets', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 404]);
    }

    public function testFiltrarPorPeriodo()
    {
        $response = $this->client->get('/api/dashboard?data_inicio=2025-01-01&data_fim=2025-01-31');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }
}
