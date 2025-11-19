"""
Templates de email pré-configurados para o sistema
"""
from typing import Dict, Any
from datetime import datetime


class EmailTemplates:
    """
    Classe com templates de email HTML responsivos

    Templates disponíveis:
    - Confirmação de pedido
    - Status de pagamento (aprovado, pendente, cancelado)
    - Tracking de envio
    - Boas-vindas
    - Recuperação de carrinho
    - Redefinição de senha
    """

    @staticmethod
    def _get_base_template(content: str) -> str:
        """
        Template base responsivo

        Args:
            content: Conteúdo HTML a inserir

        Returns:
            HTML completo com estilo
        """
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .content {{
            padding: 30px;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #dee2e6;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background-color: #667eea;
            color: white !important;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
        }}
        .button:hover {{
            background-color: #5568d3;
        }}
        .info-box {{
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .alert-success {{
            background-color: #d4edda;
            border-color: #c3e6cb;
            border-left-color: #28a745;
            color: #155724;
        }}
        .alert-warning {{
            background-color: #fff3cd;
            border-color: #ffeeba;
            border-left-color: #ffc107;
            color: #856404;
        }}
        .alert-danger {{
            background-color: #f8d7da;
            border-color: #f5c6cb;
            border-left-color: #dc3545;
            color: #721c24;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .total-row {{
            font-weight: bold;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
        <div class="footer">
            <p><strong>SISCOM - Sistema de Gestão</strong></p>
            <p>Este é um email automático, por favor não responda.</p>
            <p>Se você tiver dúvidas, entre em contato conosco.</p>
        </div>
    </div>
</body>
</html>
"""

    @staticmethod
    def confirmacao_pedido(dados: Dict[str, Any]) -> Dict[str, str]:
        """
        Template de confirmação de pedido

        Args:
            dados: {
                "numero_pedido": str,
                "cliente_nome": str,
                "itens": [{"nome": str, "quantidade": int, "valor": float}],
                "subtotal": float,
                "frete": float,
                "desconto": float,
                "total": float,
                "forma_pagamento": str,
                "status_pagamento": str,
                "endereco_entrega": str
            }

        Returns:
            Dict com "assunto" e "html"
        """
        # Montar tabela de itens
        itens_html = ""
        for item in dados.get("itens", []):
            itens_html += f"""
            <tr>
                <td>{item['nome']}</td>
                <td style="text-align: center;">{item['quantidade']}</td>
                <td style="text-align: right;">R$ {item['valor']:.2f}</td>
            </tr>
            """

        content = f"""
        <div class="header">
            <h1>✅ Pedido Confirmado!</h1>
        </div>
        <div class="content">
            <p>Olá <strong>{dados.get('cliente_nome', 'Cliente')}</strong>,</p>

            <p>Seu pedido foi recebido com sucesso e está sendo processado.</p>

            <div class="info-box alert-success">
                <strong>Número do Pedido:</strong> #{dados.get('numero_pedido')}<br>
                <strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}
            </div>

            <h3>Itens do Pedido:</h3>
            <table>
                <thead>
                    <tr>
                        <th>Produto</th>
                        <th style="text-align: center;">Qtd</th>
                        <th style="text-align: right;">Valor</th>
                    </tr>
                </thead>
                <tbody>
                    {itens_html}
                    <tr>
                        <td colspan="2"><strong>Subtotal</strong></td>
                        <td style="text-align: right;">R$ {dados.get('subtotal', 0):.2f}</td>
                    </tr>
                    <tr>
                        <td colspan="2"><strong>Frete</strong></td>
                        <td style="text-align: right;">R$ {dados.get('frete', 0):.2f}</td>
                    </tr>
                    {f'''<tr>
                        <td colspan="2"><strong>Desconto</strong></td>
                        <td style="text-align: right; color: #28a745;">- R$ {dados.get('desconto', 0):.2f}</td>
                    </tr>''' if dados.get('desconto', 0) > 0 else ''}
                    <tr class="total-row">
                        <td colspan="2">TOTAL</td>
                        <td style="text-align: right; color: #667eea;">R$ {dados.get('total', 0):.2f}</td>
                    </tr>
                </tbody>
            </table>

            <div class="info-box">
                <strong>Forma de Pagamento:</strong> {dados.get('forma_pagamento', 'N/A')}<br>
                <strong>Status:</strong> {dados.get('status_pagamento', 'Pendente')}<br>
                <strong>Endereço de Entrega:</strong><br>
                {dados.get('endereco_entrega', 'N/A')}
            </div>

            <p>Você receberá atualizações sobre o status do seu pedido por email.</p>

            <center>
                <a href="#" class="button">Acompanhar Pedido</a>
            </center>
        </div>
        """

        return {
            "assunto": f"Pedido #{dados.get('numero_pedido')} confirmado!",
            "html": EmailTemplates._get_base_template(content)
        }

    @staticmethod
    def status_pagamento(dados: Dict[str, Any]) -> Dict[str, str]:
        """
        Template de atualização de status de pagamento

        Args:
            dados: {
                "numero_pedido": str,
                "cliente_nome": str,
                "status": str ("aprovado", "pendente", "cancelado", "estornado"),
                "valor": float,
                "forma_pagamento": str,
                "mensagem_adicional": str (opcional)
            }

        Returns:
            Dict com "assunto" e "html"
        """
        status = dados.get('status', 'pendente').lower()

        # Definir estilo baseado no status
        if status == "aprovado":
            icon = "✅"
            titulo = "Pagamento Aprovado!"
            alert_class = "alert-success"
            cor = "#28a745"
        elif status == "pendente":
            icon = "⏳"
            titulo = "Pagamento Pendente"
            alert_class = "alert-warning"
            cor = "#ffc107"
        else:  # cancelado, estornado
            icon = "❌"
            titulo = "Pagamento Não Processado"
            alert_class = "alert-danger"
            cor = "#dc3545"

        content = f"""
        <div class="header">
            <h1>{icon} {titulo}</h1>
        </div>
        <div class="content">
            <p>Olá <strong>{dados.get('cliente_nome', 'Cliente')}</strong>,</p>

            <p>O status do pagamento do seu pedido foi atualizado.</p>

            <div class="info-box {alert_class}">
                <strong>Pedido:</strong> #{dados.get('numero_pedido')}<br>
                <strong>Status:</strong> <span style="color: {cor};">{status.upper()}</span><br>
                <strong>Valor:</strong> R$ {dados.get('valor', 0):.2f}<br>
                <strong>Forma de Pagamento:</strong> {dados.get('forma_pagamento', 'N/A')}
            </div>

            {f"<p>{dados.get('mensagem_adicional')}</p>" if dados.get('mensagem_adicional') else ''}

            <center>
                <a href="#" class="button">Ver Detalhes do Pedido</a>
            </center>
        </div>
        """

        return {
            "assunto": f"Pedido #{dados.get('numero_pedido')} - {titulo}",
            "html": EmailTemplates._get_base_template(content)
        }

    @staticmethod
    def tracking_envio(dados: Dict[str, Any]) -> Dict[str, str]:
        """
        Template de tracking de envio

        Args:
            dados: {
                "numero_pedido": str,
                "cliente_nome": str,
                "codigo_rastreio": str,
                "transportadora": str,
                "previsao_entrega": str,
                "link_rastreamento": str (opcional)
            }

        Returns:
            Dict com "assunto" e "html"
        """
        content = f"""
        <div class="header">
            <h1>📦 Seu pedido foi enviado!</h1>
        </div>
        <div class="content">
            <p>Olá <strong>{dados.get('cliente_nome', 'Cliente')}</strong>,</p>

            <p>Temos boas notícias! Seu pedido já foi enviado e está a caminho.</p>

            <div class="info-box alert-success">
                <strong>Pedido:</strong> #{dados.get('numero_pedido')}<br>
                <strong>Código de Rastreamento:</strong> <code>{dados.get('codigo_rastreio')}</code><br>
                <strong>Transportadora:</strong> {dados.get('transportadora', 'N/A')}<br>
                <strong>Previsão de Entrega:</strong> {dados.get('previsao_entrega', 'A definir')}
            </div>

            <p>Você pode acompanhar o status da entrega usando o código de rastreamento acima.</p>

            {f'<center><a href="{dados.get("link_rastreamento")}" class="button">Rastrear Pedido</a></center>' if dados.get('link_rastreamento') else ''}
        </div>
        """

        return {
            "assunto": f"Pedido #{dados.get('numero_pedido')} enviado! 📦",
            "html": EmailTemplates._get_base_template(content)
        }

    @staticmethod
    def boas_vindas(dados: Dict[str, Any]) -> Dict[str, str]:
        """
        Template de boas-vindas para novos clientes

        Args:
            dados: {
                "nome": str,
                "email": str,
                "cupom_desconto": str (opcional)
            }

        Returns:
            Dict com "assunto" e "html"
        """
        content = f"""
        <div class="header">
            <h1>🎉 Bem-vindo(a)!</h1>
        </div>
        <div class="content">
            <p>Olá <strong>{dados.get('nome', 'Cliente')}</strong>,</p>

            <p>É um prazer ter você conosco! Seu cadastro foi realizado com sucesso.</p>

            <div class="info-box alert-success">
                <strong>Email cadastrado:</strong> {dados.get('email')}
            </div>

            {f'''
            <h3>🎁 Presente de Boas-Vindas</h3>
            <p>Como agradecimento, preparamos um desconto especial para você:</p>
            <div class="info-box" style="border-left-color: #28a745; text-align: center;">
                <h2 style="margin: 0; color: #28a745;">
                    CUPOM: <code style="font-size: 24px;">{dados.get('cupom_desconto')}</code>
                </h2>
                <p>Use este cupom na sua primeira compra!</p>
            </div>
            ''' if dados.get('cupom_desconto') else ''}

            <h3>Próximos Passos:</h3>
            <ul>
                <li>Navegue pelo nosso catálogo de produtos</li>
                <li>Configure suas preferências de conta</li>
                <li>Adicione seus endereços de entrega</li>
            </ul>

            <center>
                <a href="#" class="button">Começar a Comprar</a>
            </center>
        </div>
        """

        return {
            "assunto": "Bem-vindo(a) ao SISCOM! 🎉",
            "html": EmailTemplates._get_base_template(content)
        }

    @staticmethod
    def recuperacao_senha(dados: Dict[str, Any]) -> Dict[str, str]:
        """
        Template de recuperação de senha

        Args:
            dados: {
                "nome": str,
                "token": str,
                "link_reset": str,
                "expiracao": str (ex: "24 horas")
            }

        Returns:
            Dict com "assunto" e "html"
        """
        content = f"""
        <div class="header">
            <h1>🔐 Redefinição de Senha</h1>
        </div>
        <div class="content">
            <p>Olá <strong>{dados.get('nome', 'Cliente')}</strong>,</p>

            <p>Recebemos uma solicitação para redefinir a senha da sua conta.</p>

            <div class="info-box alert-warning">
                ⚠️ <strong>Importante:</strong> Se você não solicitou esta alteração, ignore este email.
                Sua senha permanecerá a mesma e sua conta está segura.
            </div>

            <p>Para criar uma nova senha, clique no botão abaixo:</p>

            <center>
                <a href="{dados.get('link_reset', '#')}" class="button">Redefinir Senha</a>
            </center>

            <p style="font-size: 12px; color: #666;">
                Ou copie e cole este link no seu navegador:<br>
                <code>{dados.get('link_reset', '#')}</code>
            </p>

            <div class="info-box">
                <strong>Validade:</strong> Este link expira em {dados.get('expiracao', '24 horas')}<br>
                <strong>Por segurança:</strong> Nunca compartilhe este link com ninguém
            </div>
        </div>
        """

        return {
            "assunto": "Redefinição de senha - SISCOM",
            "html": EmailTemplates._get_base_template(content)
        }

    @staticmethod
    def carrinho_abandonado(dados: Dict[str, Any]) -> Dict[str, str]:
        """
        Template de recuperação de carrinho abandonado

        Args:
            dados: {
                "nome": str,
                "itens": [{"nome": str, "imagem": str, "valor": float}],
                "total": float,
                "cupom_desconto": str (opcional),
                "link_carrinho": str
            }

        Returns:
            Dict com "assunto" e "html"
        """
        # Montar lista de itens
        itens_html = ""
        for item in dados.get("itens", [])[:3]:  # Mostrar máximo 3 itens
            itens_html += f"""
            <div style="border-bottom: 1px solid #dee2e6; padding: 15px 0;">
                <strong>{item['nome']}</strong><br>
                <span style="color: #667eea; font-size: 18px;">R$ {item['valor']:.2f}</span>
            </div>
            """

        content = f"""
        <div class="header">
            <h1>🛒 Você esqueceu algo?</h1>
        </div>
        <div class="content">
            <p>Olá <strong>{dados.get('nome', 'Cliente')}</strong>,</p>

            <p>Notamos que você deixou alguns itens no seu carrinho. Eles ainda estão te esperando!</p>

            <h3>Itens no seu carrinho:</h3>
            {itens_html}

            <div class="info-box" style="border-left-color: #667eea;">
                <strong>Total do Carrinho:</strong>
                <span style="font-size: 20px; color: #667eea;">R$ {dados.get('total', 0):.2f}</span>
            </div>

            {f'''
            <div class="info-box alert-success">
                🎁 <strong>Oferta Especial!</strong><br>
                Complete sua compra agora e ganhe <strong>{dados.get('cupom_desconto')}</strong> de desconto!
            </div>
            ''' if dados.get('cupom_desconto') else ''}

            <center>
                <a href="{dados.get('link_carrinho', '#')}" class="button">Finalizar Compra</a>
            </center>

            <p style="text-align: center; font-size: 12px; color: #666;">
                Este carrinho é válido por tempo limitado
            </p>
        </div>
        """

        return {
            "assunto": "Seu carrinho está te esperando! 🛒",
            "html": EmailTemplates._get_base_template(content)
        }
