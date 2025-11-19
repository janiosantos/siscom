"""
Script para inicializar autenticação e criar usuário superuser

Uso:
    python scripts/init_auth.py
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.modules.auth.models import User, Role, Permission, Base
from app.modules.auth.security import get_password_hash


# Permissões padrão do sistema
DEFAULT_PERMISSIONS = [
    # Categorias
    {"name": "categorias:create", "resource": "categorias", "action": "create", "description": "Criar categorias"},
    {"name": "categorias:read", "resource": "categorias", "action": "read", "description": "Ler categorias"},
    {"name": "categorias:update", "resource": "categorias", "action": "update", "description": "Atualizar categorias"},
    {"name": "categorias:delete", "resource": "categorias", "action": "delete", "description": "Deletar categorias"},

    # Produtos
    {"name": "produtos:create", "resource": "produtos", "action": "create", "description": "Criar produtos"},
    {"name": "produtos:read", "resource": "produtos", "action": "read", "description": "Ler produtos"},
    {"name": "produtos:update", "resource": "produtos", "action": "update", "description": "Atualizar produtos"},
    {"name": "produtos:delete", "resource": "produtos", "action": "delete", "description": "Deletar produtos"},

    # Estoque
    {"name": "estoque:create", "resource": "estoque", "action": "create", "description": "Criar movimentação de estoque"},
    {"name": "estoque:read", "resource": "estoque", "action": "read", "description": "Ler estoque"},
    {"name": "estoque:update", "resource": "estoque", "action": "update", "description": "Atualizar estoque"},
    {"name": "estoque:delete", "resource": "estoque", "action": "delete", "description": "Deletar movimentação de estoque"},

    # Vendas
    {"name": "vendas:create", "resource": "vendas", "action": "create", "description": "Criar vendas"},
    {"name": "vendas:read", "resource": "vendas", "action": "read", "description": "Ler vendas"},
    {"name": "vendas:update", "resource": "vendas", "action": "update", "description": "Atualizar vendas"},
    {"name": "vendas:delete", "resource": "vendas", "action": "delete", "description": "Deletar vendas"},
    {"name": "vendas:cancel", "resource": "vendas", "action": "cancel", "description": "Cancelar vendas"},

    # PDV
    {"name": "pdv:open", "resource": "pdv", "action": "open", "description": "Abrir caixa"},
    {"name": "pdv:close", "resource": "pdv", "action": "close", "description": "Fechar caixa"},
    {"name": "pdv:sale", "resource": "pdv", "action": "sale", "description": "Realizar venda no PDV"},

    # Financeiro
    {"name": "financeiro:create", "resource": "financeiro", "action": "create", "description": "Criar contas"},
    {"name": "financeiro:read", "resource": "financeiro", "action": "read", "description": "Ler contas"},
    {"name": "financeiro:update", "resource": "financeiro", "action": "update", "description": "Atualizar contas"},
    {"name": "financeiro:delete", "resource": "financeiro", "action": "delete", "description": "Deletar contas"},
    {"name": "financeiro:pay", "resource": "financeiro", "action": "pay", "description": "Pagar contas"},

    # Clientes
    {"name": "clientes:create", "resource": "clientes", "action": "create", "description": "Criar clientes"},
    {"name": "clientes:read", "resource": "clientes", "action": "read", "description": "Ler clientes"},
    {"name": "clientes:update", "resource": "clientes", "action": "update", "description": "Atualizar clientes"},
    {"name": "clientes:delete", "resource": "clientes", "action": "delete", "description": "Deletar clientes"},

    # Fornecedores
    {"name": "fornecedores:create", "resource": "fornecedores", "action": "create", "description": "Criar fornecedores"},
    {"name": "fornecedores:read", "resource": "fornecedores", "action": "read", "description": "Ler fornecedores"},
    {"name": "fornecedores:update", "resource": "fornecedores", "action": "update", "description": "Atualizar fornecedores"},
    {"name": "fornecedores:delete", "resource": "fornecedores", "action": "delete", "description": "Deletar fornecedores"},

    # Compras
    {"name": "compras:create", "resource": "compras", "action": "create", "description": "Criar compras"},
    {"name": "compras:read", "resource": "compras", "action": "read", "description": "Ler compras"},
    {"name": "compras:update", "resource": "compras", "action": "update", "description": "Atualizar compras"},
    {"name": "compras:delete", "resource": "compras", "action": "delete", "description": "Deletar compras"},

    # NF-e
    {"name": "nfe:create", "resource": "nfe", "action": "create", "description": "Emitir NF-e"},
    {"name": "nfe:read", "resource": "nfe", "action": "read", "description": "Ler NF-e"},
    {"name": "nfe:cancel", "resource": "nfe", "action": "cancel", "description": "Cancelar NF-e"},

    # Relatórios
    {"name": "relatorios:read", "resource": "relatorios", "action": "read", "description": "Visualizar relatórios"},
    {"name": "relatorios:export", "resource": "relatorios", "action": "export", "description": "Exportar relatórios"},

    # Dashboard
    {"name": "dashboard:read", "resource": "dashboard", "action": "read", "description": "Visualizar dashboard"},

    # CRM
    {"name": "crm:read", "resource": "crm", "action": "read", "description": "Visualizar CRM"},
    {"name": "crm:manage", "resource": "crm", "action": "manage", "description": "Gerenciar CRM"},

    # E-commerce
    {"name": "ecommerce:manage", "resource": "ecommerce", "action": "manage", "description": "Gerenciar e-commerce"},
]


# Roles padrão
DEFAULT_ROLES = [
    {
        "name": "Administrador",
        "description": "Acesso total ao sistema",
        "permissions": "ALL"  # Todas as permissões
    },
    {
        "name": "Gerente",
        "description": "Gerente de loja com acesso a vendas, estoque e relatórios",
        "permissions": [
            "produtos:read", "produtos:create", "produtos:update",
            "estoque:read", "estoque:create", "estoque:update",
            "vendas:read", "vendas:create", "vendas:update", "vendas:cancel",
            "pdv:open", "pdv:close", "pdv:sale",
            "clientes:read", "clientes:create", "clientes:update",
            "relatorios:read", "relatorios:export",
            "dashboard:read",
        ]
    },
    {
        "name": "Vendedor",
        "description": "Vendedor com acesso a vendas e PDV",
        "permissions": [
            "produtos:read",
            "vendas:read", "vendas:create",
            "pdv:sale",
            "clientes:read", "clientes:create",
            "dashboard:read",
        ]
    },
    {
        "name": "Estoquista",
        "description": "Responsável pelo controle de estoque",
        "permissions": [
            "produtos:read",
            "estoque:read", "estoque:create", "estoque:update",
            "compras:read",
        ]
    },
    {
        "name": "Financeiro",
        "description": "Responsável pelo setor financeiro",
        "permissions": [
            "financeiro:read", "financeiro:create", "financeiro:update", "financeiro:pay",
            "relatorios:read", "relatorios:export",
            "dashboard:read",
        ]
    },
]


async def init_permissions(session: AsyncSession):
    """Cria permissões padrão"""
    print("Criando permissões...")

    created_count = 0
    for perm_data in DEFAULT_PERMISSIONS:
        # Verifica se já existe
        result = await session.execute(
            select(Permission).where(Permission.name == perm_data["name"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            permission = Permission(**perm_data)
            session.add(permission)
            created_count += 1

    await session.commit()
    print(f"✓ {created_count} permissões criadas")


async def init_roles(session: AsyncSession):
    """Cria roles padrão"""
    print("\nCriando roles...")

    # Busca todas as permissões
    result = await session.execute(select(Permission))
    all_permissions = list(result.scalars().all())

    created_count = 0
    for role_data in DEFAULT_ROLES:
        # Verifica se já existe
        result = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            role = Role(
                name=role_data["name"],
                description=role_data["description"]
            )

            # Atribui permissões
            if role_data["permissions"] == "ALL":
                role.permissions = all_permissions
            else:
                role_permissions = []
                for perm_name in role_data["permissions"]:
                    perm = next((p for p in all_permissions if p.name == perm_name), None)
                    if perm:
                        role_permissions.append(perm)
                role.permissions = role_permissions

            session.add(role)
            created_count += 1

    await session.commit()
    print(f"✓ {created_count} roles criados")


async def create_superuser(session: AsyncSession):
    """Cria usuário superuser"""
    print("\nCriando superuser...")

    # Verifica se já existe um superuser
    result = await session.execute(
        select(User).where(User.is_superuser == True)
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"✓ Superuser já existe: {existing.username}")
        return

    # Solicita dados do superuser
    username = input("Username do superuser: ").strip()
    email = input("Email do superuser: ").strip()
    full_name = input("Nome completo: ").strip()
    password = input("Senha (mín. 8 caracteres): ").strip()

    if len(password) < 8:
        print("✗ Senha deve ter no mínimo 8 caracteres")
        return

    # Cria superuser
    superuser = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        is_active=True,
        is_superuser=True
    )

    # Atribui role de Administrador
    result = await session.execute(
        select(Role).where(Role.name == "Administrador")
    )
    admin_role = result.scalar_one_or_none()
    if admin_role:
        superuser.roles = [admin_role]

    session.add(superuser)
    await session.commit()

    print(f"✓ Superuser criado: {username}")


async def main():
    """Função principal"""
    print("=" * 60)
    print("Inicialização de Autenticação e Autorização")
    print("=" * 60)

    # Cria engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    # Cria sessão
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        # Cria tabelas (se não existirem)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Inicializa permissões
        await init_permissions(session)

        # Inicializa roles
        await init_roles(session)

        # Cria superuser
        await create_superuser(session)

    print("\n" + "=" * 60)
    print("Inicialização concluída!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
