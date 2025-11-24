<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;

/**
 * Testes completos para o módulo de Produtos
 *
 * Cobre:
 * - CRUD completo de produtos
 * - Validações de campos obrigatórios
 * - Controle de estoque
 * - Vinculo com categoria
 * - Código de barras único
 * - Preços (custo e venda)
 * - Controle de lote e série
 * - Casos de negócio específicos
 */
class ProdutosTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdIds = [];
    private $createdCategoriaIds = [];

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
        // Limpa produtos criados
        foreach ($this->createdIds as $id) {
            try {
                $this->client->delete("/api/produtos/{$id}");
            } catch (\Exception $e) {
            }
        }

        // Limpa categorias criadas
        foreach ($this->createdCategoriaIds as $id) {
            try {
                $this->client->delete("/api/categorias/{$id}");
            } catch (\Exception $e) {
            }
        }

        parent::tearDown();
    }

    /**
     * Helper: Criar categoria para testes
     */
    private function criarCategoria($nome = 'Categoria Teste')
    {
        $response = $this->client->post('/api/categorias', [
            'json' => ['nome' => $nome]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdCategoriaIds[] = $data['id'];

        return $data['id'];
    }

    /**
     * Teste: Criar produto completo com sucesso
     * Cenário: Enviar todos os campos válidos
     * Esperado: Status 201, produto criado com todos os dados
     */
    public function testCriarProdutoCompletoComSucesso()
    {
        $categoriaId = $this->criarCategoria();

        $payload = [
            'codigo_barras' => '7891234567890',
            'descricao' => 'Cimento CP-II 50kg',
            'categoria_id' => $categoriaId,
            'unidade_medida' => 'SC',
            'preco_custo' => 25.50,
            'preco_venda' => 35.90,
            'estoque_minimo' => 10.0,
            'estoque_atual' => 100.0,
            'controla_lote' => true,
            'controla_serie' => false,
            'ativo' => true
        ];

        $response = $this->client->post('/api/produtos', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        // Validações de estrutura
        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('codigo_barras', $data);
        $this->assertArrayHasKey('descricao', $data);
        $this->assertArrayHasKey('categoria_id', $data);
        $this->assertArrayHasKey('preco_custo', $data);
        $this->assertArrayHasKey('preco_venda', $data);
        $this->assertArrayHasKey('estoque_atual', $data);
        $this->assertArrayHasKey('ativo', $data);

        // Validações de valores
        $this->assertEquals('7891234567890', $data['codigo_barras']);
        $this->assertEquals('Cimento CP-II 50kg', $data['descricao']);
        $this->assertEquals($categoriaId, $data['categoria_id']);
        $this->assertEquals(25.50, $data['preco_custo']);
        $this->assertEquals(35.90, $data['preco_venda']);
        $this->assertTrue($data['controla_lote']);
        $this->assertFalse($data['controla_serie']);

        $this->createdIds[] = $data['id'];
    }

    /**
     * Teste: Criar produto sem código de barras
     * Cenário: Omitir campo obrigatório
     * Esperado: Status 422
     */
    public function testCriarProdutoSemCodigoBarras()
    {
        $categoriaId = $this->criarCategoria();

        $payload = [
            'descricao' => 'Produto sem código',
            'categoria_id' => $categoriaId,
            'preco_custo' => 10.0,
            'preco_venda' => 15.0
        ];

        $response = $this->client->post('/api/produtos', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar produto sem descrição
     * Cenário: Omitir descrição
     * Esperado: Status 422
     */
    public function testCriarProdutoSemDescricao()
    {
        $categoriaId = $this->criarCategoria();

        $payload = [
            'codigo_barras' => '1234567890123',
            'categoria_id' => $categoriaId,
            'preco_custo' => 10.0,
            'preco_venda' => 15.0
        ];

        $response = $this->client->post('/api/produtos', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar produto com código de barras duplicado
     * Cenário: Cadastrar dois produtos com mesmo código
     * Esperado: Segundo retorna erro 400 ou 422
     */
    public function testCriarProdutoComCodigoBarrasDuplicado()
    {
        $categoriaId = $this->criarCategoria();
        $codigoBarras = '9999888877776';

        // Primeiro produto
        $response1 = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => 'Produto 1',
                'categoria_id' => $categoriaId,
                'preco_custo' => 10.0,
                'preco_venda' => 15.0
            ]
        ]);

        $this->assertEquals(201, $response1->getStatusCode());
        $data1 = json_decode($response1->getBody(), true);
        $this->createdIds[] = $data1['id'];

        // Segundo produto com mesmo código
        $response2 = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => 'Produto 2',
                'categoria_id' => $categoriaId,
                'preco_custo' => 20.0,
                'preco_venda' => 25.0
            ]
        ]);

        $this->assertContains($response2->getStatusCode(), [400, 422]);
    }

    /**
     * Teste: Criar produto com categoria inexistente
     * Cenário: Informar categoria_id que não existe
     * Esperado: Status 404 ou 422
     */
    public function testCriarProdutoComCategoriaInexistente()
    {
        $payload = [
            'codigo_barras' => '1111222233334',
            'descricao' => 'Produto',
            'categoria_id' => 999999,
            'preco_custo' => 10.0,
            'preco_venda' => 15.0
        ];

        $response = $this->client->post('/api/produtos', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [404, 422]);
    }

    /**
     * Teste: Criar produto com preço de venda menor que custo
     * Cenário: preco_venda < preco_custo
     * Esperado: API aceita (pode ser promoção), mas alerta pode ser adicionado
     */
    public function testCriarProdutoComPrecoVendaMenorQueCusto()
    {
        $categoriaId = $this->criarCategoria();

        $payload = [
            'codigo_barras' => '5555666677778',
            'descricao' => 'Produto Promocional',
            'categoria_id' => $categoriaId,
            'preco_custo' => 50.0,
            'preco_venda' => 30.0  // Menor que custo
        ];

        $response = $this->client->post('/api/produtos', [
            'json' => $payload
        ]);

        // API pode aceitar (é válido) ou rejeitar (regra de negócio)
        $this->assertContains($response->getStatusCode(), [201, 400, 422]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->createdIds[] = $data['id'];
        }
    }

    /**
     * Teste: Criar produto com preços negativos
     * Cenário: preco_custo ou preco_venda negativos
     * Esperado: Status 422
     */
    public function testCriarProdutoComPrecosNegativos()
    {
        $categoriaId = $this->criarCategoria();

        $payload = [
            'codigo_barras' => '3333444455556',
            'descricao' => 'Produto',
            'categoria_id' => $categoriaId,
            'preco_custo' => -10.0,
            'preco_venda' => 15.0
        ];

        $response = $this->client->post('/api/produtos', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar produto com estoque negativo
     * Cenário: estoque_atual negativo
     * Esperado: Status 422
     */
    public function testCriarProdutoComEstoqueNegativo()
    {
        $categoriaId = $this->criarCategoria();

        $payload = [
            'codigo_barras' => '6666777788889',
            'descricao' => 'Produto',
            'categoria_id' => $categoriaId,
            'preco_custo' => 10.0,
            'preco_venda' => 15.0,
            'estoque_atual' => -5.0
        ];

        $response = $this->client->post('/api/produtos', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Buscar produto por ID
     * Cenário: Criar e buscar produto
     * Esperado: Status 200, dados completos
     */
    public function testBuscarProdutoPorId()
    {
        $categoriaId = $this->criarCategoria();

        $createResponse = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => '1010101010101',
                'descricao' => 'Areia Fina 20kg',
                'categoria_id' => $categoriaId,
                'preco_custo' => 8.0,
                'preco_venda' => 12.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $produtoId = $created['id'];
        $this->createdIds[] = $produtoId;

        // Busca
        $response = $this->client->get("/api/produtos/{$produtoId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($produtoId, $data['id']);
        $this->assertEquals('Areia Fina 20kg', $data['descricao']);
        $this->assertEquals($categoriaId, $data['categoria_id']);
    }

    /**
     * Teste: Buscar produto inexistente
     * Cenário: ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarProdutoInexistente()
    {
        $response = $this->client->get('/api/produtos/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Buscar produto por código de barras
     * Cenário: Buscar pelo endpoint de código de barras
     * Esperado: Status 200, produto encontrado
     */
    public function testBuscarProdutoPorCodigoBarras()
    {
        $categoriaId = $this->criarCategoria();
        $codigoBarras = '7890123456789';

        $createResponse = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => 'Produto para busca',
                'categoria_id' => $categoriaId,
                'preco_custo' => 10.0,
                'preco_venda' => 15.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $this->createdIds[] = $created['id'];

        // Busca por código de barras
        $response = $this->client->get("/api/produtos/codigo-barras/{$codigoBarras}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertEquals($codigoBarras, $data['codigo_barras']);
    }

    /**
     * Teste: Listar produtos com paginação
     * Cenário: Criar vários produtos e listar
     * Esperado: Paginação funcional
     */
    public function testListarProdutosComPaginacao()
    {
        $categoriaId = $this->criarCategoria();

        // Cria 5 produtos
        for ($i = 1; $i <= 5; $i++) {
            $createResponse = $this->client->post('/api/produtos', [
                'json' => [
                    'codigo_barras' => "PROD{$i}" . str_pad($i, 10, '0'),
                    'descricao' => "Produto {$i}",
                    'categoria_id' => $categoriaId,
                    'preco_custo' => 10.0 * $i,
                    'preco_venda' => 15.0 * $i
                ]
            ]);

            $created = json_decode($createResponse->getBody(), true);
            $this->createdIds[] = $created['id'];
        }

        // Lista
        $response = $this->client->get('/api/produtos?page=1&page_size=3');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertArrayHasKey('total', $data);
        $this->assertArrayHasKey('page', $data);
        $this->assertArrayHasKey('page_size', $data);

        $this->assertEquals(1, $data['page']);
        $this->assertEquals(3, $data['page_size']);
        $this->assertGreaterThanOrEqual(5, $data['total']);
    }

    /**
     * Teste: Listar produtos por categoria
     * Cenário: Filtrar produtos de uma categoria específica
     * Esperado: Apenas produtos da categoria solicitada
     */
    public function testListarProdutosPorCategoria()
    {
        $categoria1Id = $this->criarCategoria('Categoria 1');
        $categoria2Id = $this->criarCategoria('Categoria 2');

        // Produtos categoria 1
        for ($i = 1; $i <= 3; $i++) {
            $createResponse = $this->client->post('/api/produtos', [
                'json' => [
                    'codigo_barras' => "CAT1{$i}" . str_pad($i, 9, '0'),
                    'descricao' => "Produto Cat1 {$i}",
                    'categoria_id' => $categoria1Id,
                    'preco_custo' => 10.0,
                    'preco_venda' => 15.0
                ]
            ]);

            $created = json_decode($createResponse->getBody(), true);
            $this->createdIds[] = $created['id'];
        }

        // Produtos categoria 2
        for ($i = 1; $i <= 2; $i++) {
            $createResponse = $this->client->post('/api/produtos', [
                'json' => [
                    'codigo_barras' => "CAT2{$i}" . str_pad($i, 9, '0'),
                    'descricao' => "Produto Cat2 {$i}",
                    'categoria_id' => $categoria2Id,
                    'preco_custo' => 20.0,
                    'preco_venda' => 25.0
                ]
            ]);

            $created = json_decode($createResponse->getBody(), true);
            $this->createdIds[] = $created['id'];
        }

        // Lista por categoria 1
        $response = $this->client->get("/api/produtos/categoria/{$categoria1Id}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertIsArray($data);
        $this->assertGreaterThanOrEqual(3, count($data));

        foreach ($data as $produto) {
            $this->assertEquals($categoria1Id, $produto['categoria_id']);
        }
    }

    /**
     * Teste: Atualizar produto
     * Cenário: Alterar preços e descrição
     * Esperado: Status 200, dados atualizados
     */
    public function testAtualizarProduto()
    {
        $categoriaId = $this->criarCategoria();

        $createResponse = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => '1212121212121',
                'descricao' => 'Original',
                'categoria_id' => $categoriaId,
                'preco_custo' => 10.0,
                'preco_venda' => 15.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $produtoId = $created['id'];
        $this->createdIds[] = $produtoId;

        // Atualiza
        $updatePayload = [
            'descricao' => 'Atualizado',
            'preco_custo' => 12.0,
            'preco_venda' => 18.0
        ];

        $response = $this->client->put("/api/produtos/{$produtoId}", [
            'json' => $updatePayload
        ]);

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('Atualizado', $data['descricao']);
        $this->assertEquals(12.0, $data['preco_custo']);
        $this->assertEquals(18.0, $data['preco_venda']);
    }

    /**
     * Teste: Inativar produto (soft delete)
     * Cenário: Deletar produto
     * Esperado: Produto marcado como inativo
     */
    public function testInativarProduto()
    {
        $categoriaId = $this->criarCategoria();

        $createResponse = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => '9998887776665',
                'descricao' => 'Para deletar',
                'categoria_id' => $categoriaId,
                'preco_custo' => 10.0,
                'preco_venda' => 15.0
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $produtoId = $created['id'];

        // Deleta
        $response = $this->client->delete("/api/produtos/{$produtoId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se está inativo
        $getResponse = $this->client->get("/api/produtos/{$produtoId}");

        if ($getResponse->getStatusCode() === 200) {
            $data = json_decode($getResponse->getBody(), true);
            $this->assertFalse($data['ativo']);
        }
    }

    /**
     * Teste: Listar apenas produtos ativos
     * Cenário: Criar ativos e inativos, filtrar
     * Esperado: Apenas ativos
     */
    public function testListarApenasProdutosAtivos()
    {
        $categoriaId = $this->criarCategoria();

        // Produto ativo
        $ativoResponse = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => 'ATIVO1234567890',
                'descricao' => 'Ativo',
                'categoria_id' => $categoriaId,
                'preco_custo' => 10.0,
                'preco_venda' => 15.0,
                'ativo' => true
            ]
        ]);
        $ativo = json_decode($ativoResponse->getBody(), true);
        $this->createdIds[] = $ativo['id'];

        // Produto inativo
        $inativoResponse = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => 'INATIVO123456789',
                'descricao' => 'Inativo',
                'categoria_id' => $categoriaId,
                'preco_custo' => 10.0,
                'preco_venda' => 15.0,
                'ativo' => false
            ]
        ]);
        $inativo = json_decode($inativoResponse->getBody(), true);
        $this->createdIds[] = $inativo['id'];

        // Lista apenas ativos
        $response = $this->client->get('/api/produtos?apenas_ativos=true');

        $data = json_decode($response->getBody(), true);

        foreach ($data['items'] as $produto) {
            $this->assertTrue($produto['ativo']);
        }
    }

    /**
     * Teste: Produto com controle de lote ativado
     * Cenário: controla_lote = true
     * Esperado: Campo salvo corretamente
     */
    public function testProdutoComControleLote()
    {
        $categoriaId = $this->criarCategoria();

        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => 'LOTE123456789012',
                'descricao' => 'Produto com lote',
                'categoria_id' => $categoriaId,
                'preco_custo' => 10.0,
                'preco_venda' => 15.0,
                'controla_lote' => true
            ]
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertTrue($data['controla_lote']);

        $this->createdIds[] = $data['id'];
    }

    /**
     * Teste: Produto com controle de série ativado
     * Cenário: controla_serie = true
     * Esperado: Campo salvo corretamente
     */
    public function testProdutoComControleSerie()
    {
        $categoriaId = $this->criarCategoria();

        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => 'SERIE12345678901',
                'descricao' => 'Produto com série',
                'categoria_id' => $categoriaId,
                'preco_custo' => 100.0,
                'preco_venda' => 150.0,
                'controla_serie' => true
            ]
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertTrue($data['controla_serie']);

        $this->createdIds[] = $data['id'];
    }

    /**
     * Teste: Produto com estoque abaixo do mínimo
     * Cenário: estoque_atual < estoque_minimo
     * Esperado: Produto criado (alerta pode ser gerado pelo sistema)
     */
    public function testProdutoComEstoqueAbaixoMinimo()
    {
        $categoriaId = $this->criarCategoria();

        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => 'ESTMIN1234567890',
                'descricao' => 'Produto estoque baixo',
                'categoria_id' => $categoriaId,
                'preco_custo' => 10.0,
                'preco_venda' => 15.0,
                'estoque_minimo' => 50.0,
                'estoque_atual' => 5.0  // Abaixo do mínimo
            ]
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertEquals(5.0, $data['estoque_atual']);
        $this->assertEquals(50.0, $data['estoque_minimo']);

        $this->createdIds[] = $data['id'];
    }
}
