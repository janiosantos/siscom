"""
Testes do módulo core/cache.py

Testa:
- CacheService (Redis e memória)
- Decorator @cached
- CacheManager
- Rate limiting
- Geração de chaves
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import pickle
import hashlib

from app.core.cache import (
    CacheService,
    CacheManager,
    cached,
    cache_service,
    cache_manager
)


# ========== Fixtures ==========

@pytest.fixture
def memory_cache():
    """Cache service usando memória (sem Redis)"""
    cache = CacheService(redis_url=None)
    cache._use_redis = False
    return cache


@pytest.fixture
async def redis_cache():
    """Cache service com Redis mockado"""
    cache = CacheService(redis_url="redis://localhost:6379/0")

    # Mock do cliente Redis
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.setex = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.exists = AsyncMock()
    mock_redis.keys = AsyncMock()
    mock_redis.incr = AsyncMock()
    mock_redis.expire = AsyncMock()
    mock_redis.dbsize = AsyncMock()
    mock_redis.info = AsyncMock()
    mock_redis.close = AsyncMock()

    cache._redis_client = mock_redis
    cache._use_redis = True

    return cache


@pytest.fixture
def cache_manager_memory(memory_cache):
    """CacheManager com cache em memória"""
    return CacheManager(memory_cache)


@pytest.fixture
def cache_manager_redis(redis_cache):
    """CacheManager com Redis mockado"""
    return CacheManager(redis_cache)


# ========== Testes CacheService - Memória ==========

class TestCacheServiceMemory:
    """Testes do CacheService usando memória"""

    @pytest.mark.asyncio
    async def test_set_and_get_memory(self, memory_cache):
        """Deve armazenar e recuperar valor da memória"""
        await memory_cache.set("test_key", "test_value")

        result = await memory_cache.get("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key_memory(self, memory_cache):
        """Deve retornar None para chave inexistente"""
        result = await memory_cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_complex_object_memory(self, memory_cache):
        """Deve armazenar objetos complexos"""
        data = {
            "id": 123,
            "nome": "Produto Teste",
            "precos": [10.5, 20.0, 30.5],
            "metadata": {"categoria": "test"}
        }

        await memory_cache.set("produto:123", data)
        result = await memory_cache.get("produto:123")

        assert result == data
        assert result["id"] == 123
        assert result["precos"] == [10.5, 20.0, 30.5]

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_cache):
        """Deve deletar chave da memória"""
        await memory_cache.set("to_delete", "value")
        assert await memory_cache.get("to_delete") == "value"

        deleted = await memory_cache.delete("to_delete")
        assert deleted is True
        assert await memory_cache.get("to_delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key_memory(self, memory_cache):
        """Deve retornar False ao deletar chave inexistente"""
        deleted = await memory_cache.delete("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_exists_memory(self, memory_cache):
        """Deve verificar existência de chave"""
        await memory_cache.set("exists_key", "value")

        assert await memory_cache.exists("exists_key") is True
        assert await memory_cache.exists("not_exists") is False

    @pytest.mark.asyncio
    async def test_clear_all_memory(self, memory_cache):
        """Deve limpar todo cache em memória"""
        await memory_cache.set("key1", "value1")
        await memory_cache.set("key2", "value2")
        await memory_cache.set("key3", "value3")

        count = await memory_cache.clear("*")
        assert count == 3
        assert await memory_cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_clear_pattern_memory(self, memory_cache):
        """Deve limpar cache por pattern"""
        await memory_cache.set("user:1", "user1")
        await memory_cache.set("user:2", "user2")
        await memory_cache.set("produto:1", "produto1")

        count = await memory_cache.clear("user:*")
        assert count == 2

        # Usuários foram removidos
        assert await memory_cache.get("user:1") is None
        assert await memory_cache.get("user:2") is None

        # Produto ainda existe
        assert await memory_cache.get("produto:1") == "produto1"

    @pytest.mark.asyncio
    async def test_invalidate_prefix_memory(self, memory_cache):
        """Deve invalidar por prefixo"""
        await memory_cache.set("produto:1", "p1")
        await memory_cache.set("produto:2", "p2")
        await memory_cache.set("categoria:1", "c1")

        count = await memory_cache.invalidate_prefix("produto:")
        assert count == 2
        assert await memory_cache.get("categoria:1") == "c1"

    def test_generate_key(self, memory_cache):
        """Deve gerar chave hash única"""
        key1 = memory_cache.generate_key("arg1", "arg2", param="value")
        key2 = memory_cache.generate_key("arg1", "arg2", param="value")
        key3 = memory_cache.generate_key("arg1", "arg2", param="different")

        # Mesmos argumentos geram mesma chave
        assert key1 == key2

        # Argumentos diferentes geram chaves diferentes
        assert key1 != key3

        # Chave deve ser hash MD5 (32 caracteres hexadecimais)
        assert len(key1) == 32
        assert all(c in "0123456789abcdef" for c in key1)

    def test_generate_key_ordering(self, memory_cache):
        """kwargs devem ser ordenados na geração de chave"""
        key1 = memory_cache.generate_key(a="1", b="2", c="3")
        key2 = memory_cache.generate_key(c="3", a="1", b="2")

        # Ordem dos kwargs não deve importar
        assert key1 == key2


# ========== Testes CacheService - Redis ==========

class TestCacheServiceRedis:
    """Testes do CacheService usando Redis (mockado)"""

    @pytest.mark.asyncio
    async def test_set_and_get_redis(self, redis_cache):
        """Deve armazenar e recuperar do Redis"""
        test_value = {"data": "test"}
        pickled = pickle.dumps(test_value)

        redis_cache._redis_client.get.return_value = pickled

        await redis_cache.set("test_key", test_value)
        result = await redis_cache.get("test_key")

        assert result == test_value
        redis_cache._redis_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_with_ttl_redis(self, redis_cache):
        """Deve armazenar com TTL no Redis"""
        test_value = "test"

        await redis_cache.set("test_key", test_value, ttl=300)

        redis_cache._redis_client.setex.assert_called_once()
        call_args = redis_cache._redis_client.setex.call_args
        assert call_args[0][0] == "test_key"  # key
        assert call_args[0][1] == 300  # ttl

    @pytest.mark.asyncio
    async def test_get_nonexistent_redis(self, redis_cache):
        """Deve retornar None para chave inexistente no Redis"""
        redis_cache._redis_client.get.return_value = None

        result = await redis_cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_redis(self, redis_cache):
        """Deve deletar chave do Redis"""
        await redis_cache.delete("to_delete")

        redis_cache._redis_client.delete.assert_called_once_with("to_delete")

    @pytest.mark.asyncio
    async def test_exists_redis(self, redis_cache):
        """Deve verificar existência no Redis"""
        redis_cache._redis_client.exists.return_value = 1

        exists = await redis_cache.exists("test_key")
        assert exists is True

        redis_cache._redis_client.exists.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_clear_pattern_redis(self, redis_cache):
        """Deve limpar por pattern no Redis"""
        redis_cache._redis_client.keys.return_value = [
            b"user:1", b"user:2", b"user:3"
        ]
        redis_cache._redis_client.delete.return_value = 3

        count = await redis_cache.clear("user:*")

        redis_cache._redis_client.keys.assert_called_once_with("user:*")
        redis_cache._redis_client.delete.assert_called_once()
        assert count == 3

    @pytest.mark.asyncio
    async def test_clear_no_keys_redis(self, redis_cache):
        """Deve retornar 0 quando nenhuma chave corresponde ao pattern"""
        redis_cache._redis_client.keys.return_value = []

        count = await redis_cache.clear("nonexistent:*")
        assert count == 0

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Deve conectar ao Redis com sucesso"""
        with patch("app.core.cache.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock()
            mock_from_url.return_value = mock_client

            cache = CacheService(redis_url="redis://localhost:6379/0")
            cache._use_redis = True

            await cache.connect()

            mock_from_url.assert_called_once()
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure_fallback(self):
        """Deve fazer fallback para memória em caso de falha"""
        with patch("app.core.cache.redis.from_url") as mock_from_url:
            mock_from_url.side_effect = Exception("Connection refused")

            cache = CacheService(redis_url="redis://localhost:6379/0")
            cache._use_redis = True

            await cache.connect()

            # Deve ter feito fallback para memória
            assert cache._use_redis is False

    @pytest.mark.asyncio
    async def test_disconnect(self, redis_cache):
        """Deve desconectar do Redis"""
        await redis_cache.disconnect()
        redis_cache._redis_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_error_fallback(self, redis_cache):
        """Deve retornar None em caso de erro no get"""
        redis_cache._redis_client.get.side_effect = Exception("Redis error")

        result = await redis_cache.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_error_returns_false(self, redis_cache):
        """Deve retornar False em caso de erro no set"""
        redis_cache._redis_client.set.side_effect = Exception("Redis error")

        result = await redis_cache.set("test_key", "value")
        assert result is False


# ========== Testes Decorator @cached ==========

class TestCachedDecorator:
    """Testes do decorator @cached"""

    @pytest.mark.asyncio
    async def test_cached_function_first_call(self, memory_cache):
        """Primeira chamada deve executar função e cachear resultado"""
        call_count = 0

        @cached(ttl=60, prefix="test")
        async def expensive_function(arg1: int, arg2: str):
            nonlocal call_count
            call_count += 1
            return f"{arg1}-{arg2}"

        # Usar o cache em memória
        with patch("app.core.cache.cache_service", memory_cache):
            result1 = await expensive_function(1, "test")
            assert result1 == "1-test"
            assert call_count == 1

            # Segunda chamada deve vir do cache
            result2 = await expensive_function(1, "test")
            assert result2 == "1-test"
            assert call_count == 1  # Não chamou função novamente

    @pytest.mark.asyncio
    async def test_cached_function_different_args(self, memory_cache):
        """Argumentos diferentes devem gerar cache separado"""
        call_count = 0

        @cached(ttl=60, prefix="test")
        async def get_data(id: int):
            nonlocal call_count
            call_count += 1
            return f"data-{id}"

        with patch("app.core.cache.cache_service", memory_cache):
            result1 = await get_data(1)
            result2 = await get_data(2)
            result3 = await get_data(1)  # Cache hit

            assert result1 == "data-1"
            assert result2 == "data-2"
            assert result3 == "data-1"
            assert call_count == 2  # Apenas 2 chamadas (id=1 e id=2)

    @pytest.mark.asyncio
    async def test_cached_invalidate(self, memory_cache):
        """Deve invalidar cache específico"""
        call_count = 0

        @cached(ttl=60, prefix="test")
        async def get_value(key: str):
            nonlocal call_count
            call_count += 1
            return f"value-{key}"

        with patch("app.core.cache.cache_service", memory_cache):
            # Primeira chamada
            result1 = await get_value("abc")
            assert call_count == 1

            # Cache hit
            result2 = await get_value("abc")
            assert call_count == 1

            # Invalidar cache
            await get_value.invalidate("abc")

            # Deve executar função novamente
            result3 = await get_value("abc")
            assert call_count == 2


# ========== Testes CacheManager ==========

class TestCacheManagerSessions:
    """Testes de gerenciamento de sessões"""

    @pytest.mark.asyncio
    async def test_set_and_get_session(self, cache_manager_memory):
        """Deve armazenar e recuperar sessão"""
        session_data = {
            "user_id": 123,
            "username": "testuser",
            "roles": ["user", "admin"]
        }

        await cache_manager_memory.set_session("session_abc", session_data, ttl=3600)
        result = await cache_manager_memory.get_session("session_abc")

        assert result == session_data
        assert result["user_id"] == 123

    @pytest.mark.asyncio
    async def test_delete_session(self, cache_manager_memory):
        """Deve deletar sessão"""
        await cache_manager_memory.set_session("session_xyz", {"data": "test"})

        result_before = await cache_manager_memory.get_session("session_xyz")
        assert result_before is not None

        await cache_manager_memory.delete_session("session_xyz")

        result_after = await cache_manager_memory.get_session("session_xyz")
        assert result_after is None


class TestCacheManagerProdutos:
    """Testes de cache de produtos"""

    @pytest.mark.asyncio
    async def test_set_and_get_produto(self, cache_manager_memory):
        """Deve armazenar e recuperar produto"""
        produto_data = {
            "id": 456,
            "nome": "Cimento",
            "preco": 32.90
        }

        await cache_manager_memory.set_produto(456, produto_data, ttl=600)
        result = await cache_manager_memory.get_produto(456)

        assert result == produto_data

    @pytest.mark.asyncio
    async def test_invalidate_produto(self, cache_manager_memory):
        """Deve invalidar cache de produto específico"""
        await cache_manager_memory.set_produto(789, {"nome": "Produto Teste"})

        assert await cache_manager_memory.get_produto(789) is not None

        await cache_manager_memory.invalidate_produto(789)

        assert await cache_manager_memory.get_produto(789) is None

    @pytest.mark.asyncio
    async def test_invalidate_all_produtos(self, cache_manager_memory):
        """Deve invalidar cache de todos os produtos"""
        await cache_manager_memory.set_produto(1, {"nome": "P1"})
        await cache_manager_memory.set_produto(2, {"nome": "P2"})
        await cache_manager_memory.set_produto(3, {"nome": "P3"})

        count = await cache_manager_memory.invalidate_all_produtos()

        assert count == 3
        assert await cache_manager_memory.get_produto(1) is None


class TestCacheManagerQueries:
    """Testes de cache de queries"""

    @pytest.mark.asyncio
    async def test_cache_and_get_query(self, cache_manager_memory):
        """Deve cachear resultado de query"""
        query_params = {"status": "ativo", "categoria": "ferramentas"}
        result = [
            {"id": 1, "nome": "Martelo"},
            {"id": 2, "nome": "Chave"}
        ]

        await cache_manager_memory.cache_query(
            "list_produtos",
            query_params,
            result,
            ttl=300
        )

        cached_result = await cache_manager_memory.get_cached_query(
            "list_produtos",
            query_params
        )

        assert cached_result == result

    @pytest.mark.asyncio
    async def test_get_cached_query_not_found(self, cache_manager_memory):
        """Deve retornar None para query não cacheada"""
        result = await cache_manager_memory.get_cached_query(
            "nonexistent_query",
            {"param": "value"}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_query(self, cache_manager_memory):
        """Deve invalidar queries por nome"""
        # Cachear múltiplas queries com mesmo nome mas params diferentes
        await cache_manager_memory.cache_query(
            "list_produtos", {"page": 1}, ["result1"], ttl=300
        )
        await cache_manager_memory.cache_query(
            "list_produtos", {"page": 2}, ["result2"], ttl=300
        )

        # Invalidar todas as queries "list_produtos"
        count = await cache_manager_memory.invalidate_query("list_produtos")

        assert count == 2


class TestCacheManagerRateLimit:
    """Testes de rate limiting"""

    @pytest.mark.asyncio
    async def test_increment_rate_limit_memory(self, cache_manager_memory):
        """Deve incrementar contador de rate limit"""
        count1 = await cache_manager_memory.increment_rate_limit("user:123", window=60)
        assert count1 == 1

        count2 = await cache_manager_memory.increment_rate_limit("user:123", window=60)
        assert count2 == 2

        count3 = await cache_manager_memory.increment_rate_limit("user:123", window=60)
        assert count3 == 3

    @pytest.mark.asyncio
    async def test_increment_rate_limit_redis(self, cache_manager_redis):
        """Deve incrementar usando INCR do Redis"""
        cache_manager_redis.cache._redis_client.incr.return_value = 1

        count = await cache_manager_redis.increment_rate_limit("user:456", window=60)

        assert count == 1
        cache_manager_redis.cache._redis_client.incr.assert_called_once()
        cache_manager_redis.cache._redis_client.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limit_different_identifiers(self, cache_manager_memory):
        """Rate limit deve ser independente por identificador"""
        count_user1 = await cache_manager_memory.increment_rate_limit("user:1")
        count_user2 = await cache_manager_memory.increment_rate_limit("user:2")

        assert count_user1 == 1
        assert count_user2 == 1


class TestCacheManagerStats:
    """Testes de estatísticas do cache"""

    @pytest.mark.asyncio
    async def test_get_stats_memory(self, cache_manager_memory):
        """Deve retornar stats do cache em memória"""
        # Adicionar algumas chaves
        await cache_manager_memory.cache.set("key1", "value1")
        await cache_manager_memory.cache.set("key2", "value2")

        stats = await cache_manager_memory.get_stats()

        assert stats["tipo"] == "memoria"
        assert stats["total_keys"] == 2

    @pytest.mark.asyncio
    async def test_get_stats_redis(self, cache_manager_redis):
        """Deve retornar stats do Redis"""
        cache_manager_redis.cache._redis_client.dbsize.return_value = 150
        cache_manager_redis.cache._redis_client.info.return_value = {
            "keyspace_hits": 1000,
            "keyspace_misses": 50,
            "used_memory_human": "2.5M"
        }

        stats = await cache_manager_redis.get_stats()

        assert stats["tipo"] == "redis"
        assert stats["total_keys"] == 150
        assert stats["hits"] == 1000
        assert stats["misses"] == 50
        assert stats["memoria_usada"] == "2.5M"

    @pytest.mark.asyncio
    async def test_get_stats_redis_error(self, cache_manager_redis):
        """Deve retornar erro nas stats em caso de falha"""
        cache_manager_redis.cache._redis_client.info.side_effect = Exception("Redis error")

        stats = await cache_manager_redis.get_stats()

        assert stats["tipo"] == "redis"
        assert "erro" in stats


# ========== Testes de Integração ==========

class TestCacheIntegration:
    """Testes de integração entre componentes"""

    @pytest.mark.asyncio
    async def test_full_session_cycle(self, cache_manager_memory):
        """Ciclo completo de sessão: criar -> acessar -> deletar"""
        session_id = "session_integration_test"
        session_data = {
            "user_id": 999,
            "username": "integration_user",
            "authenticated": True
        }

        # Criar sessão
        await cache_manager_memory.set_session(session_id, session_data)

        # Acessar sessão
        retrieved = await cache_manager_memory.get_session(session_id)
        assert retrieved == session_data

        # Deletar sessão
        await cache_manager_memory.delete_session(session_id)

        # Verificar que foi deletada
        deleted_check = await cache_manager_memory.get_session(session_id)
        assert deleted_check is None

    @pytest.mark.asyncio
    async def test_query_cache_lifecycle(self, cache_manager_memory):
        """Ciclo completo de cache de query"""
        query_name = "search_produtos"
        params1 = {"q": "cimento", "limit": 10}
        params2 = {"q": "tijolo", "limit": 10}

        result1 = [{"id": 1, "nome": "Cimento CP-II"}]
        result2 = [{"id": 2, "nome": "Tijolo Ceramico"}]

        # Cachear duas queries diferentes
        await cache_manager_memory.cache_query(query_name, params1, result1)
        await cache_manager_memory.cache_query(query_name, params2, result2)

        # Verificar que ambas estão cacheadas
        assert await cache_manager_memory.get_cached_query(query_name, params1) == result1
        assert await cache_manager_memory.get_cached_query(query_name, params2) == result2

        # Invalidar todas as queries desse tipo
        count = await cache_manager_memory.invalidate_query(query_name)
        assert count == 2

        # Verificar que foram invalidadas
        assert await cache_manager_memory.get_cached_query(query_name, params1) is None
        assert await cache_manager_memory.get_cached_query(query_name, params2) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
