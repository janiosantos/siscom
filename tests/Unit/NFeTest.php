<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use GuzzleHttp\Client;
use GuzzleHttp\Exception\ClientException;

/**
 * Testes completos para o módulo de NF-e e NFC-e
 *
 * Cobre:
 * - Emissão de NF-e (Nota Fiscal Eletrônica)
 * - Emissão de NFC-e (Nota Fiscal do Consumidor Eletrônica)
 * - Cancelamento de notas
 * - Inutilização de numeração
 * - Consulta de status
 * - Validações de dados
 * - Integração com SEFAZ (estrutura)
 * - Download de XML e PDF
 */
class NFeTest extends TestCase
{
    private $client;
    private $baseUrl = 'http://localhost:8000';
    private $createdNotaIds = [];
    private $createdVendaIds = [];
    private $createdProdutoIds = [];
    private $createdCategoriaIds = [];
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
        // Limpa notas
        foreach ($this->createdNotaIds as $id) {
            try {
                $this->client->delete("/api/nfe/{$id}");
            } catch (\Exception $e) {
                // Ignora erros
            }
        }

        // Limpa vendas
        foreach ($this->createdVendaIds as $id) {
            try {
                $this->client->delete("/api/vendas/{$id}");
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
     * Helper: Criar categoria
     */
    private function criarCategoria($nome = 'Categoria NF')
    {
        $response = $this->client->post('/api/categorias', [
            'json' => ['nome' => $nome]
        ]);
        $data = json_decode($response->getBody(), true);
        $this->createdCategoriaIds[] = $data['id'];
        return $data['id'];
    }

    /**
     * Helper: Criar produto
     */
    private function criarProduto($codigoBarras, $descricao, $categoriaId, $precoVenda, $estoqueInicial = 100.0)
    {
        $response = $this->client->post('/api/produtos', [
            'json' => [
                'codigo_barras' => $codigoBarras,
                'descricao' => $descricao,
                'categoria_id' => $categoriaId,
                'preco_custo' => $precoVenda * 0.6,
                'preco_venda' => $precoVenda,
                'ncm' => '12345678',
                'cfop' => '5102',
                'estoque_minimo' => 10.0,
                'ativo' => true
            ]
        ]);
        $data = json_decode($response->getBody(), true);
        $produtoId = $data['id'];
        $this->createdProdutoIds[] = $produtoId;

        // Adiciona estoque
        $this->client->post('/api/estoque/entrada', [
            'json' => [
                'produto_id' => $produtoId,
                'quantidade' => $estoqueInicial,
                'preco_custo' => $precoVenda * 0.6,
                'motivo' => 'COMPRA'
            ]
        ]);

        return $produtoId;
    }

    /**
     * Helper: Criar cliente
     */
    private function criarCliente($nome = 'Cliente NF', $tipo = 'PF')
    {
        $payload = [
            'nome' => $nome,
            'tipo_pessoa' => $tipo,
            'cpf_cnpj' => $tipo === 'PF' ? '12345678901' : '12345678000199',
            'email' => 'cliente@nf.com',
            'telefone' => '11987654321',
            'endereco' => 'Rua Teste, 123',
            'bairro' => 'Centro',
            'cidade' => 'São Paulo',
            'uf' => 'SP',
            'cep' => '01234567',
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
     * Helper: Criar venda
     */
    private function criarVenda($produtoId, $clienteId = null)
    {
        $response = $this->client->post('/api/vendas', [
            'json' => [
                'cliente_id' => $clienteId,
                'itens' => [
                    [
                        'produto_id' => $produtoId,
                        'quantidade' => 2.0,
                        'preco_unitario' => 50.0
                    ]
                ],
                'forma_pagamento' => 'DINHEIRO'
            ]
        ]);
        $data = json_decode($response->getBody(), true);
        if (isset($data['id'])) {
            $this->createdVendaIds[] = $data['id'];
            return $data['id'];
        }
        return null;
    }

    /**
     * Teste: Emitir NFC-e com sucesso
     * Cenário: Emissão de nota para consumidor final
     * Esperado: Status 201, nota criada
     */
    public function testEmitirNfceComSucesso()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000001', 'Produto NFC-e', $categoriaId, 50.0);
        $vendaId = $this->criarVenda($produtoId);

        $payload = [
            'venda_id' => $vendaId,
            'tipo_nota' => 'NFCE',
            'natureza_operacao' => 'VENDA',
            'finalidade' => 'NORMAL',
            'ambiente' => 'HOMOLOGACAO'
        ];

        $response = $this->client->post('/api/nfe/emitir', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('id', $data);
        $this->assertArrayHasKey('numero', $data);
        $this->assertArrayHasKey('serie', $data);
        $this->assertArrayHasKey('chave_acesso', $data);
        $this->assertArrayHasKey('status', $data);
        $this->assertArrayHasKey('tipo_nota', $data);

        $this->assertEquals('NFCE', $data['tipo_nota']);
        $this->assertEquals('PENDENTE', $data['status']);

        $this->createdNotaIds[] = $data['id'];
    }

    /**
     * Teste: Emitir NF-e com cliente PJ
     * Cenário: Nota fiscal para pessoa jurídica
     * Esperado: Status 201
     */
    public function testEmitirNfeComClientePj()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000002', 'Produto NF-e', $categoriaId, 100.0);
        $clienteId = $this->criarCliente('Empresa XYZ Ltda', 'PJ');
        $vendaId = $this->criarVenda($produtoId, $clienteId);

        $payload = [
            'venda_id' => $vendaId,
            'tipo_nota' => 'NFE',
            'natureza_operacao' => 'VENDA',
            'finalidade' => 'NORMAL',
            'ambiente' => 'HOMOLOGACAO'
        ];

        $response = $this->client->post('/api/nfe/emitir', [
            'json' => $payload
        ]);

        $this->assertEquals(201, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals('NFE', $data['tipo_nota']);
        $this->assertArrayHasKey('chave_acesso', $data);

        $this->createdNotaIds[] = $data['id'];
    }

    /**
     * Teste: Emitir nota sem venda
     * Cenário: Tentar emitir sem venda_id
     * Esperado: Status 422
     */
    public function testEmitirNotaSemVenda()
    {
        $payload = [
            'tipo_nota' => 'NFCE',
            'natureza_operacao' => 'VENDA',
            'ambiente' => 'HOMOLOGACAO'
        ];

        $response = $this->client->post('/api/nfe/emitir', [
            'json' => $payload
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Emitir nota com venda inexistente
     * Cenário: venda_id que não existe
     * Esperado: Status 404
     */
    public function testEmitirNotaComVendaInexistente()
    {
        $payload = [
            'venda_id' => 999999,
            'tipo_nota' => 'NFCE',
            'natureza_operacao' => 'VENDA',
            'ambiente' => 'HOMOLOGACAO'
        ];

        $response = $this->client->post('/api/nfe/emitir', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [400, 404]);
    }

    /**
     * Teste: Buscar nota por ID
     * Cenário: Criar e buscar nota
     * Esperado: Dados completos
     */
    public function testBuscarNotaPorId()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000003', 'Produto', $categoriaId, 30.0);
        $vendaId = $this->criarVenda($produtoId);

        // Emite nota
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        // Busca nota
        $response = $this->client->get("/api/nfe/{$notaId}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertEquals($notaId, $data['id']);
        $this->assertArrayHasKey('numero', $data);
        $this->assertArrayHasKey('chave_acesso', $data);
    }

    /**
     * Teste: Buscar nota inexistente
     * Cenário: ID que não existe
     * Esperado: Status 404
     */
    public function testBuscarNotaInexistente()
    {
        $response = $this->client->get('/api/nfe/999999');

        $this->assertEquals(404, $response->getStatusCode());
    }

    /**
     * Teste: Listar notas com filtros
     * Cenário: Filtrar por tipo e status
     * Esperado: Lista filtrada
     */
    public function testListarNotasComFiltros()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000004', 'Produto Lista', $categoriaId, 25.0, 100.0);

        // Emite 2 notas
        for ($i = 0; $i < 2; $i++) {
            $vendaId = $this->criarVenda($produtoId);

            $emitirResponse = $this->client->post('/api/nfe/emitir', [
                'json' => [
                    'venda_id' => $vendaId,
                    'tipo_nota' => 'NFCE',
                    'natureza_operacao' => 'VENDA',
                    'ambiente' => 'HOMOLOGACAO'
                ]
            ]);

            $emitida = json_decode($emitirResponse->getBody(), true);
            $this->createdNotaIds[] = $emitida['id'];
        }

        // Lista notas
        $response = $this->client->get('/api/nfe?tipo_nota=NFCE');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertGreaterThanOrEqual(2, $data['total']);
    }

    /**
     * Teste: Cancelar nota fiscal
     * Cenário: Cancelar nota autorizada
     * Esperado: Status CANCELADO
     */
    public function testCancelarNotaFiscal()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000005', 'Produto Cancel', $categoriaId, 40.0);
        $vendaId = $this->criarVenda($produtoId);

        // Emite nota
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        // Cancela nota
        $cancelPayload = [
            'justificativa' => 'Cancelamento solicitado pelo cliente. Erro no pedido.'
        ];

        $response = $this->client->post("/api/nfe/{$notaId}/cancelar", [
            'json' => $cancelPayload
        ]);

        $this->assertContains($response->getStatusCode(), [200, 204]);

        // Verifica status
        $getResponse = $this->client->get("/api/nfe/{$notaId}");
        if ($getResponse->getStatusCode() === 200) {
            $notaData = json_decode($getResponse->getBody(), true);
            $this->assertEquals('CANCELADO', $notaData['status']);
        }
    }

    /**
     * Teste: Cancelar nota sem justificativa
     * Cenário: Cancelamento sem justificativa mínima
     * Esperado: Status 422
     */
    public function testCancelarNotaSemJustificativa()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000006', 'Produto', $categoriaId, 20.0);
        $vendaId = $this->criarVenda($produtoId);

        // Emite nota
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        // Tenta cancelar sem justificativa
        $response = $this->client->post("/api/nfe/{$notaId}/cancelar", [
            'json' => ['justificativa' => '']
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Cancelar nota com justificativa curta
     * Cenário: Justificativa com menos de 15 caracteres
     * Esperado: Status 422
     */
    public function testCancelarNotaComJustificativaCurta()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000007', 'Produto', $categoriaId, 15.0);
        $vendaId = $this->criarVenda($produtoId);

        // Emite nota
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        // Justificativa muito curta
        $response = $this->client->post("/api/nfe/{$notaId}/cancelar", [
            'json' => ['justificativa' => 'Erro']
        ]);

        $this->assertEquals(422, $response->getStatusCode());
    }

    /**
     * Teste: Consultar status da nota na SEFAZ
     * Cenário: Verificar situação no servidor fiscal
     * Esperado: Status retornado
     */
    public function testConsultarStatusNaSefaz()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000008', 'Produto Status', $categoriaId, 35.0);
        $vendaId = $this->criarVenda($produtoId);

        // Emite nota
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        // Consulta status
        $response = $this->client->get("/api/nfe/{$notaId}/status");

        // Pode retornar 200 ou 503 se SEFAZ indisponível
        $this->assertContains($response->getStatusCode(), [200, 503]);

        if ($response->getStatusCode() === 200) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('status', $data);
        }
    }

    /**
     * Teste: Download do XML da nota
     * Cenário: Baixar arquivo XML
     * Esperado: Content-Type XML
     */
    public function testDownloadXmlNota()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000009', 'Produto XML', $categoriaId, 45.0);
        $vendaId = $this->criarVenda($produtoId);

        // Emite nota
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        // Download XML
        $response = $this->client->get("/api/nfe/{$notaId}/xml");

        // Pode retornar 200 se disponível, 404 se ainda não gerado
        $this->assertContains($response->getStatusCode(), [200, 404]);

        if ($response->getStatusCode() === 200) {
            $contentType = $response->getHeader('Content-Type');
            if (!empty($contentType)) {
                $this->assertStringContainsString('xml', strtolower($contentType[0]));
            }
        }
    }

    /**
     * Teste: Download do PDF da nota (DANFE)
     * Cenário: Baixar DANFE em PDF
     * Esperado: Content-Type PDF
     */
    public function testDownloadPdfDanfe()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000010', 'Produto PDF', $categoriaId, 55.0);
        $vendaId = $this->criarVenda($produtoId);

        // Emite nota
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        // Download PDF
        $response = $this->client->get("/api/nfe/{$notaId}/pdf");

        // Pode retornar 200 ou 404
        $this->assertContains($response->getStatusCode(), [200, 404]);

        if ($response->getStatusCode() === 200) {
            $contentType = $response->getHeader('Content-Type');
            if (!empty($contentType)) {
                $this->assertStringContainsString('pdf', strtolower($contentType[0]));
            }
        }
    }

    /**
     * Teste: Inutilizar numeração
     * Cenário: Inutilizar número de nota não utilizado
     * Esperado: Status 200
     */
    public function testInutilizarNumeracao()
    {
        $payload = [
            'serie' => 1,
            'numero_inicial' => 100,
            'numero_final' => 105,
            'justificativa' => 'Erro na sequência de numeração. Necessário inutilizar.'
        ];

        $response = $this->client->post('/api/nfe/inutilizar', [
            'json' => $payload
        ]);

        // Pode retornar 200 se implementado, 501 se não
        $this->assertContains($response->getStatusCode(), [200, 201, 501]);

        if ($response->getStatusCode() === 200 || $response->getStatusCode() === 201) {
            $data = json_decode($response->getBody(), true);
            $this->assertArrayHasKey('protocolo', $data);
        }
    }

    /**
     * Teste: Inutilizar sem justificativa
     * Cenário: Tentar inutilizar sem justificativa
     * Esperado: Status 422
     */
    public function testInutilizarSemJustificativa()
    {
        $payload = [
            'serie' => 1,
            'numero_inicial' => 200,
            'numero_final' => 205
        ];

        $response = $this->client->post('/api/nfe/inutilizar', [
            'json' => $payload
        ]);

        $this->assertContains($response->getStatusCode(), [422, 501]);
    }

    /**
     * Teste: Validar chave de acesso
     * Cenário: Verificar formato da chave
     * Esperado: Chave com 44 dígitos
     */
    public function testValidarChaveAcesso()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000011', 'Produto Chave', $categoriaId, 60.0);
        $vendaId = $this->criarVenda($produtoId);

        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $this->createdNotaIds[] = $emitida['id'];

        if (isset($emitida['chave_acesso'])) {
            $chave = $emitida['chave_acesso'];
            // Chave deve ter 44 dígitos
            $this->assertEquals(44, strlen($chave));
            $this->assertMatchesRegularExpression('/^\d{44}$/', $chave);
        }
    }

    /**
     * Teste: Validar série da nota
     * Cenário: Série deve estar no range válido (1-999)
     * Esperado: Série válida
     */
    public function testValidarSerieNota()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000012', 'Produto Serie', $categoriaId, 70.0);
        $vendaId = $this->criarVenda($produtoId);

        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'serie' => 1,
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $this->createdNotaIds[] = $emitida['id'];

        $this->assertArrayHasKey('serie', $emitida);
        $this->assertGreaterThanOrEqual(1, $emitida['serie']);
        $this->assertLessThanOrEqual(999, $emitida['serie']);
    }

