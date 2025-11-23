# Scripts Utilitários

Scripts auxiliares para desenvolvimento e manutenção do projeto.

## 📋 Scripts Disponíveis

### `validate_ci_local.sh`

Script de **validação local do CI/CD** que executa verificações antes de fazer push para o GitHub, evitando erros no pipeline.

#### Uso

```bash
# Executar todas as validações
./scripts/validate_ci_local.sh
```

#### O que valida

1. ✅ **Sintaxe Python** - Compila arquivos Python principais
2. ✅ **Imports de modelos** - Verifica se todas as 36 classes existem
3. ✅ **Foreign keys** - Detecta referências incorretas a "usuarios"
4. ✅ **Schemas Pydantic** - Verifica campos obrigatórios
5. ✅ **Configuração bcrypt** - Valida CryptContext
6. ✅ **Funções de conversão** - Verifica retorno de enums

#### Quando usar

- ✅ **Antes de fazer commit** de mudanças em modelos
- ✅ **Antes de fazer push** para o repositório remoto
- ✅ **Ao adicionar novos modelos** ao projeto
- ✅ **Ao refatorar imports** ou estruturas

#### Output de sucesso

```
==================================================
🔍 Validação Local do CI/CD
==================================================

1️⃣  Verificando sintaxe Python...
   ✅ Sintaxe Python OK

2️⃣  Verificando imports do módulo auth...
   ✅ Módulo auth OK

3️⃣  Verificando foreign keys...
   ✅ Nenhuma referência incorreta a 'usuarios'

4️⃣  Verificando imports em app/models.py...
   ✅ Todos os imports verificados (36 classes)

5️⃣  Verificando schemas Pydantic...
   ✅ ChavePixBase tem campos obrigatórios

6️⃣  Verificando converter_status_mp...
   ✅ converter_status_mp retorna StatusPagamento enum

7️⃣  Verificando configuração bcrypt...
   ✅ CryptContext configurado corretamente

==================================================
✅ VALIDAÇÃO COMPLETA - TUDO OK!
==================================================

Você pode fazer push com segurança! 🚀
```

#### Benefícios

- 🚀 **Detecção rápida** de erros (segundos vs minutos no GitHub Actions)
- 💰 **Economia de recursos** do GitHub Actions
- ⚡ **Feedback imediato** durante desenvolvimento
- 🔒 **Menos commits** de correção no histórico

---

### `init_auth.py`

Inicializa o sistema de autenticação criando usuários e roles padrão.

#### Uso

```bash
python scripts/init_auth.py
```

---

### `backup/` (futuros)

Diretório para scripts de backup do banco de dados.

---

## 🔧 Integrando com Git Hooks (Opcional)

Para executar validações automaticamente antes de cada commit:

```bash
# Criar pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
./scripts/validate_ci_local.sh
EOF

chmod +x .git/hooks/pre-commit
```

## 📚 Referências

- [GitHub Actions CI/CD](.github/workflows/ci.yml)
- [Documentação de Testes](../docs/TESTING.md)
- [CLAUDE.md](../CLAUDE.md) - Guia completo do projeto
