"""
Módulo de Machine Learning para ERP
Modelos preditivos para análise de negócio

Modelos implementados:
1. Previsão de Demanda (Demand Forecasting)
2. Recomendação de Produtos (Product Recommendation)
3. Detecção de Fraude (Fraud Detection)
4. Predição de Churn (Customer Churn Prediction)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import pickle
import os


@dataclass
class Prediction:
    """Resultado de uma predição"""
    model_name: str
    prediction: Any
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime


# ============================================================================
# BASE MODEL CLASS
# ============================================================================

class BaseMLModel:
    """Classe base para modelos de ML"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.is_trained = False
        self.last_training_date = None
        self.metrics = {}

    def save_model(self, filepath: str):
        """Salva modelo treinado em disco"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'is_trained': self.is_trained,
                'last_training_date': self.last_training_date,
                'metrics': self.metrics
            }, f)

    def load_model(self, filepath: str):
        """Carrega modelo treinado do disco"""
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.is_trained = data['is_trained']
                self.last_training_date = data['last_training_date']
                self.metrics = data['metrics']
            return True
        return False

    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo"""
        return {
            "model_name": self.model_name,
            "is_trained": self.is_trained,
            "last_training_date": self.last_training_date.isoformat() if self.last_training_date else None,
            "metrics": self.metrics
        }


# ============================================================================
# 1. DEMAND FORECASTING - Previsão de Demanda
# ============================================================================

