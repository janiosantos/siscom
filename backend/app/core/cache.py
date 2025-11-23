"""
Redis Cache Service - Sistema de cache distribuído
"""
import logging
import json
import pickle
from typing import Any, Optional, Callable
from functools import wraps
from datetime import timedelta
import hashlib

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("Redis não disponível. Cache em memória será usado.")
    REDIS_AVAILABLE = False


class CacheService:
    """Serviço de cache com suporte a Redis e fallback para memória"""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self._redis_client: Optional[redis.Redis] = None
        self._memory_cache: dict = {}  # Fallback para memória
        self._use_redis = REDIS_AVAILABLE and redis_url is not None

    async def connect(self):
        """Conecta ao Redis"""
        if not self._use_redis:
            logger.info("Usando cache em memória (Redis não disponível)")
            return

        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # Vamos usar pickle para objetos complexos
            )
            # Testar conexão
            await self._redis_client.ping()
            logger.info(f"Conectado ao Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {str(e)}")
            logger.info("Fallback para cache em memória")
            self._use_redis = False
            self._redis_client = None

    async def disconnect(self):
        """Desconecta do Redis"""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Desconectado do Redis")

    async def get(self, key: str) -> Optional[Any]:
        """
        Busca valor do cache

        Args:
            key: Chave do cache

        Returns:
            Valor armazenado ou None
        """
        if self._use_redis and self._redis_client:
            try:
                value = await self._redis_client.get(key)
                if value:
                    return pickle.loads(value)
                return None
            except Exception as e:
                logger.error(f"Erro ao buscar do Redis: {str(e)}")
                return None
        else:
            # Cache em memória
            return self._memory_cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Armazena valor no cache

        Args:
            key: Chave do cache
            value: Valor a armazenar
            ttl: Time to live em segundos (None = sem expiração)

        Returns:
            True se sucesso
        """
        if self._use_redis and self._redis_client:
            try:
                pickled_value = pickle.dumps(value)
                if ttl:
                    await self._redis_client.setex(key, ttl, pickled_value)
                else:
                    await self._redis_client.set(key, pickled_value)
                return True
            except Exception as e:
                logger.error(f"Erro ao armazenar no Redis: {str(e)}")
                return False
        else:
            # Cache em memória (sem TTL implementado)
            self._memory_cache[key] = value
            return True

    async def delete(self, key: str) -> bool:
        """
        Remove valor do cache

        Args:
            key: Chave do cache

        Returns:
            True se removido
        """
        if self._use_redis and self._redis_client:
            try:
                await self._redis_client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Erro ao deletar do Redis: {str(e)}")
                return False
        else:
            if key in self._memory_cache:
                del self._memory_cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Verifica se chave existe no cache"""
        if self._use_redis and self._redis_client:
            try:
                return await self._redis_client.exists(key) > 0
            except Exception as e:
                logger.error(f"Erro ao verificar existência no Redis: {str(e)}")
                return False
        else:
            return key in self._memory_cache

    async def clear(self, pattern: str = "*") -> int:
        """
        Limpa cache por pattern

        Args:
            pattern: Pattern das chaves (ex: "user:*")

        Returns:
            Número de chaves removidas
        """
        if self._use_redis and self._redis_client:
            try:
                keys = await self._redis_client.keys(pattern)
                if keys:
                    return await self._redis_client.delete(*keys)
                return 0
            except Exception as e:
                logger.error(f"Erro ao limpar cache no Redis: {str(e)}")
                return 0
        else:
            # Cache em memória
            if pattern == "*":
                count = len(self._memory_cache)
                self._memory_cache.clear()
                return count
            else:
                # Implementação simplificada de pattern matching
                import fnmatch
                keys_to_delete = [
                    k for k in self._memory_cache.keys()
                    if fnmatch.fnmatch(k, pattern)
                ]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                return len(keys_to_delete)

    async def invalidate_prefix(self, prefix: str) -> int:
        """
        Invalida todos os caches com determinado prefixo

        Args:
            prefix: Prefixo das chaves (ex: "produto:")

        Returns:
            Número de chaves invalidadas
        """
        return await self.clear(f"{prefix}*")

    def generate_key(self, *args, **kwargs) -> str:
        """
        Gera chave de cache baseada em argumentos

        Args:
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados

        Returns:
            Chave hash única
        """
        # Criar string representando os argumentos
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_string = ":".join(key_parts)

        # Hash para garantir tamanho fixo
        return hashlib.md5(key_string.encode()).hexdigest()


# Singleton global
cache_service = CacheService()


