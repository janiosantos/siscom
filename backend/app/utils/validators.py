"""
Validadores personalizados
"""
from validate_docbr import CPF, CNPJ


class DocumentValidator:
    """Validador de documentos brasileiros"""

    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """Valida CPF"""
        validator = CPF()
        return validator.validate(cpf)

    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """Valida CNPJ"""
        validator = CNPJ()
        return validator.validate(cnpj)

    @staticmethod
    def format_cpf(cpf: str) -> str:
        """Formata CPF"""
        validator = CPF()
        return validator.mask(cpf)

    @staticmethod
    def format_cnpj(cnpj: str) -> str:
        """Formata CNPJ"""
        validator = CNPJ()
        return validator.mask(cnpj)