class DemandForecastingModel(BaseMLModel):
    """
    Modelo para prever demanda futura de produtos

    Utiliza:
    - Histórico de vendas
    - Sazonalidade
    - Tendências
    - Eventos especiais

    Algoritmo sugerido: Prophet, SARIMA ou LSTM
    """

    def __init__(self):
        super().__init__("demand_forecasting")

    async def train(self, sales_history: List[Dict]) -> Dict[str, Any]:
        """
        Treina modelo com histórico de vendas

        Args:
            sales_history: Lista de vendas com formato:
                [{"date": "2025-01-01", "product_id": 1, "quantity": 10}, ...]

        Returns:
            Métricas de performance do modelo
        """
        # TODO: Implementar com Prophet ou SARIMA
        # from fbprophet import Prophet
        # model = Prophet()
        # model.fit(df)

        # Placeholder: modelo simples baseado em média móvel
        self.is_trained = True
        self.last_training_date = datetime.now()
        self.metrics = {
            "mae": 0.0,  # Mean Absolute Error
            "rmse": 0.0,  # Root Mean Squared Error
            "mape": 0.0   # Mean Absolute Percentage Error
        }

        return {
            "status": "success",
            "samples_trained": len(sales_history),
            "metrics": self.metrics
        }

    async def predict(
        self,
        product_id: int,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Prevê demanda futura de um produto

        Args:
            product_id: ID do produto
            days_ahead: Número de dias a prever

        Returns:
            Lista de previsões: [{"date": "2025-01-01", "predicted_quantity": 15, "confidence": 0.85}, ...]
        """
        if not self.is_trained:
            raise ValueError("Modelo não treinado. Execute train() primeiro.")

        # Placeholder: retorna previsão simples
        predictions = []
        today = datetime.now().date()

        for i in range(days_ahead):
            date = today + timedelta(days=i+1)
            predictions.append({
                "date": date.isoformat(),
                "predicted_quantity": 10,  # TODO: calcular com modelo real
                "confidence": 0.75,
                "upper_bound": 15,
                "lower_bound": 5
            })

        return predictions

    async def get_reorder_suggestions(
        self,
        product_id: int,
        current_stock: int,
        lead_time_days: int = 7
    ) -> Dict[str, Any]:
        """
        Sugere quando e quanto comprar baseado na previsão

        Args:
            product_id: ID do produto
            current_stock: Estoque atual
            lead_time_days: Prazo de entrega do fornecedor

        Returns:
            Sugestão de compra com quantidade e data
        """
        forecast = await self.predict(product_id, days_ahead=lead_time_days + 30)

        # Calcular demanda durante lead time
        lead_time_demand = sum(
            f['predicted_quantity']
            for f in forecast[:lead_time_days]
        )

        # Estoque de segurança (20% da demanda)
        safety_stock = lead_time_demand * 0.2

        # Ponto de pedido
        reorder_point = lead_time_demand + safety_stock

        # Quantidade a pedir (demanda de 30 dias)
        order_quantity = sum(f['predicted_quantity'] for f in forecast[:30])

        return {
            "product_id": product_id,
            "current_stock": current_stock,
            "reorder_point": int(reorder_point),
            "suggested_order_quantity": int(order_quantity),
            "should_order_now": current_stock <= reorder_point,
            "days_until_stockout": self._calculate_stockout_days(current_stock, forecast),
            "safety_stock": int(safety_stock)
        }

    def _calculate_stockout_days(
        self,
        current_stock: int,
        forecast: List[Dict]
    ) -> Optional[int]:
        """Calcula em quantos dias o estoque zerará"""
        cumulative = 0
        for i, pred in enumerate(forecast):
            cumulative += pred['predicted_quantity']
            if cumulative >= current_stock:
                return i + 1
        return None


# ============================================================================
# 2. PRODUCT RECOMMENDATION - Recomendação de Produtos
# ============================================================================

class ProductRecommendationModel(BaseMLModel):
    """
    Modelo para recomendar produtos aos clientes

    Técnicas:
    - Collaborative Filtering (filtro colaborativo)
    - Content-Based Filtering (baseado em conteúdo)
    - Hybrid Approach

    Algoritmo sugerido: ALS, SVD ou Neural Collaborative Filtering
    """

    def __init__(self):
        super().__init__("product_recommendation")
        self.user_item_matrix = None
        self.product_similarity_matrix = None

    async def train(
        self,
        purchase_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Treina modelo com histórico de compras

        Args:
            purchase_history: [{"customer_id": 1, "product_id": 10, "rating": 5}, ...]

        Returns:
            Métricas de performance
        """
        # TODO: Implementar com Surprise, Implicit ou TensorFlow
        # from surprise import SVD, Dataset, Reader
        # reader = Reader(rating_scale=(1, 5))
        # data = Dataset.load_from_df(df[['customer_id', 'product_id', 'rating']], reader)
        # model = SVD()
        # model.fit(data)

        self.is_trained = True
        self.last_training_date = datetime.now()
        self.metrics = {
            "precision_at_10": 0.0,
            "recall_at_10": 0.0,
            "ndcg": 0.0  # Normalized Discounted Cumulative Gain
        }

        return {
            "status": "success",
            "samples_trained": len(purchase_history),
            "metrics": self.metrics
        }

    async def recommend_for_customer(
        self,
        customer_id: int,
        n_recommendations: int = 10,
        exclude_purchased: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recomenda produtos para um cliente específico

        Returns:
            Lista de produtos recomendados com score
        """
        if not self.is_trained:
            raise ValueError("Modelo não treinado.")

        # Placeholder: retorna recomendações simuladas
        recommendations = []
        for i in range(n_recommendations):
            recommendations.append({
                "product_id": i + 1,
                "score": 0.9 - (i * 0.05),  # Score decrescente
                "reason": "Clientes com perfil similar também compraram"
            })

        return recommendations

    async def recommend_similar_products(
        self,
        product_id: int,
        n_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recomenda produtos similares (cross-sell)

        Returns:
            Lista de produtos similares
        """
        # Placeholder
        similar = []
        for i in range(n_recommendations):
            similar.append({
                "product_id": product_id + i + 1,
                "similarity_score": 0.95 - (i * 0.1),
                "reason": "Frequentemente comprados juntos"
            })

        return similar

    async def get_trending_products(
        self,
        category_id: Optional[int] = None,
        n_products: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retorna produtos em alta (trending)

        Returns:
            Lista de produtos populares
        """
        # TODO: Calcular baseado em vendas recentes, crescimento, etc
        return []


# ============================================================================
# 3. FRAUD DETECTION - Detecção de Fraude
# ============================================================================

class FraudDetectionModel(BaseMLModel):
    """
    Modelo para detectar transações fraudulentas

    Características analisadas:
    - Valor da transação
    - Horário
    - Frequência de compras
    - Localização
    - Comportamento histórico

    Algoritmo sugerido: Isolation Forest, XGBoost ou Neural Network
    """

    def __init__(self):
        super().__init__("fraud_detection")

    async def train(
        self,
        transactions: List[Dict],
        labels: List[int]  # 0 = legítima, 1 = fraude
    ) -> Dict[str, Any]:
        """
        Treina modelo com transações rotuladas

        Args:
            transactions: Lista de transações com features
            labels: 0 para transações legítimas, 1 para fraudes

        Returns:
            Métricas de performance
        """
        # TODO: Implementar com scikit-learn
        # from sklearn.ensemble import IsolationForest
        # model = IsolationForest(contamination=0.1)
        # model.fit(X)

        self.is_trained = True
        self.last_training_date = datetime.now()
        self.metrics = {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "auc_roc": 0.0
        }

        return {
            "status": "success",
            "samples_trained": len(transactions),
            "fraud_rate": sum(labels) / len(labels) if labels else 0,
            "metrics": self.metrics
        }

    async def predict(
        self,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analisa uma transação e retorna score de fraude

        Args:
            transaction: {
                "amount": 1000.0,
                "customer_id": 123,
                "payment_method": "credit_card",
                "timestamp": "2025-01-01T10:00:00",
                "ip_address": "192.168.1.1",
                ...
            }

        Returns:
            Análise com score de risco
        """
        if not self.is_trained:
            # Sem modelo treinado, usa regras heurísticas
            risk_score = self._calculate_heuristic_risk(transaction)
        else:
            # TODO: Usar modelo treinado
            risk_score = 0.1

        return {
            "is_fraud": risk_score > 0.7,
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "reasons": self._get_fraud_reasons(transaction, risk_score),
            "recommended_action": self._get_recommended_action(risk_score)
        }

    def _calculate_heuristic_risk(self, transaction: Dict) -> float:
        """Calcula risco usando regras heurísticas"""
        risk = 0.0

        # Valor muito alto
        if transaction.get("amount", 0) > 10000:
            risk += 0.3

        # Horário suspeito (madrugada)
        hour = datetime.fromisoformat(transaction.get("timestamp", datetime.now().isoformat())).hour
        if 0 <= hour <= 5:
            risk += 0.2

        # Múltiplas tentativas
        if transaction.get("attempt_count", 1) > 3:
            risk += 0.3

        return min(risk, 1.0)

    def _get_risk_level(self, score: float) -> str:
        """Converte score em nível de risco"""
        if score < 0.3:
            return "BAIXO"
        elif score < 0.7:
            return "MÉDIO"
        else:
            return "ALTO"

    def _get_fraud_reasons(self, transaction: Dict, score: float) -> List[str]:
        """Lista motivos de suspeita"""
        reasons = []

        if transaction.get("amount", 0) > 10000:
            reasons.append("Valor acima do normal")

        if score > 0.5:
            reasons.append("Padrão atípico de compra")

        return reasons

    def _get_recommended_action(self, score: float) -> str:
        """Recomenda ação baseada no risco"""
        if score < 0.3:
            return "Aprovar automaticamente"
        elif score < 0.7:
            return "Solicitar autenticação adicional (2FA)"
        else:
            return "Bloquear e revisar manualmente"


# ============================================================================
# 4. CHURN PREDICTION - Predição de Churn
# ============================================================================

class ChurnPredictionModel(BaseMLModel):
    """
    Modelo para prever quais clientes têm risco de churn (abandono)

    Características analisadas:
    - Frequência de compras
    - Valor médio de compras
    - Tempo desde última compra (RFM)
    - Engajamento
    - Reclamações

    Algoritmo sugerido: Logistic Regression, Random Forest ou XGBoost
    """

    def __init__(self):
        super().__init__("churn_prediction")

    async def train(
        self,
        customers: List[Dict],
        churn_labels: List[int]  # 0 = ativo, 1 = churned
    ) -> Dict[str, Any]:
        """
        Treina modelo com dados de clientes

        Args:
            customers: Lista de features de clientes
            churn_labels: 0 para clientes ativos, 1 para churned

        Returns:
            Métricas de performance
        """
        # TODO: Implementar com scikit-learn
        # from sklearn.ensemble import RandomForestClassifier
        # model = RandomForestClassifier()
        # model.fit(X, y)

        self.is_trained = True
        self.last_training_date = datetime.now()
        self.metrics = {
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "auc_roc": 0.0
        }

        return {
            "status": "success",
            "samples_trained": len(customers),
            "churn_rate": sum(churn_labels) / len(churn_labels) if churn_labels else 0,
            "metrics": self.metrics
        }

    async def predict(
        self,
        customer_id: int,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prevê probabilidade de churn de um cliente

        Args:
            customer_id: ID do cliente
            customer_data: {
                "days_since_last_purchase": 45,
                "total_purchases": 10,
                "average_purchase_value": 150.0,
                "complaint_count": 0,
                "total_spent": 1500.0,
                ...
            }

        Returns:
            Predição de churn com score
        """
        if not self.is_trained:
            # Sem modelo, usa regra RFM simples
            churn_probability = self._calculate_rfm_churn(customer_data)
        else:
            # TODO: Usar modelo treinado
            churn_probability = 0.3

        return {
            "customer_id": customer_id,
            "churn_probability": churn_probability,
            "risk_level": self._get_churn_risk_level(churn_probability),
            "reasons": self._get_churn_reasons(customer_data),
            "retention_actions": self._get_retention_actions(churn_probability)
        }

    def _calculate_rfm_churn(self, customer_data: Dict) -> float:
        """Calcula risco de churn baseado em RFM"""
        risk = 0.0

        # Recency: tempo desde última compra
        days_since_last = customer_data.get("days_since_last_purchase", 0)
        if days_since_last > 90:
            risk += 0.4
        elif days_since_last > 60:
            risk += 0.2

        # Frequency: número de compras
        total_purchases = customer_data.get("total_purchases", 0)
        if total_purchases < 3:
            risk += 0.2

        # Monetary: valor total gasto
        total_spent = customer_data.get("total_spent", 0)
        if total_spent < 500:
            risk += 0.2

        # Complaints
        if customer_data.get("complaint_count", 0) > 2:
            risk += 0.2

        return min(risk, 1.0)

    def _get_churn_risk_level(self, probability: float) -> str:
        """Converte probabilidade em nível de risco"""
        if probability < 0.3:
            return "BAIXO"
        elif probability < 0.7:
            return "MÉDIO"
        else:
            return "ALTO"

    def _get_churn_reasons(self, customer_data: Dict) -> List[str]:
        """Identifica motivos de risco de churn"""
        reasons = []

        if customer_data.get("days_since_last_purchase", 0) > 90:
            reasons.append("Não compra há mais de 90 dias")

        if customer_data.get("total_purchases", 0) < 3:
            reasons.append("Baixa frequência de compras")

        if customer_data.get("complaint_count", 0) > 0:
            reasons.append(f"{customer_data['complaint_count']} reclamações registradas")

        return reasons

    def _get_retention_actions(self, probability: float) -> List[str]:
        """Sugere ações de retenção"""
        actions = []

        if probability > 0.7:
            actions.extend([
                "Oferecer cupom de desconto personalizado (15-20%)",
                "Ligar para o cliente oferecendo ajuda",
                "Enviar email com produtos que ele possa gostar"
            ])
        elif probability > 0.3:
            actions.extend([
                "Enviar email de reengajamento",
                "Oferecer cupom de desconto (5-10%)",
                "Incluir em campanha de fidelidade"
            ])

        return actions

    async def get_high_risk_customers(
        self,
        customers_data: List[Dict],
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Retorna lista de clientes com alto risco de churn

        Args:
            customers_data: Lista de dados de clientes
            threshold: Probabilidade mínima para considerar alto risco

        Returns:
            Lista de clientes em risco ordenada por probabilidade
        """
        high_risk = []

        for customer_data in customers_data:
            prediction = await self.predict(
                customer_data.get("id"),
                customer_data
            )

            if prediction["churn_probability"] >= threshold:
                high_risk.append({
                    **customer_data,
                    **prediction
                })

        # Ordenar por probabilidade decrescente
        high_risk.sort(key=lambda x: x["churn_probability"], reverse=True)

        return high_risk


# ============================================================================
# ML MODEL MANAGER
# ============================================================================

class MLModelManager:
    """
    Gerenciador centralizado de modelos de ML
    """

    def __init__(self, models_dir: str = "ml_models"):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)

        # Inicializar modelos
        self.demand_forecasting = DemandForecastingModel()
        self.product_recommendation = ProductRecommendationModel()
        self.fraud_detection = FraudDetectionModel()
        self.churn_prediction = ChurnPredictionModel()

    async def load_all_models(self):
        """Carrega todos os modelos salvos"""
        self.demand_forecasting.load_model(f"{self.models_dir}/demand_forecasting.pkl")
        self.product_recommendation.load_model(f"{self.models_dir}/product_recommendation.pkl")
        self.fraud_detection.load_model(f"{self.models_dir}/fraud_detection.pkl")
        self.churn_prediction.load_model(f"{self.models_dir}/churn_prediction.pkl")

    async def save_all_models(self):
        """Salva todos os modelos"""
        self.demand_forecasting.save_model(f"{self.models_dir}/demand_forecasting.pkl")
        self.product_recommendation.save_model(f"{self.models_dir}/product_recommendation.pkl")
        self.fraud_detection.save_model(f"{self.models_dir}/fraud_detection.pkl")
        self.churn_prediction.save_model(f"{self.models_dir}/churn_prediction.pkl")

    def get_all_models_status(self) -> Dict[str, Any]:
        """Retorna status de todos os modelos"""
        return {
            "demand_forecasting": self.demand_forecasting.get_model_info(),
            "product_recommendation": self.product_recommendation.get_model_info(),
            "fraud_detection": self.fraud_detection.get_model_info(),
            "churn_prediction": self.churn_prediction.get_model_info()
        }
