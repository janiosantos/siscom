"""
Testes do módulo de Analytics e Machine Learning
"""
import pytest
from datetime import datetime

from app.analytics.ml_models import (
    DemandForecastingModel,
    ProductRecommendationModel,
    FraudDetectionModel,
    ChurnPredictionModel,
    MLModelManager
)


# ============================================================================
# TESTES - DEMAND FORECASTING
# ============================================================================

@pytest.mark.asyncio
async def test_demand_forecasting_init():
    """Teste de inicialização do modelo de previsão de demanda"""
    model = DemandForecastingModel()
    assert model.model_name == "demand_forecasting"
    assert model.is_trained is False


@pytest.mark.asyncio
async def test_demand_forecasting_predict():
    """Teste de previsão de demanda"""
    model = DemandForecastingModel()

    # Simular treinamento
    model.is_trained = True

    # Fazer previsão
    forecast = await model.predict(product_id=1, days_ahead=7)

    assert len(forecast) == 7
    assert all("date" in f for f in forecast)
    assert all("predicted_quantity" in f for f in forecast)
    assert all("confidence" in f for f in forecast)


@pytest.mark.asyncio
async def test_reorder_suggestion():
    """Teste de sugestão de reposição"""
    model = DemandForecastingModel()
    model.is_trained = True

    suggestion = await model.get_reorder_suggestions(
        product_id=1,
        current_stock=50,
        lead_time_days=7
    )

    assert "reorder_point" in suggestion
    assert "suggested_order_quantity" in suggestion
    assert "should_order_now" in suggestion
    assert "safety_stock" in suggestion


# ============================================================================
# TESTES - PRODUCT RECOMMENDATION
# ============================================================================

@pytest.mark.asyncio
async def test_product_recommendation_init():
    """Teste de inicialização do modelo de recomendação"""
    model = ProductRecommendationModel()
    assert model.model_name == "product_recommendation"
    assert model.is_trained is False


@pytest.mark.asyncio
async def test_recommend_for_customer():
    """Teste de recomendação para cliente"""
    model = ProductRecommendationModel()
    model.is_trained = True

    recommendations = await model.recommend_for_customer(
        customer_id=1,
        n_recommendations=5
    )

    assert len(recommendations) == 5
    assert all("product_id" in r for r in recommendations)
    assert all("score" in r for r in recommendations)
    assert all("reason" in r for r in recommendations)


@pytest.mark.asyncio
async def test_similar_products():
    """Teste de produtos similares"""
    model = ProductRecommendationModel()
    model.is_trained = True

    similar = await model.recommend_similar_products(
        product_id=10,
        n_recommendations=3
    )

    assert len(similar) == 3
    assert all("product_id" in s for s in similar)
    assert all("similarity_score" in s for s in similar)


# ============================================================================
# TESTES - FRAUD DETECTION
# ============================================================================

@pytest.mark.asyncio
async def test_fraud_detection_init():
    """Teste de inicialização do modelo de fraude"""
    model = FraudDetectionModel()
    assert model.model_name == "fraud_detection"
    assert model.is_trained is False


@pytest.mark.asyncio
async def test_fraud_detection_low_risk():
    """Teste de transação de baixo risco"""
    model = FraudDetectionModel()

    transaction = {
        "amount": 100.0,
        "customer_id": 1,
        "payment_method": "credit_card",
        "timestamp": datetime.now().isoformat(),
        "attempt_count": 1
    }

    result = await model.predict(transaction)

    assert "is_fraud" in result
    assert "risk_score" in result
    assert "risk_level" in result
    assert "recommended_action" in result
    assert result["risk_level"] in ["BAIXO", "MÉDIO", "ALTO"]


@pytest.mark.asyncio
async def test_fraud_detection_high_risk():
    """Teste de transação de alto risco"""
    model = FraudDetectionModel()

    transaction = {
        "amount": 50000.0,  # Valor muito alto
        "customer_id": 1,
        "payment_method": "credit_card",
        "timestamp": "2025-01-01T03:00:00",  # Madrugada
        "attempt_count": 5  # Múltiplas tentativas
    }

    result = await model.predict(transaction)

    assert result["risk_score"] > 0.5  # Deve ter alto risco
    assert result["risk_level"] in ["MÉDIO", "ALTO"]


