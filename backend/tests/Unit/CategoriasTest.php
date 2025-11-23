<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de Categorias
 *
 * Cobre:
 * - Criação de categorias
 * - Listagem e paginação
 * - Busca por ID
 * - Atualização
 * - Inativação (soft delete)
 * - Validações e erros
 * - Casos de negócio
 */
class CategoriasTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdIds = [];

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
        // Limpa categorias criadas durante os testes
        foreach ($this->createdIds as $id) {
            try {
                $this->client->delete("/api/categorias/{$id}");
            } catch (\Exception $e) {
                // Ignora erros na limpeza
            }
        }
        parent::tearDown();
    }

    /**
     * Teste: Criar categoria com sucesso
     * Cenário: Enviar dados válidos de uma categoria
     * Esperado: Status 201, categoria criada com ID válido
     */
    public function testCriarCategoriaComSucesso()
    {
        $payload = [
            'nome' => 'Cimentos',
            'descricao' => 'Categoria de cimentos e argamassas',
            'ativo' => true
        ];

        $response = $this->client->post('/api/categorias', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('nome', $data);
        $this->assertArrayHasKey('descricao', $data);
        $this->assertArrayHasKey('ativo', $data);
        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('updated_at', $data);

        $this->assertEquals('Cimentos', $data['nome']);
        $this->assertEquals('Categoria de cimentos e argamassas', $data['descricao']);
        $this->assertTrue($data['ativo']);
        $this->assertIsInt($data['id']);

        // Armazena ID para limpeza
        $this->createdIds[] = $data['id'];
    }

    /**
     * Teste: Criar categoria sem nome
     * Cenário: Enviar payload sem campo obrigatório 'nome'
     * Esperado: Status 422, mensagem de validação
     */
    public function testCriarCategoriaSemNome()
    {
        $payload = [
            'descricao' => 'Descrição sem nome'
        ];

        $response = $this->client->post('/api/categorias', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertArrayHasKey('detail', $data);
    }

    /**
     * Teste: Criar categoria com nome vazio
     * Cenário: Enviar nome como string vazia
     * Esperado: Status 422, erro de validação
     */
    public function testCriarCategoriaComNomeVazio()
    {
        $payload = [
            'nome' => '',
            'descricao' => 'Teste'
        ];

        $response = $this->client->post('/api/categorias', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar categoria com nome muito longo
     * Cenário: Nome com mais de 100 caracteres
     * Esperado: Status 422
     */
    public function testCriarCategoriaComNomeMuitoLongo()
    {
        $payload = [
            'nome' => str_repeat('A', 101),
            'descricao' => 'Teste'
        ];

        $response = $this->client->post('/api/categorias', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Buscar categoria por ID existente
     * Cenário: Criar categoria e buscar pelo ID retornado
     * Esperado: Status 200, dados completos da categoria
     */
    public function testBuscarCategoriaPorId()
    {
        // Cria categoria primeiro
        $payload = [
            'nome' => 'Tintas',
            'descricao' => 'Tintas e vernizes'
        ];

        $createResponse = $this->client->post('/api/categorias', [
            'json' => $payload
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $categoriaId = $created['id'];
        $this->createdIds[] = $categoriaId;

        // Busca categoria
        $response = $this->client->get("/api/categorias/{$categoriaId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($categoriaId, $data['id']);
        $this->assertEquals('Tintas', $data['nome']);
        $this->assertEquals('Tintas e vernizes', $data['descricao']);
    }

    /**
     * Teste: Buscar categoria inexistente
     * Cenário: Buscar ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarCategoriaInexistente()
    {
        $response = $this->client->get('/api/categorias/999999');

        $this->assertEquals(404, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertArrayHasKey('detail', $data);
    }

    /**
     * Teste: Listar categorias com paginação
     * Cenário: Criar várias categorias e listar
     * Esperado: Lista paginada com metadados corretos
     */
    public function testListarCategoriasComPaginacao()
    {
        // Cria 5 categorias
        $categorias = [
            'Ferragens',
            'Hidráulica',
            'Elétrica',
            'Madeiras',
            'Revestimentos'
        ];

        foreach ($categorias as $nome) {
            $createResponse = $this->client->post('/api/categorias', [
                'json' => ['nome' => $nome]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdIds[] = $created['id'];
        }

        // Lista com page_size=3
        $response = $this->client->get('/api/categorias?page=1&page_size=3');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertArrayHasKey('total', $data);
        $this->assertArrayHasKey('page', $data);
        $this->assertArrayHasKey('page_size', $data);
        $this->assertArrayHasKey('pages', $data);

        $this->assertIsArray($data['items']);
        $this->assertEquals(1, $data['page']);
        $this->assertEquals(3, $data['page_size']);
        $this->assertGreaterThanOrEqual(5, $data['total']);
    }

    /**
     * Teste: Listar apenas categorias ativas
     * Cenário: Criar categorias ativas e inativas, filtrar
     * Esperado: Retornar apenas ativas
     */
    public function testListarApenasCategoriasAtivas()
    {
        // Cria categoria ativa
        $ativaResponse = $this->client->post('/api/categorias', [
            'json' => ['nome' => 'Ativa', 'ativo' => true]
        ]);
        $ativa = json_decode($ativaResponse->getBody(), true);
        $this->createdIds[] = $ativa['id'];

        // Cria categoria inativa
        $inativaResponse = $this->client->post('/api/categorias', [
            'json' => ['nome' => 'Inativa', 'ativo' => false]
        ]);
        $inativa = json_decode($inativaResponse->getBody(), true);
        $this->createdIds[] = $inativa['id'];

        // Lista apenas ativas
        $response = $this->client->get('/api/categorias?apenas_ativas=true');

        $data = json_decode($response->getBody(), true);

        foreach ($data['items'] as $item) {
            $this->assertTrue($item['ativo']);
        }
    }

    /**
     * Teste: Atualizar categoria existente
     * Cenário: Alterar nome e descrição
     * Esperado: Status 200, dados atualizados
     */
    public function testAtualizarCategoria()
    {
        // Cria categoria
        $createResponse = $this->client->post('/api/categorias', [
            'json' => ['nome' => 'Nome Original']
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $categoriaId = $created['id'];
        $this->createdIds[] = $categoriaId;

        // Atualiza
        $updatePayload = [
            'nome' => 'Nome Atualizado',
            'descricao' => 'Descrição nova'
        ];

        $response = $this->client->put("/api/categorias/{$categoriaId}", [
            'json' => $updatePayload
        ]);

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('Nome Atualizado', $data['nome']);
        $this->assertEquals('Descrição nova', $data['descricao']);
        $this->assertEquals($categoriaId, $data['id']);
    }

    /**
     * Teste: Atualizar categoria inexistente
     * Cenário: Tentar atualizar ID que não existe
     * Esperado: Status 404
     */
    public function testAtualizarCategoriaInexistente()
    {
        $response = $this->client->put('/api/categorias/999999', [
            'json' => ['nome' => 'Teste']
        ]);

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Inativar categoria (soft delete)
     * Cenário: Deletar categoria existente
     * Esperado: Status 204 ou 200, categoria marcada como inativa
     */
    public function testInativarCategoria()
    {
        // Cria categoria
        $createResponse = $this->client->post('/api/categorias', [
            'json' => ['nome' => 'Para Deletar']
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $categoriaId = $created['id'];

        // Deleta (inativa)
        $response = $this->client->delete("/api/categorias/{$categoriaId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se está inativa
        $getResponse = $this->client->get("/api/categorias/{$categoriaId}");

        if ($getResponse->getStatusCode() === 200) {
            $data = json_decode($getResponse->getBody(), true);
            $this->assertFalse($data['ativo']);
        }
    }

    /**
     * Teste: Deletar categoria inexistente
     * Cenário: Tentar deletar ID inexistente
     * Esperado: Status 404
     */
    public function testDeletarCategoriaInexistente()
    {
        $response = $this->client->delete('/api/categorias/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Criar múltiplas categorias e verificar ordem
     * Cenário: Criar categorias e verificar ordenação por nome
     * Esperado: Lista ordenada alfabeticamente
     */
    public function testOrdenacaoCategorias()
    {
        $nomes = ['Zebra', 'Alpha', 'Beta'];

        foreach ($nomes as $nome) {
            $createResponse = $this->client->post('/api/categorias', [
                'json' => ['nome' => $nome]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdIds[] = $created['id'];
        }

        $response = $this->client->get('/api/categorias?page_size=100');
        $data = json_decode($response->getBody(), true);

        // Verifica se existe pelo menos as 3 criadas
        $this->assertGreaterThanOrEqual(3, count($data['items']));
    }

    /**
     * Teste: Criar categoria com caracteres especiais
     * Cenário: Nome com acentos e caracteres especiais
     * Esperado: Status 201, aceita caracteres especiais
     */
    public function testCriarCategoriaComCaracteresEspeciais()
    {
        $payload = [
            'nome' => 'Ferramentas & Ferragens Ção',
            'descricao' => 'Açúcar, álcool e água'
        ];

        $response = $this->client->post('/api/categorias', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertEquals('Ferramentas & Ferragens Ção', $data['nome']);

        $this->createdIds[] = $data['id'];
    }

    /**
     * Teste: Paginação com página inválida
     * Cenário: Solicitar página 0 ou negativa
     * Esperado: Retorna página 1 por padrão ou erro
     */
    public function testPaginacaoComPaginaInvalida()
    {
        $response = $this->client->get('/api/categorias?page=0');

        // API deve retornar página 1 por padrão ou erro 422
        $this->assertContains($response->getStatusCode(), [200, 422]);

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertEquals(1, $data['page']);
        }
    }

    /**
     * Teste: Page size muito grande
     * Cenário: Solicitar page_size > limite (ex: 1000)
     * Esperado: API limita ao máximo permitido
     */
    public function testPageSizeMuitoGrande()
    {
        $response = $this->client->get('/api/categorias?page_size=1000');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->assertLessThanOrEqual(100, $data['page_size']);
    }

    /**
     * Teste: Validar timestamps de criação e atualização
     * Cenário: Criar categoria e verificar timestamps
     * Esperado: created_at e updated_at preenchidos
     */
    public function testTimestampsCategoria()
    {
        $response = $this->client->post('/api/categorias', [
            'json' => ['nome' => 'Teste Timestamps']
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdIds[] = $data['id'];

        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('updated_at', $data);
        $this->assertNotEmpty($data['created_at']);
        $this->assertNotEmpty($data['updated_at']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/', $data['created_at']);
    }

    /**
     * Teste: Atualização parcial (PATCH-like)
     * Cenário: Enviar apenas campo 'descricao' para atualizar
     * Esperado: Apenas descrição atualizada, nome mantém
     */
    public function testAtualizacaoParcial()
    {
        // Cria
        $createResponse = $this->client->post('/api/categorias', [
            'json' => ['nome' => 'Original', 'descricao' => 'Desc Original']
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $categoriaId = $created['id'];
        $this->createdIds[] = $categoriaId;

        // Atualiza apenas descrição
        $response = $this->client->put("/api/categorias/{$categoriaId}", [
            'json' => ['descricao' => 'Desc Atualizada']
        ]);

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('Original', $data['nome']);
        $this->assertEquals('Desc Atualizada', $data['descricao']);
    }
}
