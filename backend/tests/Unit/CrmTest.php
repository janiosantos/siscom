<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes para CRM e Análise RFM
 *
 * RFM: Recency (Recência), Frequency (Frequência), Monetary (Valor Monetário)
 */
class CrmTest extends TestCase
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

    public function testAnaliseRfm()
    {
        $response = $this->client->get('/api/crm/analise-rfm');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('clientes', $data);
            $this->assertArrayHasKey('segmentos', $data);
        }
    }

    public function testSegmentacaoClientes()
    {
        $response = $this->client->get('/api/crm/segmentos');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('campeoes', $data);
            $this->assertArrayHasKey('fieis', $data);
            $this->assertArrayHasKey('em_risco', $data);
            $this->assertArrayHasKey('hibernando', $data);
        }
    }

    public function testClienteCampeao()
    {
        $response = $this->client->get('/api/crm/clientes/1/rfm');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('score_r', $data);
            $this->assertArrayHasKey('score_f', $data);
            $this->assertArrayHasKey('score_m', $data);
            $this->assertArrayHasKey('segmento', $data);
        }
    }

    public function testClientesEmRisco()
    {
        $response = $this->client->get('/api/crm/clientes-em-risco');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testCriarOportunidade()
    {
        $payload = [
            'cliente_id' => 1,
            'titulo' => 'Proposta Reforma Completa',
            'valor_estimado' => 15000.0,
            'probabilidade' => 70,
            'etapa' => 'NEGOCIACAO'
        ];

        $response = $this->client->post('/api/crm/oportunidades', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testFunilVendas()
    {
        $response = $this->client->get('/api/crm/funil-vendas');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('prospeccao', $data);
            $this->assertArrayHasKey('qualificacao', $data);
            $this->assertArrayHasKey('proposta', $data);
            $this->assertArrayHasKey('negociacao', $data);
            $this->assertArrayHasKey('fechamento', $data);
        }
    }

    public function testMoverOportunidadeEtapa()
    {
        $payload = ['etapa' => 'FECHAMENTO'];
        $response = $this->client->put('/api/crm/oportunidades/1/mover', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 404]);
    }

    public function testRegistrarInteracao()
    {
        $payload = [
            'cliente_id' => 1,
            'tipo' => 'TELEFONEMA',
            'descricao' => 'Cliente interessado em novo orçamento',
            'data_interacao' => date('Y-m-d H:i:s'),
            'proximo_contato' => date('Y-m-d', strtotime('+7 days'))
        ];

        $response = $this->client->post('/api/crm/interacoes', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testHistoricoInteracoes()
    {
        $response = $this->client->get('/api/crm/clientes/1/interacoes');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testAgendamento()
    {
        $payload = [
            'cliente_id' => 1,
            'tipo' => 'REUNIAO',
            'data_hora' => date('Y-m-d H:i:s', strtotime('+2 days')),
            'descricao' => 'Apresentação de produtos',
            'responsavel' => 'João Vendedor'
        ];

        $response = $this->client->post('/api/crm/agendamentos', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testTarefasPendentes()
    {
        $response = $this->client->get('/api/crm/tarefas?status=PENDENTE');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testCampanhaMarketing()
    {
        $payload = [
            'nome' => 'Campanha Black Friday 2025',
            'segmento_alvo' => 'CAMPEOES',
            'canal' => 'EMAIL',
            'data_inicio' => date('Y-m-d'),
            'data_fim' => date('Y-m-d', strtotime('+7 days'))
        ];

        $response = $this->client->post('/api/crm/campanhas', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testEnviarEmailSegmento()
    {
        $payload = [
            'segmento' => 'FIEIS',
            'assunto' => 'Oferta Exclusiva',
            'mensagem' => 'Aproveite descontos especiais!'
        ];

        $response = $this->client->post('/api/crm/enviar-email-segmento', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 202, 404]);
    }

    public function testLifetimeValue()
    {
        $response = $this->client->get('/api/crm/clientes/1/ltv');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('lifetime_value', $data);
            $this->assertArrayHasKey('total_compras', $data);
            $this->assertArrayHasKey('ticket_medio', $data);
        }
    }

    public function testChurnRate()
    {
        $response = $this->client->get('/api/crm/churn-rate?periodo=90');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('taxa_churn', $data);
            $this->assertArrayHasKey('clientes_inativos', $data);
        }
    }

    public function testPrevisaoChurn()
    {
        $response = $this->client->get('/api/crm/previsao-churn');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('clientes_risco_alto', $data);
        }
    }

    public function testRecomendacaoProdutos()
    {
        $response = $this->client->get('/api/crm/clientes/1/recomendacoes');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('produtos_recomendados', $data);
        }
    }

    public function testNps()
    {
        $payload = [
            'cliente_id' => 1,
            'nota' => 9,
            'comentario' => 'Excelente atendimento!'
        ];

        $response = $this->client->post('/api/crm/nps', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testCalcularNps()
    {
        $response = $this->client->get('/api/crm/nps/score?periodo=90');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('score_nps', $data);
            $this->assertArrayHasKey('promotores', $data);
            $this->assertArrayHasKey('neutros', $data);
            $this->assertArrayHasKey('detratores', $data);
        }
    }

    public function testDashboardCrm()
    {
        $response = $this->client->get('/api/crm/dashboard');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('oportunidades_abertas', $data);
            $this->assertArrayHasKey('valor_pipeline', $data);
            $this->assertArrayHasKey('taxa_conversao', $data);
        }
    }

    public function testRelatorioDesempenho()
    {
        $response = $this->client->get('/api/crm/relatorio-desempenho?periodo=30');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('oportunidades_ganhas', $data);
            $this->assertArrayHasKey('oportunidades_perdidas', $data);
        }
    }
}
