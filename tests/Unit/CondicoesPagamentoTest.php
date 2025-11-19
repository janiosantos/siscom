<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de Condições de Pagamento
 *
 * Cobre:
 * - Cadastro de condições
 * - Parcelamento
 * - Prazos e intervalos
 * - Acréscimos e descontos
 * - Validações de negócio
 */
class CondicoesPagamentoTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdCondicaoIds = [];

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
        foreach ($this->createdCondicaoIds as $id) {
            try {
                $this->client->delete("/api/condicoes-pagamento/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }
        parent::tearDown();
    }

    public function testCriarCondicaoAVista()
    {
        $payload = [
            'nome' => 'À Vista',
            'tipo' => 'A_VISTA',
            'desconto_percentual' => 5.0,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals('À Vista', $data['nome']);
        $this->assertEquals('A_VISTA', $data['tipo']);
        $this->assertEquals(5.0, $data['desconto_percentual']);

        $this->createdCondicaoIds[] = $data['id'];
    }

    public function testCriarCondicaoParcelada()
    {
        $payload = [
            'nome' => '3x sem juros',
            'tipo' => 'PARCELADO',
            'numero_parcelas' => 3,
            'intervalo_dias' => 30,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals(3, $data['numero_parcelas']);
        $this->assertEquals(30, $data['intervalo_dias']);

        $this->createdCondicaoIds[] = $data['id'];
    }

    public function testCriarCondicaoComJuros()
    {
        $payload = [
            'nome' => '6x com juros',
            'tipo' => 'PARCELADO',
            'numero_parcelas' => 6,
            'intervalo_dias' => 30,
            'juros_percentual' => 2.5,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals(2.5, $data['juros_percentual']);

        $this->createdCondicaoIds[] = $data['id'];
    }

    public function testCriarCondicaoSemNome()
    {
        $payload = [
            'tipo' => 'A_VISTA'
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    public function testBuscarCondicaoPorId()
    {
        $createResponse = $this->client->post('/api/condicoes-pagamento', [
            'json' => [
                'nome' => '2x sem juros',
                'tipo' => 'PARCELADO',
                'numero_parcelas' => 2,
                'intervalo_dias' => 30,
                'ativo' => true
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $id = $created['id'];
        $this->createdCondicaoIds[] = $id;

        $response = $this->client->get("/api/condicoes-pagamento/{$id}");

        $this->assertEquals(200, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals($id, $data['id']);
        $this->assertEquals('2x sem juros', $data['nome']);
    }

    public function testListarCondicoes()
    {
        for ($i = 0; $i < 3; $i++) {
            $createResponse = $this->client->post('/api/condicoes-pagamento', [
                'json' => [
                    'nome' => "Condição {$i}",
                    'tipo' => 'A_VISTA',
                    'ativo' => true
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdCondicaoIds[] = $created['id'];
        }

        $response = $this->client->get('/api/condicoes-pagamento');

        $this->assertEquals(200, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertGreaterThanOrEqual(3, $data['total']);
    }

    public function testAtualizarCondicao()
    {
        $createResponse = $this->client->post('/api/condicoes-pagamento', [
            'json' => [
                'nome' => 'Original',
                'tipo' => 'A_VISTA',
                'ativo' => true
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $id = $created['id'];
        $this->createdCondicaoIds[] = $id;

        $response = $this->client->put("/api/condicoes-pagamento/{$id}", [
            'json' => ['nome' => 'Atualizado']
        ]);

        $this->assertEquals(200, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals('Atualizado', $data['nome']);
    }

    public function testInativarCondicao()
    {
        $createResponse = $this->client->post('/api/condicoes-pagamento', [
            'json' => [
                'nome' => 'Para Inativar',
                'tipo' => 'A_VISTA',
                'ativo' => true
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $id = $created['id'];

        $response = $this->client->delete("/api/condicoes-pagamento/{$id}");

        $this->assertContains($response->getStatusCode(), [200, 204]);
    }

    public function testCondicaoComParcelaMinima()
    {
        $payload = [
            'nome' => '12x - parcela mínima R$50',
            'tipo' => 'PARCELADO',
            'numero_parcelas' => 12,
            'intervalo_dias' => 30,
            'valor_minimo_parcela' => 50.0,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals(50.0, $data['valor_minimo_parcela']);

        $this->createdCondicaoIds[] = $data['id'];
    }

    public function testCondicaoComDescontoEJuros()
    {
        $payload = [
            'nome' => 'Condição Especial',
            'tipo' => 'PARCELADO',
            'numero_parcelas' => 4,
            'intervalo_dias' => 30,
            'desconto_percentual' => 3.0,
            'juros_percentual' => 1.5,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals(3.0, $data['desconto_percentual']);
        $this->assertEquals(1.5, $data['juros_percentual']);

        $this->createdCondicaoIds[] = $data['id'];
    }

    public function testFiltrarApenasAtivas()
    {
        $this->client->post('/api/condicoes-pagamento', [
            'json' => ['nome' => 'Ativa', 'tipo' => 'A_VISTA', 'ativo' => true]
        ]);

        $this->client->post('/api/condicoes-pagamento', [
            'json' => ['nome' => 'Inativa', 'tipo' => 'A_VISTA', 'ativo' => false]
        ]);

        $response = $this->client->get('/api/condicoes-pagamento?apenas_ativas=true');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            foreach ($data['items'] as $item) {
                $this->assertTrue($item['ativo']);
            }
        }
    }

    public function testValidarNumeroParcelasPositivo()
    {
        $payload = [
            'nome' => 'Inválido',
            'tipo' => 'PARCELADO',
            'numero_parcelas' => -5,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    public function testCondicaoPrazo30Dias()
    {
        $payload = [
            'nome' => '30 dias',
            'tipo' => 'PRAZO',
            'dias_primeira_parcela' => 30,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [201, 422]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->createdCondicaoIds[] = $data['id'];
        }
    }

    public function testCondicao10203040()
    {
        $payload = [
            'nome' => '10-20-30-40',
            'tipo' => 'PARCELADO',
            'numero_parcelas' => 4,
            'intervalo_dias' => 10,
            'dias_primeira_parcela' => 10,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals(10, $data['dias_primeira_parcela']);
        $this->assertEquals(10, $data['intervalo_dias']);

        $this->createdCondicaoIds[] = $data['id'];
    }

    public function testCondicaoComAcrescimo()
    {
        $payload = [
            'nome' => 'Com acréscimo',
            'tipo' => 'PARCELADO',
            'numero_parcelas' => 5,
            'acrescimo_percentual' => 10.0,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());
        $data = json_decode($response->getBody(), true);

        $this->assertEquals(10.0, $data['acrescimo_percentual']);

        $this->createdCondicaoIds[] = $data['id'];
    }

    public function testTimestamps()
    {
        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => [
                'nome' => 'Test Timestamps',
                'tipo' => 'A_VISTA',
                'ativo' => true
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdCondicaoIds[] = $data['id'];

        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('updated_at', $data);
    }

    public function testBuscarCondicaoInexistente()
    {
        $response = $this->client->get('/api/condicoes-pagamento/999999');
        $this->assertEquals(404, $response->getStatusCode());
    }

    public function testDeletarCondicao()
    {
        $createResponse = $this->client->post('/api/condicoes-pagamento', [
            'json' => [
                'nome' => 'Para Deletar',
                'tipo' => 'A_VISTA',
                'ativo' => true
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $id = $created['id'];

        $response = $this->client->delete("/api/condicoes-pagamento/{$id}");

        $this->assertContains($response->getStatusCode(), [200, 204]);
    }

    public function testCondicaoEntradaMais2Parcelas()
    {
        $payload = [
            'nome' => 'Entrada + 2x',
            'tipo' => 'PARCELADO',
            'numero_parcelas' => 2,
            'entrada' => true,
            'percentual_entrada' => 30.0,
            'intervalo_dias' => 30,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [201, 422]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->createdCondicaoIds[] = $data['id'];
        }
    }

    public function testValidarPercentuaisNegativos()
    {
        $payload = [
            'nome' => 'Teste Negativo',
            'tipo' => 'A_VISTA',
            'desconto_percentual' => -10.0,
            'ativo' => true
        ];

        $response = $this->client->post('/api/condicoes-pagamento', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }
}
