"""
Exceções personalizadas do ERP
"""
from fastapi import HTTPException, status


class ERPException(Exception):
    """Exceção base do ERP"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(ERPException):
    """Recurso não encontrado"""
    def __init__(self, message: str = "Recurso não encontrado"):
        super().__init__(message, status_code=404)


class ValidationException(ERPException):
    """Erro de validação de negócio"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class InsufficientStockException(ERPException):
    """Estoque insuficiente"""
    def __init__(self, produto: str, disponivel: float, necessario: float):
        message = f"Estoque insuficiente para {produto}. Disponível: {disponivel}, Necessário: {necessario}"
        super().__init__(message, status_code=400)


class FiscalException(ERPException):
    """Erro relacionado a operações fiscais"""
    def __init__(self, message: str):
        super().__init__(f"Erro Fiscal: {message}", status_code=500)


class BusinessRuleException(ERPException):
    """Violação de regra de negócio"""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class DuplicateException(ERPException):
    """Registro duplicado"""
    def __init__(self, message: str = "Registro já existe"):
        super().__init__(message, status_code=409)


class UnauthorizedException(ERPException):
    """Não autorizado"""
    def __init__(self, message: str = "Não autorizado"):
        super().__init__(message, status_code=401)


class ForbiddenException(ERPException):
    """Acesso negado"""
    def __init__(self, message: str = "Acesso negado"):
        super().__init__(message, status_code=403)


# Aliases para compatibilidade
BusinessException = BusinessRuleException
