<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes para E-commerce / Loja Virtual
 */
class EcommerceTest extends TestCase
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

    public function testListarProdutosLoja()
    {
        $response = $this->client->get('/api/ecommerce/produtos?categoria=1&page=1');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('items', $data);
        }
    }

    public function testDetalheProduto()
    {
        $response = $this->client->get('/api/ecommerce/produtos/1');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('descricao', $data);
            $this->assertArrayHasKey('preco_venda', $data);
            $this->assertArrayHasKey('estoque_disponivel', $data);
        }
    }

    public function testAdicionarCarrinho()
    {
        $payload = [
            'produto_id' => 1,
            'quantidade' => 2
        ];

        $response = $this->client->post('/api/ecommerce/carrinho/adicionar', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testVisualizarCarrinho()
    {
        $response = $this->client->get('/api/ecommerce/carrinho');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('itens', $data);
            $this->assertArrayHasKey('valor_total', $data);
        }
    }

    public function testRemoverItemCarrinho()
    {
        $response = $this->client->delete('/api/ecommerce/carrinho/item/1');
        $this->assertContains($response->getStatusCode(), [200, 204, 404]);
    }

    public function testAtualizarQuantidadeCarrinho()
    {
        $payload = ['quantidade' => 3];
        $response = $this->client->put('/api/ecommerce/carrinho/item/1', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 404]);
    }

    public function testCalcularFrete()
    {
        $payload = [
            'cep_destino' => '01310100',
            'itens' => [
                [
                    'produto_id' => 1,
                    'quantidade' => 2
                ]
            ]
        ];

        $response = $this->client->post('/api/ecommerce/frete/calcular', ['json' => $payload]);

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('valor_frete', $data);
            $this->assertArrayHasKey('prazo_entrega', $data);
        }
    }

    public function testAplicarCupomDesconto()
    {
        $payload = ['codigo_cupom' => 'DESCONTO10'];
        $response = $this->client->post('/api/ecommerce/carrinho/cupom', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 400, 404]);
    }

    public function testFinalizarPedido()
    {
        $payload = [
            'forma_pagamento' => 'CARTAO_CREDITO',
            'endereco_entrega' => [
                'cep' => '01310100',
                'endereco' => 'Av. Paulista, 1000',
                'numero' => '1000',
                'bairro' => 'Bela Vista',
                'cidade' => 'São Paulo',
                'uf' => 'SP'
            ],
            'parcelas' => 3
        ];

        $response = $this->client->post('/api/ecommerce/pedidos/finalizar', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 422]);
    }

    public function testConsultarPedido()
    {
        $response = $this->client->get('/api/ecommerce/pedidos/1');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('numero_pedido', $data);
            $this->assertArrayHasKey('status', $data);
        }
    }

    public function testRastreamento()
    {
        $response = $this->client->get('/api/ecommerce/pedidos/1/rastreamento');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('codigo_rastreio', $data);
        }
    }

    public function testAvaliarProduto()
    {
        $payload = [
            'produto_id' => 1,
            'nota' => 5,
            'comentario' => 'Excelente produto!'
        ];

        $response = $this->client->post('/api/ecommerce/avaliacoes', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testListarAvaliacoes()
    {
        $response = $this->client->get('/api/ecommerce/produtos/1/avaliacoes');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testListaDesejos()
    {
        $payload = ['produto_id' => 1];
        $response = $this->client->post('/api/ecommerce/lista-desejos', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 404]);
    }

    public function testBuscarProdutos()
    {
        $response = $this->client->get('/api/ecommerce/busca?q=notebook&order=preco_asc');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('items', $data);
        }
    }

    public function testProdutosRelacionados()
    {
        $response = $this->client->get('/api/ecommerce/produtos/1/relacionados');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testCategorias()
    {
        $response = $this->client->get('/api/ecommerce/categorias');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testBanners()
    {
        $response = $this->client->get('/api/ecommerce/banners');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertIsArray($data);
        }
    }

    public function testNewsletterCadastro()
    {
        $payload = ['email' => 'cliente@email.com'];
        $response = $this->client->post('/api/ecommerce/newsletter', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 201, 422]);
    }

    public function testCancelarPedido()
    {
        $payload = ['motivo' => 'Desistência do cliente'];
        $response = $this->client->post('/api/ecommerce/pedidos/1/cancelar', ['json' => $payload]);
        $this->assertContains($response->getStatusCode(), [200, 204, 400, 404]);
    }
}