# ============================================================================
# TESTES - CHURN PREDICTION
# ============================================================================

@pytest.mark.asyncio
async def test_churn_prediction_init():
    """Teste de inicialização do modelo de churn"""
    model = ChurnPredictionModel()
    assert model.model_name == "churn_prediction"
    assert model.is_trained is False


@pytest.mark.asyncio
async def test_churn_prediction_low_risk():
    """Teste de cliente com baixo risco de churn"""
    model = ChurnPredictionModel()

    customer_data = {
        "days_since_last_purchase": 10,  # Comprou recentemente
        "total_purchases": 50,  # Muitas compras
        "average_purchase_value": 200.0,
        "total_spent": 10000.0,
        "complaint_count": 0
    }

    result = await model.predict(customer_id=1, customer_data=customer_data)

    assert "churn_probability" in result
    assert "risk_level" in result
    assert "reasons" in result
    assert "retention_actions" in result
    assert result["risk_level"] == "BAIXO"


@pytest.mark.asyncio
async def test_churn_prediction_high_risk():
    """Teste de cliente com alto risco de churn"""
    model = ChurnPredictionModel()

    customer_data = {
        "days_since_last_purchase": 120,  # Não compra há tempo
        "total_purchases": 2,  # Poucas compras
        "average_purchase_value": 50.0,
        "total_spent": 100.0,
        "complaint_count": 3  # Muitas reclamações
    }

    result = await model.predict(customer_id=1, customer_data=customer_data)

    assert result["churn_probability"] > 0.5  # Alto risco
    assert result["risk_level"] in ["MÉDIO", "ALTO"]
    assert len(result["reasons"]) > 0
    assert len(result["retention_actions"]) > 0


# ============================================================================
# TESTES - ML MODEL MANAGER
# ============================================================================

def test_ml_manager_initialization():
    """Teste de inicialização do gerenciador de modelos"""
    manager = MLModelManager(models_dir="test_ml_models")

    assert manager.demand_forecasting is not None
    assert manager.product_recommendation is not None
    assert manager.fraud_detection is not None
    assert manager.churn_prediction is not None


def test_get_all_models_status():
    """Teste de obtenção de status de todos os modelos"""
    manager = MLModelManager()
    status = manager.get_all_models_status()

    assert "demand_forecasting" in status
    assert "product_recommendation" in status
    assert "fraud_detection" in status
    assert "churn_prediction" in status

    # Verificar estrutura de cada status
    for model_status in status.values():
        assert "model_name" in model_status
        assert "is_trained" in model_status
        assert "last_training_date" in model_status
        assert "metrics" in model_status


# ============================================================================
# TESTES - MODEL PERSISTENCE
# ============================================================================

def test_demand_model_info():
    """Teste de informações do modelo"""
    model = DemandForecastingModel()
    info = model.get_model_info()

    assert info["model_name"] == "demand_forecasting"
    assert info["is_trained"] is False
    assert info["last_training_date"] is None


@pytest.mark.asyncio
async def test_risk_level_calculation():
    """Teste de cálculo de níveis de risco"""
    fraud_model = FraudDetectionModel()

    # Baixo risco
    assert fraud_model._get_risk_level(0.2) == "BAIXO"

    # Médio risco
    assert fraud_model._get_risk_level(0.5) == "MÉDIO"

    # Alto risco
    assert fraud_model._get_risk_level(0.8) == "ALTO"


@pytest.mark.asyncio
async def test_churn_rfm_calculation():
    """Teste de cálculo RFM para churn"""
    model = ChurnPredictionModel()

    # Cliente ativo (baixo risco)
    good_customer = {
        "days_since_last_purchase": 10,
        "total_purchases": 20,
        "total_spent": 5000,
        "complaint_count": 0
    }
    risk = model._calculate_rfm_churn(good_customer)
    assert risk < 0.3

    # Cliente em risco
    bad_customer = {
        "days_since_last_purchase": 120,
        "total_purchases": 1,
        "total_spent": 100,
        "complaint_count": 3
    }
    risk = model._calculate_rfm_churn(bad_customer)
    assert risk > 0.6
