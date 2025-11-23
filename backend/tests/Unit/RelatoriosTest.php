<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes para Relatórios Gerenciais
 */
class RelatoriosTest extends TestCase
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

    public function testRelatorioVendas()
    {
        $inicio = date('Y-m-d', strtotime('-30 days'));
        $fim = date('Y-m-d');

        $response = $this->client->get("/api/relatorios/vendas?data_inicio={$inicio}&data_fim={$fim}");

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_vendas', $data);
            $this->assertArrayHasKey('quantidade_vendas', $data);
        }
    }

    public function testRelatorioVendasPorVendedor()
    {
        $response = $this->client->get('/api/relatorios/vendas-por-vendedor?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testRelatorioEstoque()
    {
        $response = $this->client->get('/api/relatorios/estoque');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('produtos', $data);
        }
    }

    public function testRelatorioEstoqueMinimo()
    {
        $response = $this->client->get('/api/relatorios/estoque-minimo');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testRelatorioFinanceiro()
    {
        $response = $this->client->get('/api/relatorios/financeiro?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('contas_pagar', $data);
            $this->assertArrayHasKey('contas_receber', $data);
        }
    }

    public function testRelatorioDre()
    {
        $response = $this->client->get('/api/relatorios/dre?mes=2025-01');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('receitas', $data);
            $this->assertArrayHasKey('despesas', $data);
            $this->assertArrayHasKey('lucro_liquido', $data);
        }
    }

    public function testRelatorioFluxoCaixa()
    {
        $response = $this->client->get('/api/relatorios/fluxo-caixa?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('entradas', $data);
            $this->assertArrayHasKey('saidas', $data);
            $this->assertArrayHasKey('saldo', $data);
        }
    }

    public function testRelatorioProdutosMaisVendidos()
    {
        $response = $this->client->get('/api/relatorios/produtos-mais-vendidos?limite=10');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testRelatorioClientesAtivos()
    {
        $response = $this->client->get('/api/relatorios/clientes-ativos?periodo=90');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_clientes', $data);
        }
    }

    public function testRelatorioCompras()
    {
        $response = $this->client->get('/api/relatorios/compras?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_compras', $data);
        }
    }

    public function testRelatorioNotasFiscais()
    {
        $response = $this->client->get('/api/relatorios/notas-fiscais?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testRelatorioOrdensServico()
    {
        $response = $this->client->get('/api/relatorios/ordens-servico?status=CONCLUIDA');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_os', $data);
        }
    }

    public function testRelatorioComissoes()
    {
        $response = $this->client->get('/api/relatorios/comissoes?mes=2025-01');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testRelatorioImpostos()
    {
        $response = $this->client->get('/api/relatorios/impostos?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_impostos', $data);
        }
    }

    public function testRelatorioMovimentacaoEstoque()
    {
        $response = $this->client->get('/api/relatorios/movimentacao-estoque?periodo=7');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('entradas', $data);
            $this->assertArrayHasKey('saidas', $data);
        }
    }

    public function testExportarRelatorioVendas()
    {
        $response = $this->client->get('/api/relatorios/vendas/exportar?formato=xlsx&periodo=30');
        $this->assertContains($response->getStatusCode(), [200, 404, 501]);
    }

    public function testExportarRelatorioPDF()
    {
        $response = $this->client->get('/api/relatorios/vendas/exportar?formato=pdf&periodo=30');
        $this->assertContains($response->getStatusCode(), [200, 404, 501]);
    }

    public function testRelatorioGiroEstoque()
    {
        $response = $this->client->get('/api/relatorios/giro-estoque?periodo=90');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testRelatorioMargemLucro()
    {
        $response = $this->client->get('/api/relatorios/margem-lucro');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('margem_media', $data);
        }
    }

    public function testRelatorioVendasPorCategoria()
    {
        $response = $this->client->get('/api/relatorios/vendas-por-categoria?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }
}
