"""
Router da API de Analytics
Endpoints para Machine Learning e Insights
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.models import User
from app.analytics.ml_models import (
    MLModelManager,
    DemandForecastingModel,
    ProductRecommendationModel,
    FraudDetectionModel,
    ChurnPredictionModel
)


router = APIRouter()

# Singleton do gerenciador de modelos
ml_manager = MLModelManager()


# ============================================================================
# SCHEMAS
# ============================================================================

class DemandForecastRequest(BaseModel):
    """Request para previsão de demanda"""
    product_id: int
    days_ahead: int = Field(30, ge=1, le=365)


class ReorderSuggestionRequest(BaseModel):
    """Request para sugestão de reposição"""
    product_id: int
    current_stock: int = Field(..., ge=0)
    lead_time_days: int = Field(7, ge=1, le=90)


class ProductRecommendationRequest(BaseModel):
    """Request para recomendação de produtos"""
    customer_id: int
    n_recommendations: int = Field(10, ge=1, le=50)
    exclude_purchased: bool = True


class SimilarProductsRequest(BaseModel):
    """Request para produtos similares"""
    product_id: int
    n_recommendations: int = Field(5, ge=1, le=20)


class FraudDetectionRequest(BaseModel):
    """Request para detecção de fraude"""
    transaction_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    customer_id: int
    payment_method: str
    timestamp: datetime
    ip_address: Optional[str] = None
    attempt_count: int = Field(1, ge=1)


class ChurnPredictionRequest(BaseModel):
    """Request para predição de churn"""
    customer_id: int
    days_since_last_purchase: int = Field(..., ge=0)
    total_purchases: int = Field(..., ge=0)
    average_purchase_value: float = Field(..., ge=0)
    total_spent: float = Field(..., ge=0)
    complaint_count: int = Field(0, ge=0)


# ============================================================================
# ENDPOINTS - DEMAND FORECASTING
# ============================================================================

@router.post(
    "/ml/demand-forecast",
    summary="Previsão de demanda",
    description="Prevê demanda futura de um produto usando ML"
)
async def forecast_demand(
    request: DemandForecastRequest,
    current_user: User = Depends(require_permission("analytics.view"))
):
    """
    Prevê a demanda de um produto para os próximos N dias

    Retorna previsão com intervalo de confiança
    """
    try:
        forecast = await ml_manager.demand_forecasting.predict(
            product_id=request.product_id,
            days_ahead=request.days_ahead
        )

        return {
            "success": True,
            "product_id": request.product_id,
            "forecast_days": request.days_ahead,
            "predictions": forecast,
            "model_info": ml_manager.demand_forecasting.get_model_info()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao prever demanda: {str(e)}"
        )


@router.post(
    "/ml/reorder-suggestion",
    summary="Sugestão de reposição de estoque",
    description="Sugere quando e quanto comprar baseado em ML"
)
async def get_reorder_suggestion(
    request: ReorderSuggestionRequest,
    current_user: User = Depends(require_permission("analytics.view"))
):
    """
    Calcula ponto de pedido e quantidade de reposição ideal

    Baseado em:
    - Previsão de demanda
    - Estoque atual
    - Prazo de entrega
    - Estoque de segurança
    """
    try:
        suggestion = await ml_manager.demand_forecasting.get_reorder_suggestions(
            product_id=request.product_id,
            current_stock=request.current_stock,
            lead_time_days=request.lead_time_days
        )

        return {
            "success": True,
            **suggestion
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular sugestão: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - PRODUCT RECOMMENDATION
# ============================================================================

@router.post(
    "/ml/recommend-products",
    summary="Recomendação de produtos",
    description="Recomenda produtos personalizados para um cliente"
)
async def recommend_products(
    request: ProductRecommendationRequest,
    current_user: User = Depends(require_permission("analytics.view"))
):
    """
    Recomenda produtos usando Collaborative Filtering

    Retorna produtos que o cliente provavelmente irá gostar
    """
    try:
        recommendations = await ml_manager.product_recommendation.recommend_for_customer(
            customer_id=request.customer_id,
            n_recommendations=request.n_recommendations,
            exclude_purchased=request.exclude_purchased
        )

        return {
            "success": True,
            "customer_id": request.customer_id,
            "recommendations": recommendations,
            "model_info": ml_manager.product_recommendation.get_model_info()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao recomendar produtos: {str(e)}"
        )


@router.post(
    "/ml/similar-products",
    summary="Produtos similares",
    description="Encontra produtos similares para cross-sell"
)
async def get_similar_products(
    request: SimilarProductsRequest,
    current_user: User = Depends(require_permission("analytics.view"))
):
    """
    Recomenda produtos similares (cross-sell)

    Baseado em:
    - Produtos frequentemente comprados juntos
    - Similaridade de características
    """
    try:
        similar = await ml_manager.product_recommendation.recommend_similar_products(
            product_id=request.product_id,
            n_recommendations=request.n_recommendations
        )

        return {
            "success": True,
            "product_id": request.product_id,
            "similar_products": similar
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar produtos similares: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - FRAUD DETECTION
# ============================================================================

@router.post(
    "/ml/detect-fraud",
    summary="Detecção de fraude",
    description="Analisa transação e retorna score de risco de fraude"
)
async def detect_fraud(
    request: FraudDetectionRequest,
    current_user: User = Depends(require_permission("analytics.fraud_detection"))
):
    """
    Detecta transações fraudulentas usando ML

    Analisa padrões suspeitos e retorna:
    - Score de risco (0-1)
    - Nível de risco (BAIXO/MÉDIO/ALTO)
    - Ação recomendada
    """
    try:
        transaction = {
            "transaction_id": request.transaction_id,
            "amount": request.amount,
            "customer_id": request.customer_id,
            "payment_method": request.payment_method,
            "timestamp": request.timestamp.isoformat(),
            "ip_address": request.ip_address,
            "attempt_count": request.attempt_count
        }

        analysis = await ml_manager.fraud_detection.predict(transaction)

        return {
            "success": True,
            "transaction_id": request.transaction_id,
            **analysis,
            "model_info": ml_manager.fraud_detection.get_model_info()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao detectar fraude: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - CHURN PREDICTION
# ============================================================================

@router.post(
    "/ml/predict-churn",
    summary="Predição de churn",
    description="Prevê probabilidade de um cliente abandonar"
)
async def predict_churn(
    request: ChurnPredictionRequest,
    current_user: User = Depends(require_permission("analytics.view"))
):
    """
    Prevê risco de churn de um cliente

    Retorna:
    - Probabilidade de churn (0-1)
    - Nível de risco (BAIXO/MÉDIO/ALTO)
    - Motivos do risco
    - Ações de retenção sugeridas
    """
    try:
        customer_data = {
            "id": request.customer_id,
            "days_since_last_purchase": request.days_since_last_purchase,
            "total_purchases": request.total_purchases,
            "average_purchase_value": request.average_purchase_value,
            "total_spent": request.total_spent,
            "complaint_count": request.complaint_count
        }

        prediction = await ml_manager.churn_prediction.predict(
            customer_id=request.customer_id,
            customer_data=customer_data
        )

        return {
            "success": True,
            **prediction,
            "model_info": ml_manager.churn_prediction.get_model_info()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao prever churn: {str(e)}"
        )


# ============================================================================
# ENDPOINTS - MODEL MANAGEMENT
# ============================================================================

@router.get(
    "/ml/models/status",
    summary="Status dos modelos de ML",
    description="Retorna informações sobre todos os modelos"
)
async def get_models_status(
    current_user: User = Depends(require_permission("analytics.view"))
):
    """
    Retorna status de todos os modelos de ML

    Informações incluem:
    - Se o modelo está treinado
    - Data do último treinamento
    - Métricas de performance
    """
    return {
        "success": True,
        "models": ml_manager.get_all_models_status(),
        "timestamp": datetime.now().isoformat()
    }


@router.post(
    "/ml/models/load",
    summary="Carregar modelos salvos",
    description="Carrega todos os modelos salvos em disco"
)
async def load_models(
    current_user: User = Depends(require_permission("analytics.manage"))
):
    """
    Carrega modelos treinados previamente salvos

    Útil após reiniciar o servidor
    """
    try:
        await ml_manager.load_all_models()

        return {
            "success": True,
            "message": "Modelos carregados com sucesso",
            "models": ml_manager.get_all_models_status()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar modelos: {str(e)}"
        )


@router.post(
    "/ml/models/save",
    summary="Salvar modelos",
    description="Salva todos os modelos treinados em disco"
)
async def save_models(
    current_user: User = Depends(require_permission("analytics.manage"))
):
    """
    Salva modelos treinados em disco

    Permite persistir modelos entre restarts
    """
    try:
        await ml_manager.save_all_models()

        return {
            "success": True,
            "message": "Modelos salvos com sucesso",
            "models": ml_manager.get_all_models_status()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar modelos: {str(e)}"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/analytics/health",
    summary="Health check de analytics",
    description="Verifica status do módulo de analytics"
)
async def analytics_health_check():
    """
    Health check do módulo de analytics

    Retorna status de:
    - API de analytics
    - Modelos de ML
    - Dashboards
    """
    return {
        "status": "healthy",
        "service": "Analytics & ML",
        "models_loaded": {
            "demand_forecasting": ml_manager.demand_forecasting.is_trained,
            "product_recommendation": ml_manager.product_recommendation.is_trained,
            "fraud_detection": ml_manager.fraud_detection.is_trained,
            "churn_prediction": ml_manager.churn_prediction.is_trained
        },
        "dashboards_available": 5,
        "timestamp": datetime.now().isoformat()
    }
