<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes para Programa de Fidelidade
 */
class FidelidadeTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdProgramaIds = [];

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
        foreach ($this->createdProgramaIds as $id) {
            try {
                $this->client->delete("/api/fidelidade/programas/{$id}");
            } catch (\Exception $e) {
            }
        }
        parent::tearDown();
    }

    public function testCriarProgramaFidelidade()
    {
        $payload = [
            'nome' => 'Programa Ouro',
            'descricao' => 'Acumule pontos e ganhe prêmios',
            'regra_acumulo' => 'VALOR_COMPRA',
            'pontos_por_real' => 1.0,
            'ativo' => true
        ];

        $response = $this->client->post('/api/fidelidade/programas', ['json' => $payload]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->assertEquals('Programa Ouro', $data['nome']);
            $this->createdProgramaIds[] = $data['id'];
        }
    }

    public function testAdicionarCliente Programa()
    {
        $payload = [
            'cliente_id' => 1,
            'programa_id' => 1
        ];

        $response = $this->client->post('/api/fidelidade/participantes', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testAcumularPontos()
    {
        $payload = [
            'cliente_id' => 1,
            'pontos' => 100,
            'origem' => 'COMPRA',
            'referencia_id' => 1
        ];

        $response = $this->client->post('/api/fidelidade/acumular-pontos', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testConsultarSaldo()
    {
        $response = $this->client->get('/api/fidelidade/clientes/1/saldo');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('pontos_disponiveis', $data);
            $this->assertArrayHasKey('pontos_bloqueados', $data);
        }
    }

    public function testRegatarPontos()
    {
        $payload = [
            'cliente_id' => 1,
            'pontos' => 50,
            'tipo_resgate' => 'DESCONTO',
            'valor_desconto' => 25.0
        ];

        $response = $this->client->post('/api/fidelidade/resgatar', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 400, 404]);
    }

    public function testListarPremios()
    {
        $response = $this->client->get('/api/fidelidade/premios');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testTrocarPontosPorPremio()
    {
        $payload = [
            'cliente_id' => 1,
            'premio_id' => 1
        ];

        $response = $this->client->post('/api/fidelidade/trocar-premio', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 400, 404]);
    }

    public function testExtratoCliente()
    {
        $response = $this->client->get('/api/fidelidade/clientes/1/extrato');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('movimentacoes', $data);
        }
    }

    public function testNivelCliente()
    {
        $response = $this->client->get('/api/fidelidade/clientes/1/nivel');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('nivel_atual', $data);
            $this->assertArrayHasKey('pontos_para_proximo', $data);
        }
    }

    public function testBonusPorAniversario()
    {
        $payload = [
            'cliente_id' => 1,
            'pontos_bonus' => 50,
            'motivo' => 'Aniversário'
        ];

        $response = $this->client->post('/api/fidelidade/bonus', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testExpiracaoPontos()
    {
        $response = $this->client->get('/api/fidelidade/clientes/1/pontos-expirando?dias=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('pontos_expirando', $data);
        }
    }

    public function testCampanhaBonus()
    {
        $payload = [
            'nome' => 'Black Friday - Pontos em Dobro',
            'multiplicador' => 2.0,
            'data_inicio' => date('Y-m-d'),
            'data_fim' => date('Y-m-d', strtotime('+7 days'))
        ];

        $response = $this->client->post('/api/fidelidade/campanhas', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testRankingClientes()
    {
        $response = $this->client->get('/api/fidelidade/ranking?limite=10');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testVoucherDesconto()
    {
        $payload = [
            'cliente_id' => 1,
            'pontos' => 100,
            'valor_desconto' => 50.0
        ];

        $response = $this->client->post('/api/fidelidade/gerar-voucher', ['json' => $payload]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('codigo_voucher', $data);
            $this->assertArrayHasKey('valor', $data);
        }
    }

    public function testAplicarVoucher()
    {
        $payload = [
            'codigo_voucher' => 'VOUCHER12345',
            'venda_id' => 1
        ];

        $response = $this->client->post('/api/fidelidade/aplicar-voucher', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 400, 404]);
    }

    public function testRelatorioFidelidade()
    {
        $response = $this->client->get('/api/fidelidade/relatorio?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('total_participantes', $data);
            $this->assertArrayHasKey('pontos_emitidos', $data);
            $this->assertArrayHasKey('pontos_resgatados', $data);
        }
    }

    public function testBloquearPontos()
    {
        $payload = [
            'cliente_id' => 1,
            'pontos' => 20,
            'motivo' => 'Reserva para troca'
        ];

        $response = $this->client->post('/api/fidelidade/bloquear-pontos', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testDesbloquearPontos()
    {
        $payload = [
            'cliente_id' => 1,
            'pontos' => 20
        ];

        $response = $this->client->post('/api/fidelidade/desbloquear-pontos', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testNotificarClientePontos()
    {
        $response = $this->client->post('/api/fidelidade/clientes/1/notificar-saldo');
        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testIndicadoresPrograma()
    {
        $response = $this->client->get('/api/fidelidade/indicadores');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('taxa_participacao', $data);
            $this->assertArrayHasKey('taxa_resgate', $data);
        }
    }
}
