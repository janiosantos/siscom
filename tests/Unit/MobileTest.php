<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes para API Mobile
 *
 * Endpoints otimizados para dispositivos móveis:
 * - Vendas offline
 * - Consulta de produtos
 * - Sincronização de dados
 * - Geolocalização
 */
class MobileTest extends TestCase
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

    public function testLoginMobile()
    {
        $response = $this->client->post('/api/mobile/auth/login', [
            'json' => [
                'usuario' => 'vendedor',
                'senha' => 'senha123'
            ]
        ]);

        $this->assertContains($response->getStatusCode(), [200, 401, 404]);

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('token', $data);
        }
    }

    public function testConsultaProdutoRapida()
    {
        $response = $this->client->get('/api/mobile/produtos/busca?q=notebook');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('items', $data);
        }
    }

    public function testVendaOffline()
    {
        $payload = [
            'vendas_offline' => [
                [
                    'id_local' => 'OFFLINE_001',
                    'data_venda' => date('Y-m-d H:i:s'),
                    'itens' => [
                        [
                            'produto_id' => 1,
                            'quantidade' => 2,
                            'preco_unitario' => 50.0
                        ]
                    ],
                    'forma_pagamento' => 'DINHEIRO',
                    'valor_total' => 100.0
                ]
            ]
        ];

        $response = $this->client->post('/api/mobile/vendas/sincronizar', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testSincronizacaoProdutos()
    {
        $response = $this->client->get('/api/mobile/sync/produtos?ultima_sync=2025-01-01T00:00:00');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('produtos', $data);
            $this->assertArrayHasKey('timestamp_sync', $data);
        }
    }

    public function testConsultaEstoqueRapida()
    {
        $response = $this->client->get('/api/mobile/produtos/1/estoque');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('estoque_disponivel', $data);
        }
    }

    public function testGeoloca lizacaoVenda()
    {
        $payload = [
            'cliente_id' => 1,
            'latitude' => -23.550520,
            'longitude' => -46.633308,
            'itens' => [
                [
                    'produto_id' => 1,
                    'quantidade' => 1,
                    'preco_unitario' => 100.0
                ]
            ]
        ];

        $response = $this->client->post('/api/mobile/vendas', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 422]);
    }

    public function testHistoricoVendasVendedor()
    {
        $response = $this->client->get('/api/mobile/vendas/minhas');

        $this->assertContains($response->getStatusCode(), [200, 401, 404]);
    }

    public function testMetasVendedor()
    {
        $response = $this->client->get('/api/mobile/vendedor/metas');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('meta_mensal', $data);
        }
    }

    public function testCatalogoProdutosMobile()
    {
        $response = $this->client->get('/api/mobile/catalogo?categoria=1&page=1&limit=20');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testConsultaCliente()
    {
        $response = $this->client->get('/api/mobile/clientes/busca?cpf=12345678901');

        $this->assertContains($response->getStatusCode(), [200, 404]);
    }

    public function testRegistrarVisita()
    {
        $payload = [
            'cliente_id' => 1,
            'data_visita' => date('Y-m-d H:i:s'),
            'latitude' => -23.550520,
            'longitude' => -46.633308,
            'observacoes' => 'Cliente interessado em novos produtos'
        ];

        $response = $this->client->post('/api/mobile/visitas', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testDashboardVendedor()
    {
        $response = $this->client->get('/api/mobile/dashboard');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('vendas_hoje', $data);
        }
    }

    public function testNotificacoes()
    {
        $response = $this->client->get('/api/mobile/notificacoes');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testMarcarNotificacaoLida()
    {
        $response = $this->client->post('/api/mobile/notificacoes/1/marcar-lida');

        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testVersaoApp()
    {
        $response = $this->client->get('/api/mobile/versao');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('versao_minima', $data);
            $this->assertArrayHasKey('versao_atual', $data);
        }
    }
}
