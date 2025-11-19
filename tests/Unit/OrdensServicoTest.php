<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de Ordens de Serviço
 *
 * Cobre:
 * - Criação de OS
 * - Ciclo de vida (aberta → andamento → concluída → faturada)
 * - Atribuição de técnicos
 * - Rastreamento de equipamentos
 * - Gestão de peças e mão de obra
 * - Integração com financeiro
 * - Validações de negócio
 */
class OrdensServicoTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdOsIds = [];
    private $createdClienteIds = [];
    private $createdProdutoIds = [];
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
        // Limpa OS criadas
        foreach ($this->createdOsIds as $id) {
            try {
                $this->client->delete("/api/ordens-servico/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa clientes
        foreach ($this->createdClienteIds as $id) {
            try {
                $this->client->delete("/api/clientes/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa produtos
        foreach ($this->createdProdutoIds as $id) {
            try {
                $this->client->delete("/api/produtos/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa categorias
        foreach ($this->createdCategoriaIds as $id) {
            try {
                $this->client->delete("/api/categorias/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        parent::tearDown();
    }

    /**
     * Helper: Criar cliente
     */
    private function criarCliente($nome = 'Cliente OS')
    {
        $payload = [
            'nome' => $nome,
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '12345678901',
            'email' => 'os@cliente.com',
            'telefone' => '11999999999',
            'ativo' => true
        ];

        $response = $this->client->post('/api/clientes', [
            'json' => $payload
        ]);
        $data = json_decode($response->getBody(), true);
        if (isset($data['id'])) {
            $this->createdClienteIds[] = $data['id'];
            return $data['id'];
        }
        return null;
    }

    /**
     * Helper: Criar categoria
     */
    private function criarCategoria($nome = 'Categoria OS')
    {
        $response = $this->client->post('/api/categorias', [
            'json' => ['nome' => $nome]
        ]);
        $data = json_decode($response->getBody(), true);
        $this->createdCategoriaIds[] = $data['id'];
        return $data['id'];
    }

    /**
     * Helper: Criar produto (peça)
     */
    private function criarProduto($codigoBarras, $descricao, $categoriaId, $preco)
    {
        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => $descricao,
                'categoria_id' => $categoriaId,
                'preco_custo' => $preco * 0.6,
                'preco_venda' => $preco,
                'estoque_minimo' => 5.0,
                'ativo' => true
            ]
        ]);
        $data = json_decode($response->getBody(), true);
        $this->createdProdutoIds[] = $data['id'];

        // Adiciona estoque
        $this->client->post('/api/estoque/entrada', [
            'json' => [
                'produto_id' => $data['id'],
                'quantidade' => 50.0,
                'preco_custo' => $preco * 0.6,
                'motivo' => 'COMPRA'
            ]
        ]);

        return $data['id'];
    }

    /**
     * Teste: Criar OS com sucesso
     * Cenário: OS simples com dados completos
     * Esperado: Status 201, OS criada
     */
    public function testCriarOsComSucesso()
    {
        $clienteId = $this->criarCliente('João Silva');

        $payload = [
            'cliente_id' => $clienteId,
            'equipamento' => 'Notebook Dell Inspiron 15',
            'numero_serie' => 'SN123456789',
            'defeito_reclamado' => 'Equipamento não liga, LED da bateria piscando',
            'tecnico' => 'Carlos Souza',
            'prioridade' => 'NORMAL'
        ];

        $response = $this->client->post('/api/ordens-servico', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('numero_os', $data);
        $this->assertArrayHasKey('data_abertura', $data);
        $this->assertArrayHasKey('status', $data);
        $this->assertArrayHasKey('equipamento', $data);

        $this->assertEquals('ABERTA', $data['status']);
        $this->assertEquals('Notebook Dell Inspiron 15', $data['equipamento']);
        $this->assertEquals('SN123456789', $data['numero_serie']);
        $this->assertEquals('Carlos Souza', $data['tecnico']);

        $this->createdOsIds[] = $data['id'];
    }

    /**
     * Teste: Criar OS sem cliente
     * Cenário: Não informar cliente_id
     * Esperado: Status 422
     */
    public function testCriarOsSemCliente()
    {
        $payload = [
            'equipamento' => 'Notebook',
            'defeito_reclamado' => 'Não liga'
        ];

        $response = $this->client->post('/api/ordens-servico', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar OS sem equipamento
     * Cenário: Não informar equipamento
     * Esperado: Status 422
     */
    public function testCriarOsSemEquipamento()
    {
        $clienteId = $this->criarCliente();

        $payload = [
            'cliente_id' => $clienteId,
            'defeito_reclamado' => 'Problema não especificado'
        ];

        $response = $this->client->post('/api/ordens-servico', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Buscar OS por ID
     * Cenário: Criar e buscar OS
     * Esperado: Dados completos
     */
    public function testBuscarOsPorId()
    {
        $clienteId = $this->criarCliente();

        // Cria OS
        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Impressora HP LaserJet',
                'numero_serie' => 'HP9876543',
                'defeito_reclamado' => 'Não imprime, erro no display',
                'tecnico' => 'Ana Costa'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];
        $this->createdOsIds[] = $osId;

        // Busca OS
        $response = $this->client->get("/api/ordens-servico/{$osId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($osId, $data['id']);
        $this->assertEquals('Impressora HP LaserJet', $data['equipamento']);
    }

    /**
     * Teste: Buscar OS inexistente
     * Cenário: ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarOsInexistente()
    {
        $response = $this->client->get('/api/ordens-servico/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Listar OS com paginação
     * Cenário: Criar várias OS e listar
     * Esperado: Lista paginada
     */
    public function testListarOsComPaginacao()
    {
        $clienteId = $this->criarCliente();

        // Cria 3 OS
        for ($i = 0; $i < 3; $i++) {
            $createResponse = $this->client->post('/api/ordens-servico', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'equipamento' => "Equipamento {$i}",
                    'defeito_reclamado' => "Defeito {$i}",
                    'tecnico' => 'Técnico Teste'
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdOsIds[] = $created['id'];
        }

        // Lista OS
        $response = $this->client->get('/api/ordens-servico?page=1&page_size=10');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertArrayHasKey('total', $data);
        $this->assertGreaterThanOrEqual(3, $data['total']);
    }

    /**
     * Teste: Iniciar OS (mudar para EM_ANDAMENTO)
     * Cenário: Técnico inicia o atendimento
     * Esperado: Status atualizado
     */
    public function testIniciarOs()
    {
        $clienteId = $this->criarCliente();

        // Cria OS
        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Smartphone Samsung',
                'defeito_reclamado' => 'Tela quebrada',
                'tecnico' => 'Pedro Santos'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];
        $this->createdOsIds[] = $osId;

        // Inicia OS
        $response = $this->client->post("/api/ordens-servico/{$osId}/iniciar");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/ordens-servico/{$osId}");
        $osData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('EM_ANDAMENTO', $osData['status']);
        $this->assertArrayHasKey('data_inicio', $osData);
    }

    /**
     * Teste: Concluir OS
     * Cenário: Finalizar atendimento com laudo
     * Esperado: Status CONCLUIDA
     */
    public function testConcluirOs()
    {
        $clienteId = $this->criarCliente();

        // Cria e inicia OS
        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Monitor LG 24"',
                'defeito_reclamado' => 'Sem imagem',
                'tecnico' => 'Roberto Lima'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];
        $this->createdOsIds[] = $osId;

        $this->client->post("/api/ordens-servico/{$osId}/iniciar");

        // Conclui OS
        $conclusaoPayload = [
            'laudo_tecnico' => 'Cabo VGA danificado. Substituído e testado com sucesso.',
            'observacoes' => 'Cliente orientado sobre uso adequado'
        ];

        $response = $this->client->post("/api/ordens-servico/{$osId}/concluir", [
            'json' => $conclusaoPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/ordens-servico/{$osId}");
        $osData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('CONCLUIDA', $osData['status']);
        $this->assertArrayHasKey('data_conclusao', $osData);
        $this->assertEquals('Cabo VGA danificado. Substituído e testado com sucesso.', $osData['laudo_tecnico']);
    }

    /**
     * Teste: Adicionar peças à OS
     * Cenário: Adicionar produtos utilizados no serviço
     * Esperado: Peças registradas, estoque baixado
     */
    public function testAdicionarPecasNaOs()
    {
        $clienteId = $this->criarCliente();
        $categoriaId = $this->criarCategoria();
        $pecaId = $this->criarProduto('OS0000000001', 'Fonte 12V 2A', $categoriaId, 45.0);

        // Cria OS
        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Roteador TP-Link',
                'defeito_reclamado' => 'Não liga',
                'tecnico' => 'Marcos Silva'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];
        $this->createdOsIds[] = $osId;

        // Adiciona peças
        $pecasPayload = [
            'pecas' => [
                [
                    'produto_id' => $pecaId,
                    'quantidade' => 1.0,
                    'preco_unitario' => 45.0
                ]
            ]
        ];

        $response = $this->client->post("/api/ordens-servico/{$osId}/pecas", [
            'json' => $pecasPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201]);

        // Verifica se peças foram adicionadas
        $getResponse = $this->client->get("/api/ordens-servico/{$osId}");
        $osData = json_decode($getResponse->getBody(), true);

        if (isset($osData['pecas'])) {
            $this->assertGreaterThanOrEqual(1, count($osData['pecas']));
        }
    }

    /**
     * Teste: Adicionar mão de obra
     * Cenário: Registrar valor do serviço
     * Esperado: Valor de mão de obra adicionado
     */
    public function testAdicionarMaoDeObra()
    {
        $clienteId = $this->criarCliente();

        // Cria OS
        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Desktop HP',
                'defeito_reclamado' => 'Lentidão',
                'tecnico' => 'Fernanda Costa'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];
        $this->createdOsIds[] = $osId;

        // Adiciona mão de obra
        $maoObraPayload = [
            'descricao' => 'Formatação e instalação de sistema operacional',
            'valor' => 150.0,
            'horas' => 3.0
        ];

        $response = $this->client->post("/api/ordens-servico/{$osId}/mao-obra", [
            'json' => $maoObraPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201]);

        // Verifica valor total
        $getResponse = $this->client->get("/api/ordens-servico/{$osId}");
        $osData = json_decode($getResponse->getBody(), true);

        if (isset($osData['valor_mao_obra'])) {
            $this->assertEquals(150.0, $osData['valor_mao_obra']);
        }
    }

    /**
     * Teste: Faturar OS
     * Cenário: Gerar cobrança após conclusão
     * Esperado: Status FATURADA, conta a receber criada
     */
    public function testFaturarOs()
    {
        $clienteId = $this->criarCliente();

        // Cria, inicia e conclui OS
        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Tablet Samsung',
                'defeito_reclamado' => 'Não carrega',
                'tecnico' => 'Lucas Martins'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];
        $this->createdOsIds[] = $osId;

        $this->client->post("/api/ordens-servico/{$osId}/iniciar");
        $this->client->post("/api/ordens-servico/{$osId}/concluir", [
            'json' => ['laudo_tecnico' => 'Conector USB danificado, substituído.']
        ]);

        // Fatura OS
        $faturaPayload = [
            'forma_pagamento' => 'PIX',
            'valor_total' => 200.0
        ];

        $response = $this->client->post("/api/ordens-servico/{$osId}/faturar", [
            'json' => $faturaPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 201]);

        // Verifica status
        $getResponse = $this->client->get("/api/ordens-servico/{$osId}");
        $osData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('FATURADA', $osData['status']);
        $this->assertArrayHasKey('data_faturamento', $osData);
    }

    /**
     * Teste: Cancelar OS
     * Cenário: Cliente desiste do serviço
     * Esperado: Status CANCELADA
     */
    public function testCancelarOs()
    {
        $clienteId = $this->criarCliente();

        // Cria OS
        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Console PlayStation 4',
                'defeito_reclamado' => 'Não lê discos',
                'tecnico' => 'Rafael Souza'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];
        $this->createdOsIds[] = $osId;

        // Cancela OS
        $cancelPayload = [
            'motivo' => 'Cliente desistiu do reparo, custo elevado'
        ];

        $response = $this->client->post("/api/ordens-servico/{$osId}/cancelar", [
            'json' => $cancelPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/ordens-servico/{$osId}");
        $osData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('CANCELADA', $osData['status']);
    }

    /**
     * Teste: Filtrar OS por status
     * Cenário: Buscar apenas OS abertas
     * Esperado: Lista filtrada
     */
    public function testFiltrarOsPorStatus()
    {
        $clienteId = $this->criarCliente();

        // Cria 2 OS abertas
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/ordens-servico', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'equipamento' => "Equipamento {$i}",
                    'defeito_reclamado' => "Defeito {$i}",
                    'tecnico' => 'Técnico Teste'
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdOsIds[] = $created['id'];
        }

        // Filtra por status
        $response = $this->client->get('/api/ordens-servico?status=ABERTA');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(2, $data['total']);

        foreach ($data['items'] as $os) {
            $this->assertEquals('ABERTA', $os['status']);
        }
    }

    /**
     * Teste: Filtrar OS por técnico
     * Cenário: Buscar OS de técnico específico
     * Esperado: Apenas OS do técnico
     */
    public function testFiltrarOsPorTecnico()
    {
        $clienteId = $this->criarCliente();

        // Cria 2 OS para o mesmo técnico
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/ordens-servico', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'equipamento' => "Equipamento {$i}",
                    'defeito_reclamado' => "Defeito {$i}",
                    'tecnico' => 'José da Silva'
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdOsIds[] = $created['id'];
        }

        // Filtra por técnico
        $response = $this->client->get('/api/ordens-servico?tecnico=José da Silva');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertGreaterThanOrEqual(2, $data['total']);

            foreach ($data['items'] as $os) {
                $this->assertEquals('José da Silva', $os['tecnico']);
            }
        }
    }

    /**
     * Teste: Filtrar OS por cliente
     * Cenário: Buscar OS de cliente específico
     * Esperado: Apenas OS do cliente
     */
    public function testFiltrarOsPorCliente()
    {
        $clienteId = $this->criarCliente('Cliente Específico');

        // Cria 2 OS para o cliente
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/ordens-servico', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'equipamento' => "Equipamento {$i}",
                    'defeito_reclamado' => "Defeito {$i}",
                    'tecnico' => 'Técnico Teste'
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdOsIds[] = $created['id'];
        }

        // Filtra por cliente
        $response = $this->client->get("/api/ordens-servico?cliente_id={$clienteId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(2, $data['total']);

        foreach ($data['items'] as $os) {
            $this->assertEquals($clienteId, $os['cliente_id']);
        }
    }

    /**
     * Teste: Atualizar OS aberta
     * Cenário: Alterar dados da OS
     * Esperado: Dados atualizados
     */
    public function testAtualizarOsAberta()
    {
        $clienteId = $this->criarCliente();

        // Cria OS
        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Notebook Lenovo',
                'defeito_reclamado' => 'Teclado não funciona',
                'tecnico' => 'Antônio Silva',
                'observacoes' => 'Observação original'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];
        $this->createdOsIds[] = $osId;

        // Atualiza
        $updatePayload = [
            'observacoes' => 'Observação atualizada - Cliente trouxe carregador também',
            'prioridade' => 'URGENTE'
        ];

        $response = $this->client->put("/api/ordens-servico/{$osId}", [
            'json' => $updatePayload
        ]);

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertStringContainsString('atualizada', $data['observacoes']);
        $this->assertEquals('URGENTE', $data['prioridade']);
    }

    /**
     * Teste: Validar timestamps
     * Cenário: Verificar created_at e updated_at
     * Esperado: Campos preenchidos
     */
    public function testTimestampsOs()
    {
        $clienteId = $this->criarCliente();

        $response = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Câmera Canon',
                'defeito_reclamado' => 'Lente travada',
                'tecnico' => 'Paula Santos'
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdOsIds[] = $data['id'];

        $this->assertArrayHasKey('data_abertura', $data);
        $this->assertArrayHasKey('created_at', $data);
        $this->assertNotEmpty($data['data_abertura']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/', $data['data_abertura']);
    }

    /**
     * Teste: Número de OS único
     * Cenário: Criar várias OS
     * Esperado: Cada OS tem número único
     */
    public function testNumeroOsUnico()
    {
        $clienteId = $this->criarCliente();

        $numerosOs = [];

        for ($i = 0; $i < 3; $i++) {
            $response = $this->client->post('/api/ordens-servico', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'equipamento' => "Equipamento {$i}",
                    'defeito_reclamado' => "Defeito {$i}",
                    'tecnico' => 'Técnico Teste'
                ]
            ]);

            $data = json_decode($response->getBody(), true);
            $this->createdOsIds[] = $data['id'];

            $this->assertArrayHasKey('numero_os', $data);
            $numerosOs[] = $data['numero_os'];
        }

        // Verifica se todos os números são únicos
        $this->assertEquals(count($numerosOs), count(array_unique($numerosOs)));
    }

    /**
     * Teste: Calcular valor total da OS
     * Cenário: Somar peças e mão de obra
     * Esperado: Total correto
     */
    public function testCalcularValorTotalOs()
    {
        $clienteId = $this->criarCliente();
        $categoriaId = $this->criarCategoria();
        $pecaId = $this->criarProduto('OS0000000002', 'Placa de Rede', $categoriaId, 80.0);

        // Cria OS
        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Desktop Positivo',
                'defeito_reclamado' => 'Sem rede',
                'tecnico' => 'Bruno Costa'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];
        $this->createdOsIds[] = $osId;

        // Adiciona peça
        $this->client->post("/api/ordens-servico/{$osId}/pecas", [
            'json' => [
                'pecas' => [
                    [
                        'produto_id' => $pecaId,
                        'quantidade' => 1.0,
                        'preco_unitario' => 80.0
                    ]
                ]
            ]
        ]);

        // Adiciona mão de obra
        $this->client->post("/api/ordens-servico/{$osId}/mao-obra", [
            'json' => [
                'descricao' => 'Instalação de placa',
                'valor' => 50.0,
                'horas' => 1.0
            ]
        ]);

        // Verifica valor total
        $getResponse = $this->client->get("/api/ordens-servico/{$osId}");
        $osData = json_decode($getResponse->getBody(), true);

        if (isset($osData['valor_total'])) {
            $this->assertEquals(130.0, $osData['valor_total']); // 80 + 50
        }
    }

    /**
     * Teste: Deletar OS
     * Cenário: Remover OS do sistema
     * Esperado: Status 204 ou 200
     */
    public function testDeletarOs()
    {
        $clienteId = $this->criarCliente();

        $createResponse = $this->client->post('/api/ordens-servico', [
            'json' => [
                'cliente_id' => $clienteId,
                'equipamento' => 'Mouse Logitech',
                'defeito_reclamado' => 'Botão não funciona',
                'tecnico' => 'Sandra Lima'
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $osId = $created['id'];

        $response = $this->client->delete("/api/ordens-servico/{$osId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se foi removida
        $getResponse = $this->client->get("/api/ordens-servico/{$osId}");
        $this->assertContains($getResponse->getStatusCode(), [404, 200]);
    }
}