def cached(ttl: int = 300, prefix: str = "cache"):
    """
    Decorator para cachear resultado de função

    Args:
        ttl: Time to live em segundos (padrão: 5 minutos)
        prefix: Prefixo da chave de cache

    Example:
        @cached(ttl=60, prefix="produto")
        async def get_produto(produto_id: int):
            return await db.query(Produto).filter_by(id=produto_id).first()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave de cache
            cache_key = f"{prefix}:{cache_service.generate_key(*args, **kwargs)}"

            # Tentar buscar do cache
            cached_value = await cache_service.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # Executar função
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Armazenar no cache
            await cache_service.set(cache_key, result, ttl=ttl)

            return result

        # Adicionar método para invalidar cache
        async def invalidate(*args, **kwargs):
            cache_key = f"{prefix}:{cache_service.generate_key(*args, **kwargs)}"
            await cache_service.delete(cache_key)

        wrapper.invalidate = invalidate

        return wrapper

    return decorator


class CacheManager:
    """Gerenciador de cache para diferentes tipos de dados"""

    def __init__(self, cache: CacheService):
        self.cache = cache

    # ========== Sessões ==========

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Busca sessão do cache"""
        key = f"session:{session_id}"
        return await self.cache.get(key)

    async def set_session(
        self,
        session_id: str,
        session_data: dict,
        ttl: int = 3600
    ):
        """Armazena sessão no cache (padrão: 1 hora)"""
        key = f"session:{session_id}"
        await self.cache.set(key, session_data, ttl=ttl)

    async def delete_session(self, session_id: str):
        """Remove sessão do cache"""
        key = f"session:{session_id}"
        await self.cache.delete(key)

    # ========== Produtos ==========

    async def get_produto(self, produto_id: int) -> Optional[dict]:
        """Busca produto do cache"""
        key = f"produto:{produto_id}"
        return await self.cache.get(key)

    async def set_produto(
        self,
        produto_id: int,
        produto_data: dict,
        ttl: int = 600
    ):
        """Armazena produto no cache (padrão: 10 minutos)"""
        key = f"produto:{produto_id}"
        await self.cache.set(key, produto_data, ttl=ttl)

    async def invalidate_produto(self, produto_id: int):
        """Invalida cache de produto"""
        key = f"produto:{produto_id}"
        await self.cache.delete(key)

    async def invalidate_all_produtos(self):
        """Invalida cache de todos os produtos"""
        return await self.cache.invalidate_prefix("produto:")

    # ========== Consultas ==========

    async def cache_query(
        self,
        query_name: str,
        query_params: dict,
        result: Any,
        ttl: int = 300
    ):
        """
        Cacheia resultado de query

        Args:
            query_name: Nome da query (ex: "list_produtos_ativos")
            query_params: Parâmetros da query
            result: Resultado da query
            ttl: Time to live (padrão: 5 minutos)
        """
        key = f"query:{query_name}:{self.cache.generate_key(**query_params)}"
        await self.cache.set(key, result, ttl=ttl)

    async def get_cached_query(
        self,
        query_name: str,
        query_params: dict
    ) -> Optional[Any]:
        """Busca resultado de query do cache"""
        key = f"query:{query_name}:{self.cache.generate_key(**query_params)}"
        return await self.cache.get(key)

    async def invalidate_query(self, query_name: str):
        """Invalida todas as queries com determinado nome"""
        return await self.cache.invalidate_prefix(f"query:{query_name}:")

    # ========== Rate Limiting ==========

    async def increment_rate_limit(
        self,
        identifier: str,
        window: int = 60
    ) -> int:
        """
        Incrementa contador de rate limit

        Args:
            identifier: Identificador (ex: IP, user_id)
            window: Janela de tempo em segundos

        Returns:
            Número de requests nesta janela
        """
        key = f"ratelimit:{identifier}"

        if self.cache._use_redis and self.cache._redis_client:
            # Usar INCR atômico do Redis
            count = await self.cache._redis_client.incr(key)
            if count == 1:
                await self.cache._redis_client.expire(key, window)
            return count
        else:
            # Fallback para memória (não thread-safe)
            current = await self.cache.get(key) or 0
            new_count = current + 1
            await self.cache.set(key, new_count, ttl=window)
            return new_count

    # ========== Estatísticas ==========

    async def get_stats(self) -> dict:
        """Retorna estatísticas do cache"""
        if self.cache._use_redis and self.cache._redis_client:
            try:
                info = await self.cache._redis_client.info("stats")
                return {
                    "tipo": "redis",
                    "total_keys": await self.cache._redis_client.dbsize(),
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "memoria_usada": info.get("used_memory_human", "N/A")
                }
            except Exception as e:
                logger.error(f"Erro ao obter stats do Redis: {str(e)}")
                return {"tipo": "redis", "erro": str(e)}
        else:
            return {
                "tipo": "memoria",
                "total_keys": len(self.cache._memory_cache)
            }


# Instância global
cache_manager = CacheManager(cache_service)