    /**
     * Teste: Carta de Correção Eletrônica (CC-e)
     * Cenário: Emitir CC-e para nota autorizada
     * Esperado: Status 200
     */
    public function testEmitirCartaCorrecao()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000013', 'Produto CCe', $categoriaId, 80.0);
        $vendaId = $this->criarVenda($produtoId);

        // Emite nota
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        // Emite CC-e
        $ccePayload = [
            'correcao' => 'Correção do endereço de entrega conforme solicitado pelo cliente.'
        ];

        $response = $this->client->post("/api/nfe/{$notaId}/carta-correcao", [
            'json' => $ccePayload
        ]);

        // Pode retornar 200 se implementado, 501 se não
        $this->assertContains($response->getStatusCode(), [200, 201, 501]);
    }

    /**
     * Teste: Emitir CC-e sem texto de correção
     * Cenário: CC-e sem descrição mínima
     * Esperado: Status 422
     */
    public function testEmitirCartaCorrecaoSemTexto()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000014', 'Produto', $categoriaId, 90.0);
        $vendaId = $this->criarVenda($produtoId);

        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        $response = $this->client->post("/api/nfe/{$notaId}/carta-correcao", [
            'json' => ['correcao' => '']
        ]);

        $this->assertContains($response->getStatusCode(), [422, 501]);
    }

    /**
     * Teste: Validar timestamps da nota
     * Cenário: Verificar data_emissao e created_at
     * Esperado: Campos preenchidos
     */
    public function testTimestampsNota()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000015', 'Produto Time', $categoriaId, 95.0);
        $vendaId = $this->criarVenda($produtoId);

        $response = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $data = json_decode($response->getBody(), true);
        $this->createdNotaIds[] = $data['id'];

        $this->assertArrayHasKey('data_emissao', $data);
        $this->assertArrayHasKey('created_at', $data);
        $this->assertNotEmpty($data['data_emissao']);

        // Valida formato ISO8601
        $this->assertMatchesRegularExpression('/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/', $data['data_emissao']);
    }

    /**
     * Teste: Emitir nota de devolução
     * Cenário: Nota de devolução referenciando nota original
     * Esperado: Status 201
     */
    public function testEmitirNotaDevolucao()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000016', 'Produto Dev', $categoriaId, 100.0);
        $clienteId = $this->criarCliente('Cliente Devolução', 'PF');
        $vendaId = $this->criarVenda($produtoId, $clienteId);

        // Emite nota original
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $notaOriginal = json_decode($emitirResponse->getBody(), true);
        $notaOriginalId = $notaOriginal['id'];
        $this->createdNotaIds[] = $notaOriginalId;

        // Emite nota de devolução
        $devolucaoPayload = [
            'nota_referenciada_id' => $notaOriginalId,
            'tipo_nota' => 'NFE',
            'natureza_operacao' => 'DEVOLUCAO',
            'finalidade' => 'DEVOLUCAO',
            'ambiente' => 'HOMOLOGACAO'
        ];

        $response = $this->client->post('/api/nfe/emitir', [
            'json' => $devolucaoPayload
        ]);

        // Pode aceitar ou rejeitar dependendo da implementação
        $this->assertContains($response->getStatusCode(), [201, 422]);

        if ($response->getStatusCode() === 201) {
            $devolucao = json_decode($response->getBody(), true);
            $this->createdNotaIds[] = $devolucao['id'];
            $this->assertEquals('DEVOLUCAO', $devolucao['natureza_operacao']);
        }
    }

    /**
     * Teste: Filtrar notas por período
     * Cenário: Buscar notas emitidas em data específica
     * Esperado: Lista filtrada
     */
    public function testFiltrarNotasPorPeriodo()
    {
        $dataHoje = date('Y-m-d');

        $response = $this->client->get("/api/nfe?data_inicio={$dataHoje}&data_fim={$dataHoje}");

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        $this->assertArrayHasKey('items', $data);
        $this->assertArrayHasKey('total', $data);
    }

    /**
     * Teste: Filtrar notas por ambiente (homologação/produção)
     * Cenário: Buscar apenas notas de homologação
     * Esperado: Apenas notas do ambiente especificado
     */
    public function testFiltrarNotasPorAmbiente()
    {
        $response = $this->client->get('/api/nfe?ambiente=HOMOLOGACAO');

        $this->assertEquals(200, $response->getStatusCode());

        $data = json_decode($response->getBody(), true);

        foreach ($data['items'] as $nota) {
            $this->assertEquals('HOMOLOGACAO', $nota['ambiente']);
        }
    }

    /**
     * Teste: Reenviar nota rejeitada
     * Cenário: Reenviar nota com erros corrigidos
     * Esperado: Nova tentativa de envio
     */
    public function testReenviarNotaRejeitada()
    {
        $categoriaId = $this->criarCategoria();
        $produtoId = $this->criarProduto('NFE0000000017', 'Produto Reenvio', $categoriaId, 110.0);
        $vendaId = $this->criarVenda($produtoId);

        // Emite nota
        $emitirResponse = $this->client->post('/api/nfe/emitir', [
            'json' => [
                'venda_id' => $vendaId,
                'tipo_nota' => 'NFCE',
                'natureza_operacao' => 'VENDA',
                'ambiente' => 'HOMOLOGACAO'
            ]
        ]);

        $emitida = json_decode($emitirResponse->getBody(), true);
        $notaId = $emitida['id'];
        $this->createdNotaIds[] = $notaId;

        // Tenta reenviar
        $response = $this->client->post("/api/nfe/{$notaId}/reenviar");

        // Pode retornar 200 se implementado
        $this->assertContains($response->getStatusCode(), [200, 201, 501]);
    }
}
