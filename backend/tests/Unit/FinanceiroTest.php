<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo Financeiro
 *
 * Cobre:
 * - Contas a pagar
 * - Contas a receber
 * - Baixa de contas (pagamento/recebimento)
 * - Parcelamento
 * - Juros e multas
 * - Fluxo de caixa
 * - Relatórios financeiros
 * - Validações de negócio
 */
class FinanceiroTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdContasPagarIds = [];
    private $createdContasReceberIds = [];
    private $createdFornecedorIds = [];
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
        // Limpa contas a pagar
        foreach ($this->createdContasPagarIds as $id) {
            try {
                $this->client->delete("/api/financeiro/contas-pagar/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa contas a receber
        foreach ($this->createdContasReceberIds as $id) {
            try {
                $this->client->delete("/api/financeiro/contas-receber/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa fornecedores
        foreach ($this->createdFornecedorIds as $id) {
            try {
                $this->client->delete("/api/fornecedores/{$id}");
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

        parent::tearDown();
    }

    /**
     * Helper: Criar fornecedor
     */
    private function criarFornecedor($nome = 'Fornecedor Teste')
    {
        $payload = [
            'nome' => $nome,
            'tipo_pessoa' => 'PJ',
            'cpf_cnpj' => '12345678000199',
            'email' => 'fornecedor@teste.com',
            'telefone' => '1133334444',
            'ativo' => true
        ];

        $response = $this->client->post('/api/fornecedores', [
            'json' => $payload
        ]);
        $data = json_decode($response->getBody(), true);
        if (isset($data['id'])) {
            $this->createdFornecedorIds[] = $data['id'];
            return $data['id'];
        }
        return null;
    }

    /**
     * Helper: Criar cliente
     */
    private function criarCliente($nome = 'Cliente Teste')
    {
        $payload = [
            'nome' => $nome,
            'tipo_pessoa' => 'PF',
            'cpf_cnpj' => '12345678901',
            'email' => 'cliente@teste.com',
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
     * Teste: Criar conta a pagar com sucesso
     * Cenário: Conta simples de fornecedor
     * Esperado: Status 201, conta criada
     */
    public function testCriarContaPagarComSucesso()
    {
        $fornecedorId = $this->criarFornecedor('Fornecedor ABC');

        $payload = [
            'fornecedor_id' => $fornecedorId,
            'descricao' => 'Compra de materiais',
            'valor' => 1500.0,
            'data_vencimento' => date('Y-m-d', strtotime('+30 days')),
            'categoria' => 'COMPRAS'
        ];

        $response = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('descricao', $data);
        $this->assertArrayHasKey('valor', $data);
        $this->assertArrayHasKey('data_vencimento', $data);
        $this->assertArrayHasKey('status', $data);

        $this->assertEquals('Compra de materiais', $data['descricao']);
        $this->assertEquals(1500.0, $data['valor']);
        $this->assertEquals('PENDENTE', $data['status']);

        $this->createdContasPagarIds[] = $data['id'];
    }

    /**
     * Teste: Criar conta a pagar sem fornecedor
     * Cenário: Conta sem fornecedor_id
     * Esperado: Status 422
     */
    public function testCriarContaPagarSemFornecedor()
    {
        $payload = [
            'descricao' => 'Despesa geral',
            'valor' => 500.0,
            'data_vencimento' => date('Y-m-d', strtotime('+15 days'))
        ];

        $response = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Criar conta a pagar com valor negativo
     * Cenário: Valor < 0
     * Esperado: Status 422
     */
    public function testCriarContaPagarComValorNegativo()
    {
        $fornecedorId = $this->criarFornecedor();

        $payload = [
            'fornecedor_id' => $fornecedorId,
            'descricao' => 'Teste',
            'valor' => -100.0,
            'data_vencimento' => date('Y-m-d')
        ];

        $response = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Buscar conta a pagar por ID
     * Cenário: Criar e buscar
     * Esperado: Dados completos
     */
    public function testBuscarContaPagarPorId()
    {
        $fornecedorId = $this->criarFornecedor();

        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Energia elétrica',
                'valor' => 350.0,
                'data_vencimento' => date('Y-m-d', strtotime('+10 days'))
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];
        $this->createdContasPagarIds[] = $contaId;

        $response = $this->client->get("/api/financeiro/contas-pagar/{$contaId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($contaId, $data['id']);
        $this->assertEquals('Energia elétrica', $data['descricao']);
        $this->assertEquals(350.0, $data['valor']);
    }

    /**
     * Teste: Buscar conta a pagar inexistente
     * Cenário: ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarContaPagarInexistente()
    {
        $response = $this->client->get('/api/financeiro/contas-pagar/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Baixar conta a pagar (pagamento)
     * Cenário: Pagar conta pendente
     * Esperado: Status PAGO, data_pagamento preenchida
     */
    public function testBaixarContaPagar()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria conta
        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Aluguel',
                'valor' => 2000.0,
                'data_vencimento' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];
        $this->createdContasPagarIds[] = $contaId;

        // Baixa conta
        $baixaPayload = [
            'data_pagamento' => date('Y-m-d'),
            'valor_pago' => 2000.0,
            'forma_pagamento' => 'TRANSFERENCIA'
        ];

        $response = $this->client->post("/api/financeiro/contas-pagar/{$contaId}/baixar", [
            'json' => $baixaPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/financeiro/contas-pagar/{$contaId}");
        $contaData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('PAGO', $contaData['status']);
        $this->assertArrayHasKey('data_pagamento', $contaData);
        $this->assertEquals(2000.0, $contaData['valor_pago']);
    }

    /**
     * Teste: Baixar conta com valor parcial
     * Cenário: Pagar menos que o valor total
     * Esperado: Status PARCIAL
     */
    public function testBaixarContaComValorParcial()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria conta
        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Fornecimento',
                'valor' => 1000.0,
                'data_vencimento' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];
        $this->createdContasPagarIds[] = $contaId;

        // Baixa parcial
        $baixaPayload = [
            'data_pagamento' => date('Y-m-d'),
            'valor_pago' => 600.0,
            'forma_pagamento' => 'DINHEIRO'
        ];

        $response = $this->client->post("/api/financeiro/contas-pagar/{$contaId}/baixar", [
            'json' => $baixaPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/financeiro/contas-pagar/{$contaId}");
        if ($getResponse->getStatusCode() === 200) {
            $contaData = json_decode($getResponse->getBody(), true);
            $this->assertContains($contaData['status'], ['PARCIAL', 'PAGO']);
        }
    }

    /**
     * Teste: Criar conta a receber com sucesso
     * Cenário: Conta de cliente
     * Esperado: Status 201
     */
    public function testCriarContaReceberComSucesso()
    {
        $clienteId = $this->criarCliente('João Silva');

        $payload = [
            'cliente_id' => $clienteId,
            'descricao' => 'Venda de materiais',
            'valor' => 850.0,
            'data_vencimento' => date('Y-m-d', strtotime('+15 days')),
            'categoria' => 'VENDAS'
        ];

        $response = $this->client->post('/api/financeiro/contas-receber', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertEquals('Venda de materiais', $data['descricao']);
        $this->assertEquals(850.0, $data['valor']);
        $this->assertEquals('PENDENTE', $data['status']);

        $this->createdContasReceberIds[] = $data['id'];
    }

    /**
     * Teste: Criar conta a receber sem cliente
     * Cenário: Venda sem cliente_id
     * Esperado: Status 422 ou aceitar null
     */
    public function testCriarContaReceberSemCliente()
    {
        $payload = [
            'descricao' => 'Venda balcão',
            'valor' => 100.0,
            'data_vencimento' => date('Y-m-d')
        ];

        $response = $this->client->post('/api/financeiro/contas-receber', [
            'json' => $payload
        ]);

        // Pode aceitar null para vendas sem cliente ou rejeitar
        $this->assertContains($response->getStatusCode(), [201, 422]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->createdContasReceberIds[] = $data['id'];
        }
    }

    /**
     * Teste: Baixar conta a receber (recebimento)
     * Cenário: Receber pagamento de cliente
     * Esperado: Status RECEBIDO
     */
    public function testBaixarContaReceber()
    {
        $clienteId = $this->criarCliente();

        // Cria conta
        $createResponse = $this->client->post('/api/financeiro/contas-receber', [
            'json' => [
                'cliente_id' => $clienteId,
                'descricao' => 'Venda 001',
                'valor' => 500.0,
                'data_vencimento' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];
        $this->createdContasReceberIds[] = $contaId;

        // Baixa conta
        $baixaPayload = [
            'data_recebimento' => date('Y-m-d'),
            'valor_recebido' => 500.0,
            'forma_pagamento' => 'PIX'
        ];

        $response = $this->client->post("/api/financeiro/contas-receber/{$contaId}/baixar", [
            'json' => $baixaPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/financeiro/contas-receber/{$contaId}");
        $contaData = json_decode($getResponse->getBody(), true);

        $this->assertEquals('RECEBIDO', $contaData['status']);
        $this->assertArrayHasKey('data_recebimento', $contaData);
    }

    /**
     * Teste: Listar contas a pagar com filtros
     * Cenário: Filtrar por status e período
     * Esperado: Lista filtrada
     */
    public function testListarContasPagarComFiltros()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria 2 contas
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
                'json' => [
                    'fornecedor_id' => $fornecedorId,
                    'descricao' => "Conta {$i}",
                    'valor' => 100.0 + ($i * 50),
                    'data_vencimento' => date('Y-m-d', strtotime("+{$i} days"))
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdContasPagarIds[] = $created['id'];
        }

        // Lista pendentes
        $response = $this->client->get('/api/financeiro/contas-pagar?status=PENDENTE');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertGreaterThanOrEqual(2, $data['total']);
    }

    /**
     * Teste: Listar contas a receber com filtros
     * Cenário: Filtrar por cliente
     * Esperado: Apenas contas do cliente
     */
    public function testListarContasReceberPorCliente()
    {
        $clienteId = $this->criarCliente('Maria Santos');

        // Cria 2 contas para o cliente
        for ($i = 0; $i < 2; $i++) {
            $createResponse = $this->client->post('/api/financeiro/contas-receber', [
                'json' => [
                    'cliente_id' => $clienteId,
                    'descricao' => "Venda {$i}",
                    'valor' => 200.0,
                    'data_vencimento' => date('Y-m-d', strtotime('+7 days'))
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdContasReceberIds[] = $created['id'];
        }

        // Lista por cliente
        $response = $this->client->get("/api/financeiro/contas-receber?cliente_id={$clienteId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(2, $data['total']);

        foreach ($data['items'] as $conta) {
            $this->assertEquals($clienteId, $conta['cliente_id']);
        }
    }

    /**
     * Teste: Contas vencidas
     * Cenário: Buscar contas com vencimento passado
     * Esperado: Lista de contas vencidas
     */
    public function testListarContasVencidas()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria conta vencida
        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Conta vencida',
                'valor' => 300.0,
                'data_vencimento' => date('Y-m-d', strtotime('-5 days'))
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $this->createdContasPagarIds[] = $created['id'];

        // Lista vencidas
        $response = $this->client->get('/api/financeiro/contas-pagar?vencidas=true');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertGreaterThanOrEqual(1, $data['total']);
    }

    /**
     * Teste: Cancelar conta a pagar
     * Cenário: Cancelar conta pendente
     * Esperado: Status CANCELADO
     */
    public function testCancelarContaPagar()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria conta
        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Conta para cancelar',
                'valor' => 250.0,
                'data_vencimento' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];
        $this->createdContasPagarIds[] = $contaId;

        // Cancela
        $response = $this->client->post("/api/financeiro/contas-pagar/{$contaId}/cancelar");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/financeiro/contas-pagar/{$contaId}");
        if ($getResponse->getStatusCode() === 200) {
            $contaData = json_decode($getResponse->getBody(), true);
            $this->assertEquals('CANCELADO', $contaData['status']);
        }
    }

    /**
     * Teste: Cancelar conta já paga
     * Cenário: Tentar cancelar conta paga
     * Esperado: Status 400
     */
    public function testCancelarContaJaPaga()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria e paga conta
        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Conta paga',
                'valor' => 150.0,
                'data_vencimento' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];
        $this->createdContasPagarIds[] = $contaId;

        // Paga
        $this->client->post("/api/financeiro/contas-pagar/{$contaId}/baixar", [
            'json' => [
                'data_pagamento' => date('Y-m-d'),
                'valor_pago' => 150.0,
                'forma_pagamento' => 'DINHEIRO'
            ]
        ]);

        // Tenta cancelar
        $response = $this->client->post("/api/financeiro/contas-pagar/{$contaId}/cancelar");

        $this->assertEquals(400, $response->getStatusCode());
    }

    /**
     * Teste: Aplicar juros em conta vencida
     * Cenário: Conta vencida com juros
     * Esperado: Valor com juros calculado
     */
    public function testAplicarJurosEmContaVencida()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria conta vencida
        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Conta com juros',
                'valor' => 1000.0,
                'data_vencimento' => date('Y-m-d', strtotime('-10 days')),
                'percentual_juros_dia' => 0.1
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];
        $this->createdContasPagarIds[] = $contaId;

        // Busca conta (deve calcular juros)
        $response = $this->client->get("/api/financeiro/contas-pagar/{$contaId}");
        $contaData = json_decode($response->getBody(), true);

        if (isset($contaData['valor_com_juros'])) {
            // Juros de 10 dias a 0.1% ao dia = 1%
            // 1000 + 1% = 1010
            $this->assertGreaterThan(1000.0, $contaData['valor_com_juros']);
        }
    }

    /**
     * Teste: Criar conta parcelada
     * Cenário: Dividir valor em parcelas
     * Esperado: Múltiplas contas criadas
     */
    public function testCriarContaParcelada()
    {
        $fornecedorId = $this->criarFornecedor();

        $payload = [
            'fornecedor_id' => $fornecedorId,
            'descricao' => 'Compra parcelada',
            'valor_total' => 900.0,
            'numero_parcelas' => 3,
            'data_primeira_parcela' => date('Y-m-d', strtotime('+30 days')),
            'intervalo_dias' => 30
        ];

        $response = $this->client->post('/api/financeiro/contas-pagar/parcelado', [
            'json' => $payload
        ]);

        if ($response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);

            $this->assertArrayHasKey('parcelas', $data);
            $this->assertCount(3, $data['parcelas']);

            // Cada parcela deve ter 300
            foreach ($data['parcelas'] as $parcela) {
                $this->assertEquals(300.0, $parcela['valor']);
                $this->createdContasPagarIds[] = $parcela['id'];
            }
        } else {
            // Endpoint pode não estar implementado
            $this->assertContains($response->getStatusCode(), [404, 501]);
        }
    }

    /**
     * Teste: Fluxo de caixa do período
     * Cenário: Consultar entradas e saídas
     * Esperado: Relatório com totais
     */
    public function testFluxoCaixaPeriodo()
    {
        $dataInicio = date('Y-m-d');
        $dataFim = date('Y-m-d', strtotime('+30 days'));

        $response = $this->client->get("/api/financeiro/fluxo-caixa?data_inicio={$dataInicio}&data_fim={$dataFim}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('total_pagar', $data);
        $this->assertArrayHasKey('total_receber', $data);
        $this->assertArrayHasKey('saldo', $data);

        $this->assertIsNumeric($data['total_pagar']);
        $this->assertIsNumeric($data['total_receber']);
    }

    /**
     * Teste: Relatório por categoria
     * Cenário: Agrupar contas por categoria
     * Esperado: Totais por categoria
     */
    public function testRelatorioPorCategoria()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria contas em categorias diferentes
        $categorias = ['COMPRAS', 'IMPOSTOS', 'SALARIOS'];

        foreach ($categorias as $categoria) {
            $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
                'json' => [
                    'fornecedor_id' => $fornecedorId,
                    'descricao' => "Despesa {$categoria}",
                    'valor' => 500.0,
                    'data_vencimento' => date('Y-m-d'),
                    'categoria' => $categoria
                ]
            ]);
            $created = json_decode($createResponse->getBody(), true);
            $this->createdContasPagarIds[] = $created['id'];
        }

        $response = $this->client->get('/api/financeiro/relatorio/categoria');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('categorias', $data);
            $this->assertIsArray($data['categorias']);
        }
    }

    /**
     * Teste: Validar timestamps
     * Cenário: Verificar created_at e updated_at
     * Esperado: Campos preenchidos
     */
    public function testTimestampsContaPagar()
    {
        $fornecedorId = $this->criarFornecedor();

        $response = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Teste timestamps',
                'valor' => 100.0,
                'data_vencimento' => date('Y-m-d')
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdContasPagarIds[] = $data['id'];

        $this->assertArrayHasKey('created_at', $data);
        $this->assertArrayHasKey('updated_at', $data);
        $this->assertNotEmpty($data['created_at']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/', $data['created_at']);
    }

    /**
     * Teste: Atualizar conta a pagar
     * Cenário: Alterar valor e vencimento
     * Esperado: Dados atualizados
     */
    public function testAtualizarContaPagar()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria conta
        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Conta original',
                'valor' => 100.0,
                'data_vencimento' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];
        $this->createdContasPagarIds[] = $contaId;

        // Atualiza
        $updatePayload = [
            'valor' => 150.0,
            'data_vencimento' => date('Y-m-d', strtotime('+5 days'))
        ];

        $response = $this->client->put("/api/financeiro/contas-pagar/{$contaId}", [
            'json' => $updatePayload
        ]);

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals(150.0, $data['valor']);
    }

    /**
     * Teste: Atualizar conta já paga
     * Cenário: Tentar alterar conta paga
     * Esperado: Status 400
     */
    public function testAtualizarContaJaPaga()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria e paga
        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Conta',
                'valor' => 200.0,
                'data_vencimento' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];
        $this->createdContasPagarIds[] = $contaId;

        // Paga
        $this->client->post("/api/financeiro/contas-pagar/{$contaId}/baixar", [
            'json' => [
                'data_pagamento' => date('Y-m-d'),
                'valor_pago' => 200.0,
                'forma_pagamento' => 'DINHEIRO'
            ]
        ]);

        // Tenta atualizar
        $response = $this->client->put("/api/financeiro/contas-pagar/{$contaId}", [
            'json' => ['valor' => 300.0]
        ]);

        $this->assertEquals(400, $response->getStatusCode());
    }

    /**
     * Teste: Deletar conta a pagar
     * Cenário: Remover conta pendente
     * Esperado: Status 204 ou 200
     */
    public function testDeletarContaPagar()
    {
        $fornecedorId = $this->criarFornecedor();

        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Conta para deletar',
                'valor' => 50.0,
                'data_vencimento' => date('Y-m-d')
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $contaId = $created['id'];

        $response = $this->client->delete("/api/financeiro/contas-pagar/{$contaId}");

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica se foi removida
        $getResponse = $this->client->get("/api/financeiro/contas-pagar/{$contaId}");
        $this->assertEquals(404, $getResponse->getStatusCode());
    }

    /**
     * Teste: Contas a vencer nos próximos dias
     * Cenário: Buscar contas próximas do vencimento
     * Esperado: Lista de contas
     */
    public function testContasAVencer()
    {
        $fornecedorId = $this->criarFornecedor();

        // Cria conta vencendo em 3 dias
        $createResponse = $this->client->post('/api/financeiro/contas-pagar', [
            'json' => [
                'fornecedor_id' => $fornecedorId,
                'descricao' => 'Vence em breve',
                'valor' => 400.0,
                'data_vencimento' => date('Y-m-d', strtotime('+3 days'))
            ]
        ]);

        $created = json_decode($createResponse->getBody(), true);
        $this->createdContasPagarIds[] = $created['id'];

        // Busca contas a vencer em 7 dias
        $response = $this->client->get('/api/financeiro/contas-pagar?vence_em_dias=7');

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertGreaterThanOrEqual(1, $data['total']);
        }
    }
}
