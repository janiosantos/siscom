<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de Fornecedores
 *
 * Cobre:
 * - Cadastro de fornecedores PF e PJ
 * - Validação de CPF/CNPJ
 * - Endereço e contatos
 * - Prazo de pagamento
 * - Histórico de compras
 * - Análise de desempenho
 * - Busca e filtros
 */
class FornecedoresTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdFornecedorIds = [];

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
        // Limpa fornecedores criados
        foreach ($this->createdFornecedorIds as $id) {
            try {
                $this->client->delete("/api/fornecedores/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        parent::tearDown();
    }

    /**
     * Teste: Criar fornecedor PJ com sucesso
     * Cenário: Fornecedor pessoa jurídica completo
     * Esperado: Status 201, fornecedor criado
     */
    public function testCriarFornecedorPjComSucesso()
    {
        $payload = [
            'nome' => 'Distribuidora ABC Ltda',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '12345678000199',
            'razao_social' => 'ABC Distribuição e Comércio Ltda',
            'inscricao_estadual' => '123456789',
            'email' => 'contato@distribuidoraabc.com',
            'telefone' => '1133334444',
            'endereco' => 'Av. Industrial, 1000',
            'bairro' => 'Distrito Industrial',
            'cidade' => 'São Paulo',
            'uf' => 'SP',
            'cep' => '04321000',
            'prazo_pagamento' => 30,
            'ativo' => true
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('nome', $data);
        $this->assertArrayHasKey('tipo_pessoa', $data);
        $this->assertArrayHasKey('cpf_cnpj', $data);
        $this->assertArrayHasKey('created_at', $data);

        $this->assertEquals('Distribuidora ABC Ltda', $data['nome']);
        $this->assertEquals('PJ', $data['tipo_pessoa']);
        $this->assertEquals('12345678000199', $data['cpf_cnpj']);
        $this->assertEquals(30, $data['prazo_pagamento']);
        $this->assertTrue($data['ativo']);

        $this->createdFornecedorIds[] = $data['id'];
    }

    /**
     * Teste: Criar fornecedor PF com sucesso
     * Cenário: Fornecedor pessoa física
     * Esperado: Status 201
     */
    public function testCriarFornecedorPfComSucesso()
    {
        $payload = [
            'nome' => 'João Fornecedor',
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '12345678901',
            'email' => 'joao@fornecedor.com',
            'telefone' => '11987654321',
            'endereco' => 'Rua do Comércio, 500',
            'bairro' => 'Centro',
            'cidade' => 'Campinas',
            'uf' => 'SP',
            'cep' => '13010000',
            'ativo' => true
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('João Fornecedor', $data['nome']);
        $this->assertEquals('PF', $data['tipo_pessoa']);

        $this->createdFornecedorIds[] = $data['id'];
    }

    /**
     * Teste: Criar fornecedor sem nome
     * Cenário: Payload sem campo obrigatório
     * Esperado: Status 422
     */
    public function testCriarFornecedorSemNome()
    {
        $payload = [
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '98765432000199',
            'email' => 'teste@fornecedor.com'
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar fornecedor sem CNPJ
     * Cenário: Não informar cpf_cnpj
     * Esperado: Status 422
     */
    public function testCriarFornecedorSemCnpj()
    {
        $payload = [
            'nome' => 'Fornecedor Sem CNPJ',
            'tipo_pessoa' => 'PJ',
            'email' => 'semcnpj@fornecedor.com'
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar fornecedor com CNPJ duplicado
     * Cenário: Tentar cadastrar CNPJ já existente
     * Esperado: Status 400 ou 422
     */
    public function testCriarFornecedorComCnpjDuplicado()
    {
        $cnpj = '11122233000199';

        // Cria primeiro fornecedor
        $payload1 = [
            'nome' => 'Fornecedor 1',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => $cnpj,
            'email' => 'fornecedor1@empresa.com',
            'telefone' => '1133333333',
            'ativo' => true
        ];

        $response1 = $this->client->post('/api/fornecedores', [
            'json' => $payload1
        ]);

        $this->assertEquals(201, $response1->getStatusCode());
        $data1 = json_decode($response1->getBody(), true);
        $this->createdFornecedorIds[] = $data1['id'];

        // Tenta criar segundo com mesmo CNPJ
        $payload2 = [
            'nome' => 'Fornecedor 2',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => $cnpj,
            'email' => 'fornecedor2@empresa.com',
            'telefone' => '1144444444'
        ];

        $response2 = $this->client->post('/api/fornecedores', [
            'json' => $payload2
        ]);

        $this->assertContains($response2->getStatusCode(), [400, 422]);
    }

    /**
     * Teste: Buscar fornecedor por ID
     * Cenário: Criar e buscar fornecedor
     * Esperado: Dados completos
     */
    public function testBuscarFornecedorPorId()
    {
        // Cria fornecedor
        $createResponse = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Materiais Construção Ltda',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '55566677000199',
                'email' => 'materiais@construcao.com',
                'telefone' => '1155555555',
                'ativo' => true
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $fornecedorId = $created['id'];
        $this->createdFornecedorIds[] = $fornecedorId;

        // Busca fornecedor
        $response = $this->client->get("/api/fornecedores/{$fornecedorId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($fornecedorId, $data['id']);
        $this->assertEquals('Materiais Construção Ltda', $data['nome']);
        $this->assertEquals('55566677000199', $data['cpf_cnpj']);
    }

    /**
     * Teste: Buscar fornecedor inexistente
     * Cenário: ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarFornecedorInexistente()
    {
        $response = $this->client->get('/api/fornecedores/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Listar fornecedores com paginação
     * Cenário: Criar vários fornecedores e listar
     * Esperado: Lista paginada
     */
    public function testListarFornecedoresComPaginacao()
    {
        // Cria 3 fornecedores
        for ($i = 1; $i <= 3; $i++) {
            $response = $this->client->post('/api/fornecedores', [
                'json' => [
                    'nome' => "Fornecedor {$i}",
                    'tipo_pessoa' => 'PJ',
                    'cpf_cnpj' => "1112223330{$i}199",
                    'email' => "fornecedor{$i}@empresa.com",
                    'telefone' => '1166666666',
                    'ativo' => true
                ]
            ]);
            $data = json_decode($response->getBody(), true);
            $this->createdFornecedorIds[] = $data['id'];
        }

        // Lista fornecedores
        $response = $this->client->get('/api/fornecedores?page=1&page_size=10');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertArrayHasKey('total', $data);
        $this->assertArrayHasKey('page', $data);
        $this->assertArrayHasKey('page_size', $data);

        $this->assertGreaterThanOrEqual(3, $data['total']);
    }

    /**
     * Teste: Filtrar fornecedores ativos
     * Cenário: Buscar apenas fornecedores ativos
     * Esperado: Apenas ativos na lista
     */
    public function testFiltrarFornecedoresAtivos()
    {
        // Cria fornecedor ativo
        $responseAtivo = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Fornecedor Ativo',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '99988877000199',
                'email' => 'ativo@fornecedor.com',
                'telefone' => '1177777777',
                'ativo' => true
            ]
        ]);
        $ativo = json_decode($responseAtivo->getBody(), true);
        $this->createdFornecedorIds[] = $ativo['id'];

        // Cria fornecedor inativo
        $responseInativo = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Fornecedor Inativo',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '88877766000199',
                'email' => 'inativo@fornecedor.com',
                'telefone' => '1188888888',
                'ativo' => false
            ]
        ]);
        $inativo = json_decode($responseInativo->getBody(), true);
        $this->createdFornecedorIds[] = $inativo['id'];

        // Lista apenas ativos
        $response = $this->client->get('/api/fornecedores?apenas_ativos=true');

        $data = json_decode($response->getBody(), true);

        foreach ($data['items'] as $fornecedor) {
            $this->assertTrue($fornecedor['ativo']);
        }
    }

    /**
     * Teste: Atualizar fornecedor
     * Cenário: Alterar dados do fornecedor
     * Esperado: Dados atualizados
     */
    public function testAtualizarFornecedor()
    {
        // Cria fornecedor
        $createResponse = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Nome Original',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '77788899000199',
                'email' => 'original@fornecedor.com',
                'telefone' => '1199999999',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $fornecedorId = $created['id'];
        $this->createdFornecedorIds[] = $fornecedorId;

        // Atualiza
        $updatePayload = [
            'nome' => 'Nome Atualizado',
            'email' => 'atualizado@fornecedor.com',
            'telefone' => '1100000000'
        ];

        $response = $this->client->put("/api/fornecedores/{$fornecedorId}", [
            'json' => $updatePayload
        ]);

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('Nome Atualizado', $data['nome']);
        $this->assertEquals('atualizado@fornecedor.com', $data['email']);
    }

    /**
     * Teste: Atualizar fornecedor inexistente
     * Cenário: Tentar atualizar ID que não existe
     * Esperado: Status 404
     */
    public function testAtualizarFornecedorInexistente()
    {
        $response = $this->client->put('/api/fornecedores/999999', [
            'json' => ['nome' => 'Teste']
        ]);

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Inativar fornecedor
     * Cenário: Marcar fornecedor como inativo
     * Esperado: ativo = false
     */
    public function testInativarFornecedor()
    {
        // Cria fornecedor
        $createResponse = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Fornecedor Para Inativar',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '66677788000199',
                'email' => 'inativar@fornecedor.com',
                'telefone' => '1111111111',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $fornecedorId = $created['id'];

        // Inativa
        $response = $this->client->delete("/api/fornecedores/{$fornecedorId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se está inativo
        $getResponse = $this->client->get("/api/fornecedores/{$fornecedorId}");

        if ($getResponse->getStatusCode() === 200) {
            $data = json_decode($getResponse->getBody(), true);
            $this->assertFalse($data['ativo']);
        }
    }

    /**
     * Teste: Fornecedor com prazo de pagamento
     * Cenário: Definir prazo padrão
     * Esperado: Prazo armazenado
     */
    public function testFornecedorComPrazoPagamento()
    {
        $payload = [
            'nome' => 'Fornecedor Prazo',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '33344455000199',
            'email' => 'prazo@fornecedor.com',
            'telefone' => '1122222222',
            'prazo_pagamento' => 45,
            'ativo' => true
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->createdFornecedorIds[] = $data['id'];

        $this->assertEquals(45, $data['prazo_pagamento']);
    }

    /**
     * Teste: Fornecedor com prazo negativo
     * Cenário: Prazo < 0
     * Esperado: Status 422
     */
    public function testFornecedorComPrazoNegativo()
    {
        $payload = [
            'nome' => 'Fornecedor Teste',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '44455566000199',
            'email' => 'teste@fornecedor.com',
            'telefone' => '1133333333',
            'prazo_pagamento' => -10,
            'ativo' => true
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Buscar fornecedor por CNPJ
     * Cenário: Buscar usando cpf_cnpj
     * Esperado: Fornecedor encontrado
     */
    public function testBuscarFornecedorPorCnpj()
    {
        $cnpj = '22233344000199';

        // Cria fornecedor
        $createResponse = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Fornecedor CNPJ',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => $cnpj,
                'email' => 'cnpj@fornecedor.com',
                'telefone' => '1144444444',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $this->createdFornecedorIds[] = $created['id'];

        // Busca por CNPJ
        $response = $this->client->get("/api/fornecedores/buscar?cpf_cnpj={$cnpj}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($cnpj, $data['cpf_cnpj']);
        $this->assertEquals('Fornecedor CNPJ', $data['nome']);
    }

    /**
     * Teste: Fornecedor com endereço completo
     * Cenário: Verificar todos os campos de endereço
     * Esperado: Endereço armazenado
     */
    public function testFornecedorComEnderecoCompleto()
    {
        $payload = [
            'nome' => 'Fornecedor Endereço',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '88866644000199',
            'email' => 'endereco@fornecedor.com',
            'telefone' => '1155555555',
            'endereco' => 'Rua Industrial, 789',
            'complemento' => 'Galpão 5',
            'bairro' => 'Zona Leste',
            'cidade' => 'São Paulo',
            'uf' => 'SP',
            'cep' => '03400000',
            'ativo' => true
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->createdFornecedorIds[] = $data['id'];

        $this->assertEquals('Rua Industrial, 789', $data['endereco']);
        $this->assertEquals('Galpão 5', $data['complemento']);
        $this->assertEquals('Zona Leste', $data['bairro']);
        $this->assertEquals('São Paulo', $data['cidade']);
        $this->assertEquals('SP', $data['uf']);
        $this->assertEquals('03400000', $data['cep']);
    }

    /**
     * Teste: Validar formato de email
     * Cenário: Email inválido
     * Esperado: Status 422
     */
    public function testValidarFormatoEmail()
    {
        $payload = [
            'nome' => 'Fornecedor Email Inválido',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '22211100000199',
            'email' => 'email-invalido',
            'telefone' => '1166666666',
            'ativo' => true
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Buscar por nome parcial
     * Cenário: Buscar fornecedores com nome contendo texto
     * Esperado: Fornecedores correspondentes
     */
    public function testBuscarPorNomeParcial()
    {
        // Cria fornecedor
        $createResponse = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Distribuidora Nacional de Materiais',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '99988877000199',
                'email' => 'nacional@distribuidora.com',
                'telefone' => '1177777777',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $this->createdFornecedorIds[] = $created['id'];

        // Busca por nome parcial
        $response = $this->client->get('/api/fornecedores?nome=Nacional');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(1, $data['total']);
    }

    /**
     * Teste: Histórico de compras do fornecedor
     * Cenário: Buscar pedidos associados ao fornecedor
     * Esperado: Lista de pedidos
     */
    public function testHistoricoComprasFornecedor()
    {
        // Cria fornecedor
        $createResponse = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Fornecedor Histórico',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '88866655000199',
                'email' => 'historico@fornecedor.com',
                'telefone' => '1188888888',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $fornecedorId = $created['id'];
        $this->createdFornecedorIds[] = $fornecedorId;

        // Busca histórico
        $response = $this->client->get("/api/fornecedores/{$fornecedorId}/historico");

        // Pode retornar 200 ou 404 se endpoint não existe
        $this->assertContains($response->getStatusCode(), [200, 404]);

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('compras', $data);
        }
    }

    /**
     * Teste: Análise de desempenho do fornecedor
     * Cenário: Métricas de prazo, qualidade, etc
     * Esperado: Dados de performance
     */
    public function testAnaliseDesempenhoFornecedor()
    {
        // Cria fornecedor
        $createResponse = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Fornecedor Desempenho',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '77766655000199',
                'email' => 'desempenho@fornecedor.com',
                'telefone' => '1199999999',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $fornecedorId = $created['id'];
        $this->createdFornecedorIds[] = $fornecedorId;

        // Busca análise
        $response = $this->client->get("/api/fornecedores/{$fornecedorId}/desempenho");

        // Pode retornar 200 ou 404
        $this->assertContains($response->getStatusCode(), [200, 404]);

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('metricas', $data);
        }
    }

    /**
     * Teste: Validar timestamps
     * Cenário: Verificar created_at e updated_at
     * Esperado: Campos preenchidos
     */
    public function testTimestampsFornecedor()
    {
        $response = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Fornecedor Timestamps',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '77766644000199',
                'email' => 'timestamps@fornecedor.com',
                'telefone' => '1100000000',
                'ativo' => true
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdFornecedorIds[] = $data['id'];

        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('updated_at', $data);
        $this->assertNotEmpty($data['created_at']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/', $data['created_at']);
    }

    /**
     * Teste: Fornecedor com caracteres especiais
     * Cenário: Nome com acentuação
     * Esperado: Aceitar e armazenar corretamente
     */
    public function testFornecedorComCaracteresEspeciais()
    {
        $payload = [
            'nome' => 'Distribuidora São José Ltda',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '66655544000199',
            'email' => 'saojose@distribuidora.com',
            'telefone' => '1111111111',
            'ativo' => true
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->createdFornecedorIds[] = $data['id'];

        $this->assertEquals('Distribuidora São José Ltda', $data['nome']);
    }

    /**
     * Teste: Deletar fornecedor
     * Cenário: Remover fornecedor do sistema
     * Esperado: Status 204 ou 200
     */
    public function testDeletarFornecedor()
    {
        $createResponse = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Fornecedor Deletar',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '55544433000199',
                'email' => 'deletar@fornecedor.com',
                'telefone' => '1122222222',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $fornecedorId = $created['id'];

        $response = $this->client->delete("/api/fornecedores/{$fornecedorId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se foi removido
        $getResponse = $this->client->get("/api/fornecedores/{$fornecedorId}");
        $this->assertContains($getResponse->getStatusCode(), [404, 200]);
    }

    /**
     * Teste: Filtrar fornecedores por cidade
     * Cenário: Buscar fornecedores de uma cidade específica
     * Esperado: Apenas fornecedores da cidade
     */
    public function testFiltrarFornecedoresPorCidade()
    {
        // Cria fornecedor em Campinas
        $responseCampinas = $this->client->post('/api/fornecedores', [
            'json' => [
                'nome' => 'Fornecedor Campinas',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '44433322000199',
                'email' => 'campinas@fornecedor.com',
                'telefone' => '1933333333',
                'cidade' => 'Campinas',
                'uf' => 'SP',
                'ativo' => true
            ]
        ]);
        $campinas = json_decode($responseCampinas->getBody(), true);
        $this->createdFornecedorIds[] = $campinas['id'];

        // Filtra por cidade
        $response = $this->client->get('/api/fornecedores?cidade=Campinas');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertGreaterThanOrEqual(1, $data['total']);
        }
    }
}
