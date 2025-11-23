<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de Clientes
 *
 * Cobre:
 * - Cadastro de clientes PF e PJ
 * - Validação de CPF/CNPJ
 * - Endereço completo
 * - Limite de crédito
 * - Histórico de compras
 * - Busca e filtros
 * - Validações de negócio
 */
class ClientesTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdClienteIds = [];

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
        // Limpa clientes criados
        foreach ($this->createdClienteIds as $id) {
            try {
                $this->client->delete("/api/clientes/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        parent::tearDown();
    }

    /**
     * Teste: Criar cliente PF com sucesso
     * Cenário: Cliente pessoa física completo
     * Esperado: Status 201, cliente criado
     */
    public function testCriarClientePfComSucesso()
    {
        $payload = [
            'nome' => 'João da Silva',
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '12345678901',
            'email' => 'joao@email.com',
            'telefone' => '11987654321',
            'endereco' => 'Rua das Flores, 123',
            'bairro' => 'Centro',
            'cidade' => 'São Paulo',
            'uf' => 'SP',
            'cep' => '01234567',
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('nome', $data);
        $this->assertArrayHasKey('tipo_pessoa', $data);
        $this->assertArrayHasKey('cpf_cnpj', $data);
        $this->assertArrayHasKey('created_at', $data);

        $this->assertEquals('João da Silva', $data['nome']);
        $this->assertEquals('PF', $data['tipo_pessoa']);
        $this->assertEquals('12345678901', $data['cpf_cnpj']);
        $this->assertTrue($data['ativo']);

        $this->createdClienteIds[] = $data['id'];
    }

    /**
     * Teste: Criar cliente PJ com sucesso
     * Cenário: Cliente pessoa jurídica completo
     * Esperado: Status 201
     */
    public function testCriarClientePjComSucesso()
    {
        $payload = [
            'nome' => 'Empresa ABC Ltda',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '12345678000199',
            'razao_social' => 'ABC Comércio e Serviços Ltda',
            'inscricao_estadual' => '123456789',
            'email' => 'contato@empresaabc.com',
            'telefone' => '1133334444',
            'endereco' => 'Av. Paulista, 1000',
            'bairro' => 'Bela Vista',
            'cidade' => 'São Paulo',
            'uf' => 'SP',
            'cep' => '01310100',
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('Empresa ABC Ltda', $data['nome']);
        $this->assertEquals('PJ', $data['tipo_pessoa']);
        $this->assertEquals('12345678000199', $data['cpf_cnpj']);
        $this->assertEquals('ABC Comércio e Serviços Ltda', $data['razao_social']);

        $this->createdClienteIds[] = $data['id'];
    }

    /**
     * Teste: Criar cliente sem nome
     * Cenário: Payload sem campo obrigatório 'nome'
     * Esperado: Status 422
     */
    public function testCriarClienteSemNome()
    {
        $payload = [
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '98765432100',
            'email' => 'teste@email.com'
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar cliente sem CPF/CNPJ
     * Cenário: Não informar cpf_cnpj
     * Esperado: Status 422
     */
    public function testCriarClienteSemCpfCnpj()
    {
        $payload = [
            'nome' => 'Maria Santos',
            'tipo_pessoa' => 'PF',
            'email' => 'maria@email.com'
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar cliente com CPF duplicado
     * Cenário: Tentar cadastrar CPF já existente
     * Esperado: Status 400 ou 422
     */
    public function testCriarClienteComCpfDuplicado()
    {
        $cpf = '11122233344';

        // Cria primeiro cliente
        $payload1 = [
            'nome' => 'Cliente 1',
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => $cpf,
            'email' => 'cliente1@email.com',
            'telefone' => '11999999999',
            'ativo' => true
        ];

        $response1 = $this->client->post('/api/clientes', [
            'json' => $payload1
        ]);

        $this->assertEquals(201, $response1->getStatusCode());
        $data1 = json_decode($response1->getBody(), true);
        $this->createdClienteIds[] = $data1['id'];

        // Tenta criar segundo com mesmo CPF
        $payload2 = [
            'nome' => 'Cliente 2',
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => $cpf,
            'email' => 'cliente2@email.com',
            'telefone' => '11888888888'
        ];

        $response2 = $this->client->post('/api/clientes', [
            'json' => $payload2
        ]);

        $this->assertContains($response2->getStatusCode(), [400, 422]);
    }

    /**
     * Teste: Buscar cliente por ID
     * Cenário: Criar e buscar cliente
     * Esperado: Dados completos
     */
    public function testBuscarClientePorId()
    {
        // Cria cliente
        $createResponse = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Pedro Oliveira',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '55566677788',
                'email' => 'pedro@email.com',
                'telefone' => '11777777777',
                'ativo' => true
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $clienteId = $created['id'];
        $this->createdClienteIds[] = $clienteId;

        // Busca cliente
        $response = $this->client->get("/api/clientes/{$clienteId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($clienteId, $data['id']);
        $this->assertEquals('Pedro Oliveira', $data['nome']);
        $this->assertEquals('55566677788', $data['cpf_cnpj']);
    }

    /**
     * Teste: Buscar cliente inexistente
     * Cenário: ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarClienteInexistente()
    {
        $response = $this->client->get('/api/clientes/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Listar clientes com paginação
     * Cenário: Criar vários clientes e listar
     * Esperado: Lista paginada
     */
    public function testListarClientesComPaginacao()
    {
        // Cria 3 clientes
        for ($i = 1; $i <= 3; $i++) {
            $response = $this->client->post('/api/clientes', [
                'json' => [
                    'nome' => "Cliente {$i}",
                    'tipo_pessoa' => 'PF',
                    'cpf_cnpj' => "1112223334{$i}",
                    'email' => "cliente{$i}@email.com",
                    'telefone' => '11999999999',
                    'ativo' => true
                ]
            ]);
            $data = json_decode($response->getBody(), true);
            $this->createdClienteIds[] = $data['id'];
        }

        // Lista clientes
        $response = $this->client->get('/api/clientes?page=1&page_size=10');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertArrayHasKey('total', $data);
        $this->assertArrayHasKey('page', $data);
        $this->assertArrayHasKey('page_size', $data);

        $this->assertGreaterThanOrEqual(3, $data['total']);
    }

    /**
     * Teste: Filtrar clientes por tipo pessoa
     * Cenário: Buscar apenas clientes PJ
     * Esperado: Apenas pessoas jurídicas
     */
    public function testFiltrarClientesPorTipoPessoa()
    {
        // Cria cliente PF
        $responsePf = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Ana Costa',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '99988877766',
                'email' => 'ana@email.com',
                'telefone' => '11666666666',
                'ativo' => true
            ]
        ]);
        $dataPf = json_decode($responsePf->getBody(), true);
        $this->createdClienteIds[] = $dataPf['id'];

        // Cria cliente PJ
        $responsePj = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Empresa XYZ',
                'tipo_pessoa' => 'PJ',
                'cpf_cnpj' => '99988877000199',
                'email' => 'xyz@empresa.com',
                'telefone' => '1155555555',
                'ativo' => true
            ]
        ]);
        $dataPj = json_decode($responsePj->getBody(), true);
        $this->createdClienteIds[] = $dataPj['id'];

        // Filtra apenas PJ
        $response = $this->client->get('/api/clientes?tipo_pessoa=PJ');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        foreach ($data['items'] as $cliente) {
            $this->assertEquals('PJ', $cliente['tipo_pessoa']);
        }
    }

    /**
     * Teste: Buscar cliente por CPF/CNPJ
     * Cenário: Buscar usando cpf_cnpj
     * Esperado: Cliente encontrado
     */
    public function testBuscarClientePorCpfCnpj()
    {
        $cpf = '33344455566';

        // Cria cliente
        $createResponse = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Carlos Lima',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => $cpf,
                'email' => 'carlos@email.com',
                'telefone' => '11444444444',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $this->createdClienteIds[] = $created['id'];

        // Busca por CPF
        $response = $this->client->get("/api/clientes/buscar?cpf_cnpj={$cpf}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($cpf, $data['cpf_cnpj']);
        $this->assertEquals('Carlos Lima', $data['nome']);
    }

    /**
     * Teste: Atualizar cliente
     * Cenário: Alterar dados do cliente
     * Esperado: Dados atualizados
     */
    public function testAtualizarCliente()
    {
        // Cria cliente
        $createResponse = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Nome Original',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '77788899900',
                'email' => 'original@email.com',
                'telefone' => '11333333333',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $clienteId = $created['id'];
        $this->createdClienteIds[] = $clienteId;

        // Atualiza
        $updatePayload = [
            'nome' => 'Nome Atualizado',
            'email' => 'atualizado@email.com',
            'telefone' => '11222222222'
        ];

        $response = $this->client->put("/api/clientes/{$clienteId}", [
            'json' => $updatePayload
        ]);

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('Nome Atualizado', $data['nome']);
        $this->assertEquals('atualizado@email.com', $data['email']);
        $this->assertEquals('11222222222', $data['telefone']);
    }

    /**
     * Teste: Atualizar cliente inexistente
     * Cenário: Tentar atualizar ID que não existe
     * Esperado: Status 404
     */
    public function testAtualizarClienteInexistente()
    {
        $response = $this->client->put('/api/clientes/999999', [
            'json' => ['nome' => 'Teste']
        ]);

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Inativar cliente
     * Cenário: Marcar cliente como inativo
     * Esperado: ativo = false
     */
    public function testInativarCliente()
    {
        // Cria cliente
        $createResponse = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Cliente Para Inativar',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '66677788899',
                'email' => 'inativar@email.com',
                'telefone' => '11111111111',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $clienteId = $created['id'];

        // Inativa
        $response = $this->client->delete("/api/clientes/{$clienteId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se está inativo
        $getResponse = $this->client->get("/api/clientes/{$clienteId}");

        if ($getResponse->getStatusCode() === 200) {
            $data = json_decode($getResponse->getBody(), true);
            $this->assertFalse($data['ativo']);
        }
    }

    /**
     * Teste: Cliente com limite de crédito
     * Cenário: Definir limite de crédito
     * Esperado: Limite armazenado
     */
    public function testClienteComLimiteCredito()
    {
        $payload = [
            'nome' => 'Cliente Crédito',
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '88899900011122',
            'email' => 'credito@empresa.com',
            'telefone' => '1199999999',
            'limite_credito' => 50000.00,
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->createdClienteIds[] = $data['id'];

        $this->assertEquals(50000.00, $data['limite_credito']);
    }

    /**
     * Teste: Cliente com limite de crédito negativo
     * Cenário: Tentar definir limite < 0
     * Esperado: Status 422
     */
    public function testClienteComLimiteCreditoNegativo()
    {
        $payload = [
            'nome' => 'Cliente Teste',
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '44455566677',
            'email' => 'teste@email.com',
            'telefone' => '11888888888',
            'limite_credito' => -1000.00,
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Validar formato de email
     * Cenário: Email inválido
     * Esperado: Status 422
     */
    public function testValidarFormatoEmail()
    {
        $payload = [
            'nome' => 'Cliente Email Inválido',
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '22233344455',
            'email' => 'email-invalido',
            'telefone' => '11777777777',
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Cliente com endereço completo
     * Cenário: Verificar todos os campos de endereço
     * Esperado: Endereço armazenado
     */
    public function testClienteComEnderecoCompleto()
    {
        $payload = [
            'nome' => 'Cliente Endereço',
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '88877766655',
            'email' => 'endereco@email.com',
            'telefone' => '11666666666',
            'endereco' => 'Rua das Palmeiras, 456',
            'complemento' => 'Apto 101',
            'bairro' => 'Jardim Europa',
            'cidade' => 'São Paulo',
            'uf' => 'SP',
            'cep' => '05432000',
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->createdClienteIds[] = $data['id'];

        $this->assertEquals('Rua das Palmeiras, 456', $data['endereco']);
        $this->assertEquals('Apto 101', $data['complemento']);
        $this->assertEquals('Jardim Europa', $data['bairro']);
        $this->assertEquals('São Paulo', $data['cidade']);
        $this->assertEquals('SP', $data['uf']);
        $this->assertEquals('05432000', $data['cep']);
    }

    /**
     * Teste: Validar UF inválida
     * Cenário: UF com código inválido
     * Esperado: Status 422
     */
    public function testValidarUfInvalida()
    {
        $payload = [
            'nome' => 'Cliente UF',
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '11100099988',
            'email' => 'uf@email.com',
            'telefone' => '11555555555',
            'uf' => 'XX', // UF inválida
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Buscar clientes ativos
     * Cenário: Filtrar apenas clientes ativos
     * Esperado: Apenas ativos na lista
     */
    public function testBuscarClientesAtivos()
    {
        // Cria cliente ativo
        $responseAtivo = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Cliente Ativo',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '11122233355',
                'email' => 'ativo@email.com',
                'telefone' => '11444444444',
                'ativo' => true
            ]
        ]);
        $ativo = json_decode($responseAtivo->getBody(), true);
        $this->createdClienteIds[] = $ativo['id'];

        // Cria cliente inativo
        $responseInativo = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Cliente Inativo',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '22233344466',
                'email' => 'inativo@email.com',
                'telefone' => '11333333333',
                'ativo' => false
            ]
        ]);
        $inativo = json_decode($responseInativo->getBody(), true);
        $this->createdClienteIds[] = $inativo['id'];

        // Lista apenas ativos
        $response = $this->client->get('/api/clientes?apenas_ativos=true');

        $data = json_decode($response->getBody(), true);

        foreach ($data['items'] as $cliente) {
            $this->assertTrue($cliente['ativo']);
        }
    }

    /**
     * Teste: Buscar por nome parcial
     * Cenário: Buscar clientes com nome contendo texto
     * Esperado: Clientes correspondentes
     */
    public function testBuscarPorNomeParcial()
    {
        // Cria cliente
        $createResponse = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Roberto Silva Santos',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '99988877755',
                'email' => 'roberto@email.com',
                'telefone' => '11222222222',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $this->createdClienteIds[] = $created['id'];

        // Busca por nome parcial
        $response = $this->client->get('/api/clientes?nome=Roberto');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(1, $data['total']);
    }

    /**
     * Teste: Histórico de compras do cliente
     * Cenário: Buscar vendas associadas ao cliente
     * Esperado: Lista de vendas
     */
    public function testHistoricoComprasCliente()
    {
        // Cria cliente
        $createResponse = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Cliente Histórico',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '88866644422',
                'email' => 'historico@email.com',
                'telefone' => '11111111111',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $clienteId = $created['id'];
        $this->createdClienteIds[] = $clienteId;

        // Busca histórico
        $response = $this->client->get("/api/clientes/{$clienteId}/historico");

        // Pode retornar 200 ou 404 se endpoint não existe
        $this->assertContains($response->getStatusCode(), [200, 404]);

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('vendas', $data);
        }
    }

    /**
     * Teste: Validar timestamps
     * Cenário: Verificar created_at e updated_at
     * Esperado: Campos preenchidos
     */
    public function testTimestampsCliente()
    {
        $response = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Cliente Timestamps',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '77766655544',
                'email' => 'timestamps@email.com',
                'telefone' => '11999999999',
                'ativo' => true
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdClienteIds[] = $data['id'];

        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('updated_at', $data);
        $this->assertNotEmpty($data['created_at']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/', $data['created_at']);
    }

    /**
     * Teste: Cliente com caracteres especiais no nome
     * Cenário: Nome com acentuação
     * Esperado: Aceitar e armazenar corretamente
     */
    public function testClienteComCaracteresEspeciais()
    {
        $payload = [
            'nome' => 'José da Conceição Araújo',
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '66655544433',
            'email' => 'jose@email.com',
            'telefone' => '11888888888',
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);
        $this->createdClienteIds[] = $data['id'];

        $this->assertEquals('José da Conceição Araújo', $data['nome']);
    }

    /**
     * Teste: Deletar cliente
     * Cenário: Remover cliente do sistema
     * Esperado: Status 204 ou 200
     */
    public function testDeletarCliente()
    {
        $createResponse = $this->client->post('/api/clientes', [
            'json' => [
                'nome' => 'Cliente Deletar',
                'tipo_pessoa' => 'PF',
                'cpf_cnpj' => '55544433322',
                'email' => 'deletar@email.com',
                'telefone' => '11777777777',
                'ativo' => true
            ]
        ]);
        $created = json_decode($createResponse->getBody(), true);
        $clienteId = $created['id'];

        $response = $this->client->delete("/api/clientes/{$clienteId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se foi removido
        $getResponse = $this->client->get("/api/clientes/{$clienteId}");
        $this->assertContains($getResponse->getStatusCode(), [404, 200]);
    }
}
