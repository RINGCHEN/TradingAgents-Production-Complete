#!/usr/bin/env python3
"""
財務管理服務 (Financial Management Service)
天工 (TianGong) - 完整的財務管理業務邏輯

此模組提供完整的財務管理功能，包含：
1. 收入和支出管理
2. 訂閱和付款處理
3. 財務報表生成
4. 稅務管理
5. 預算和預測
"""

import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import calendar

from ..models.financial_management import (
    Transaction, TransactionType, TransactionStatus, PaymentMethod,
    Invoice, InvoiceStatus, Subscription, SubscriptionStatus,
    FinancialReport, RevenueAnalysis, ExpenseAnalysis,
    TaxRecord, Budget, FinancialForecast, PaymentGateway,
    RefundRequest, RefundStatus, FinancialMetrics
)
from ...utils.logging_config import get_api_logger
from ...utils.cache_manager import CacheManager

api_logger = get_api_logger(__name__)

class FinancialManagementService:
    """財務管理服務類"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_manager = CacheManager()
    
    # ==================== 交易管理 ====================
    
    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Transaction:
        """創建交易記錄"""
        try:
            transaction_id = str(uuid.uuid4())
            
            transaction = Transaction(
                transaction_id=transaction_id,
                user_id=transaction_data["user_id"],
                amount=Decimal(str(transaction_data["amount"])),
                currency=transaction_data.get("currency", "TWD"),
                transaction_type=TransactionType(transaction_data["transaction_type"]),
                payment_method=PaymentMethod(transaction_data["payment_method"]),
                status=TransactionStatus.PENDING,
                description=transaction_data.get("description", ""),
                reference_id=transaction_data.get("reference_id"),
                gateway_transaction_id=transaction_data.get("gateway_transaction_id"),
                metadata=transaction_data.get("metadata", {}),
                created_at=datetime.now()
            )
            
            # 保存到數據庫（模擬）
            api_logger.info("交易創建成功", extra={'transaction_id': transaction_id})
            
            return transaction
            
        except Exception as e:
            api_logger.error("創建交易失敗", extra={'error': str(e)})
            raise
    
    async def update_transaction_status(self, transaction_id: str, status: TransactionStatus, 
                                      gateway_response: Optional[Dict[str, Any]] = None) -> Transaction:
        """更新交易狀態"""
        try:
            transaction = await self._get_transaction_by_id(transaction_id)
            if not transaction:
                raise ValueError(f"交易不存在: {transaction_id}")
            
            old_status = transaction.status
            transaction.status = status
            transaction.updated_at = datetime.now()
            
            if gateway_response:
                transaction.gateway_response = gateway_response
            
            # 如果交易成功，更新相關記錄
            if status == TransactionStatus.COMPLETED and old_status != TransactionStatus.COMPLETED:
                await self._process_successful_transaction(transaction)
            
            # 如果交易失敗，處理失敗邏輯
            elif status == TransactionStatus.FAILED:
                await self._process_failed_transaction(transaction)
            
            api_logger.info("交易狀態更新", extra={
                'transaction_id': transaction_id,
                'old_status': old_status.value,
                'new_status': status.value
            })
            
            return transaction
            
        except Exception as e:
            api_logger.error("更新交易狀態失敗", extra={'transaction_id': transaction_id, 'error': str(e)})
            raise
    
    async def get_transaction_history(self, 
                                    user_id: Optional[str] = None,
                                    transaction_type: Optional[TransactionType] = None,
                                    status: Optional[TransactionStatus] = None,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None,
                                    page: int = 1,
                                    page_size: int = 20) -> List[Transaction]:
        """獲取交易歷史"""
        try:
            # 模擬交易歷史數據
            transactions = []
            
            for i in range(min(page_size, 10)):
                transactions.append(Transaction(
                    transaction_id=str(uuid.uuid4()),
                    user_id=user_id or f"user_{i+1}",
                    amount=Decimal("99.99") * (i + 1),
                    currency="TWD",
                    transaction_type=TransactionType.PAYMENT,
                    payment_method=PaymentMethod.CREDIT_CARD,
                    status=TransactionStatus.COMPLETED,
                    description=f"訂閱付款 #{i+1}",
                    created_at=datetime.now() - timedelta(days=i)
                ))
            
            return transactions
            
        except Exception as e:
            api_logger.error("獲取交易歷史失敗", extra={'error': str(e)})
            raise
    
    # ==================== 發票管理 ====================
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Invoice:
        """創建發票"""
        try:
            invoice_id = str(uuid.uuid4())
            invoice_number = await self._generate_invoice_number()
            
            invoice = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_number,
                user_id=invoice_data["user_id"],
                amount=Decimal(str(invoice_data["amount"])),
                tax_amount=Decimal(str(invoice_data.get("tax_amount", 0))),
                currency=invoice_data.get("currency", "TWD"),
                status=InvoiceStatus.DRAFT,
                due_date=invoice_data.get("due_date", datetime.now() + timedelta(days=30)),
                items=invoice_data.get("items", []),
                billing_address=invoice_data.get("billing_address", {}),
                notes=invoice_data.get("notes", ""),
                created_at=datetime.now()
            )
            
            return invoice
            
        except Exception as e:
            api_logger.error("創建發票失敗", extra={'error': str(e)})
            raise
    
    async def send_invoice(self, invoice_id: str) -> bool:
        """發送發票"""
        try:
            invoice = await self._get_invoice_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"發票不存在: {invoice_id}")
            
            # 更新狀態為已發送
            invoice.status = InvoiceStatus.SENT
            invoice.sent_at = datetime.now()
            
            # 發送郵件（模擬）
            await self._send_invoice_email(invoice)
            
            api_logger.info("發票發送成功", extra={'invoice_id': invoice_id})
            return True
            
        except Exception as e:
            api_logger.error("發送發票失敗", extra={'invoice_id': invoice_id, 'error': str(e)})
            return False
    
    async def mark_invoice_paid(self, invoice_id: str, transaction_id: str) -> Invoice:
        """標記發票為已付款"""
        try:
            invoice = await self._get_invoice_by_id(invoice_id)
            if not invoice:
                raise ValueError(f"發票不存在: {invoice_id}")
            
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = datetime.now()
            invoice.transaction_id = transaction_id
            
            return invoice
            
        except Exception as e:
            api_logger.error("標記發票付款失敗", extra={'invoice_id': invoice_id, 'error': str(e)})
            raise
    
    # ==================== 訂閱管理 ====================
    
    async def create_subscription(self, subscription_data: Dict[str, Any]) -> Subscription:
        """創建訂閱"""
        try:
            subscription_id = str(uuid.uuid4())
            
            subscription = Subscription(
                subscription_id=subscription_id,
                user_id=subscription_data["user_id"],
                plan_id=subscription_data["plan_id"],
                status=SubscriptionStatus.ACTIVE,
                amount=Decimal(str(subscription_data["amount"])),
                currency=subscription_data.get("currency", "TWD"),
                billing_cycle=subscription_data.get("billing_cycle", "monthly"),
                start_date=subscription_data.get("start_date", datetime.now()),
                next_billing_date=self._calculate_next_billing_date(
                    subscription_data.get("start_date", datetime.now()),
                    subscription_data.get("billing_cycle", "monthly")
                ),
                trial_end_date=subscription_data.get("trial_end_date"),
                metadata=subscription_data.get("metadata", {}),
                created_at=datetime.now()
            )
            
            return subscription
            
        except Exception as e:
            api_logger.error("創建訂閱失敗", extra={'error': str(e)})
            raise
    
    async def cancel_subscription(self, subscription_id: str, reason: Optional[str] = None) -> Subscription:
        """取消訂閱"""
        try:
            subscription = await self._get_subscription_by_id(subscription_id)
            if not subscription:
                raise ValueError(f"訂閱不存在: {subscription_id}")
            
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.now()
            subscription.cancellation_reason = reason
            
            # 處理退款邏輯（如果需要）
            if subscription.billing_cycle == "yearly":
                await self._process_subscription_refund(subscription)
            
            api_logger.info("訂閱取消成功", extra={'subscription_id': subscription_id})
            
            return subscription
            
        except Exception as e:
            api_logger.error("取消訂閱失敗", extra={'subscription_id': subscription_id, 'error': str(e)})
            raise
    
    async def process_subscription_renewal(self, subscription_id: str) -> bool:
        """處理訂閱續費"""
        try:
            subscription = await self._get_subscription_by_id(subscription_id)
            if not subscription:
                raise ValueError(f"訂閱不存在: {subscription_id}")
            
            # 創建續費交易
            transaction_data = {
                "user_id": subscription.user_id,
                "amount": float(subscription.amount),
                "currency": subscription.currency,
                "transaction_type": "payment",
                "payment_method": "credit_card",  # 實際應該從用戶設置獲取
                "description": f"訂閱續費 - {subscription.plan_id}",
                "reference_id": subscription_id
            }
            
            transaction = await self.create_transaction(transaction_data)
            
            # 更新下次計費日期
            subscription.next_billing_date = self._calculate_next_billing_date(
                subscription.next_billing_date,
                subscription.billing_cycle
            )
            subscription.updated_at = datetime.now()
            
            return True
            
        except Exception as e:
            api_logger.error("處理訂閱續費失敗", extra={'subscription_id': subscription_id, 'error': str(e)})
            return False
    
    # ==================== 財務報表 ====================
    
    async def generate_financial_report(self, 
                                      report_type: str,
                                      start_date: datetime,
                                      end_date: datetime) -> FinancialReport:
        """生成財務報表"""
        try:
            report_id = str(uuid.uuid4())
            
            if report_type == "revenue":
                data = await self._generate_revenue_report(start_date, end_date)
            elif report_type == "expense":
                data = await self._generate_expense_report(start_date, end_date)
            elif report_type == "profit_loss":
                data = await self._generate_profit_loss_report(start_date, end_date)
            elif report_type == "cash_flow":
                data = await self._generate_cash_flow_report(start_date, end_date)
            else:
                raise ValueError(f"不支持的報表類型: {report_type}")
            
            report = FinancialReport(
                report_id=report_id,
                report_type=report_type,
                period_start=start_date,
                period_end=end_date,
                data=data,
                generated_at=datetime.now()
            )
            
            return report
            
        except Exception as e:
            api_logger.error("生成財務報表失敗", extra={'report_type': report_type, 'error': str(e)})
            raise
    
    async def _generate_revenue_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成收入報表"""
        # 模擬收入數據
        total_revenue = Decimal("125000.00")
        subscription_revenue = Decimal("95000.00")
        one_time_revenue = Decimal("30000.00")
        
        # 按月分組的收入
        monthly_revenue = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            month_revenue = total_revenue / 12  # 平均分配
            monthly_revenue.append({
                "month": current_date.strftime("%Y-%m"),
                "revenue": float(month_revenue),
                "growth_rate": 0.08  # 8% 增長率
            })
            
            # 下個月
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return {
            "total_revenue": float(total_revenue),
            "subscription_revenue": float(subscription_revenue),
            "one_time_revenue": float(one_time_revenue),
            "monthly_revenue": monthly_revenue,
            "revenue_by_plan": {
                "basic": 35000.0,
                "premium": 60000.0,
                "enterprise": 30000.0
            },
            "average_revenue_per_user": 76.0,
            "customer_lifetime_value": 450.0
        }
    
    async def _generate_expense_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成支出報表"""
        return {
            "total_expenses": 85000.0,
            "operational_expenses": 45000.0,
            "marketing_expenses": 25000.0,
            "development_expenses": 15000.0,
            "expense_by_category": {
                "人力成本": 50000.0,
                "服務器成本": 15000.0,
                "營銷廣告": 12000.0,
                "辦公費用": 5000.0,
                "其他": 3000.0
            },
            "monthly_expenses": [
                {"month": "2024-01", "amount": 7000.0},
                {"month": "2024-02", "amount": 7200.0},
                {"month": "2024-03", "amount": 7500.0}
            ]
        }
    
    async def _generate_profit_loss_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成損益報表"""
        revenue_data = await self._generate_revenue_report(start_date, end_date)
        expense_data = await self._generate_expense_report(start_date, end_date)
        
        total_revenue = revenue_data["total_revenue"]
        total_expenses = expense_data["total_expenses"]
        gross_profit = total_revenue - total_expenses
        net_profit = gross_profit * 0.85  # 扣除稅費等
        
        return {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "profit_margin": net_profit / total_revenue if total_revenue > 0 else 0,
            "ebitda": gross_profit * 1.1,  # 模擬EBITDA
            "quarterly_comparison": [
                {"quarter": "Q1", "profit": net_profit * 0.8},
                {"quarter": "Q2", "profit": net_profit * 0.9},
                {"quarter": "Q3", "profit": net_profit * 1.1},
                {"quarter": "Q4", "profit": net_profit * 1.2}
            ]
        }
    
    # ==================== 退款管理 ====================
    
    async def create_refund_request(self, refund_data: Dict[str, Any]) -> RefundRequest:
        """創建退款請求"""
        try:
            refund_id = str(uuid.uuid4())
            
            refund_request = RefundRequest(
                refund_id=refund_id,
                transaction_id=refund_data["transaction_id"],
                user_id=refund_data["user_id"],
                amount=Decimal(str(refund_data["amount"])),
                currency=refund_data.get("currency", "TWD"),
                reason=refund_data["reason"],
                status=RefundStatus.PENDING,
                requested_at=datetime.now(),
                metadata=refund_data.get("metadata", {})
            )
            
            return refund_request
            
        except Exception as e:
            api_logger.error("創建退款請求失敗", extra={'error': str(e)})
            raise
    
    async def process_refund(self, refund_id: str, approved: bool, admin_notes: Optional[str] = None) -> RefundRequest:
        """處理退款請求"""
        try:
            refund_request = await self._get_refund_by_id(refund_id)
            if not refund_request:
                raise ValueError(f"退款請求不存在: {refund_id}")
            
            if approved:
                # 執行退款
                success = await self._execute_refund(refund_request)
                if success:
                    refund_request.status = RefundStatus.COMPLETED
                    refund_request.processed_at = datetime.now()
                else:
                    refund_request.status = RefundStatus.FAILED
            else:
                refund_request.status = RefundStatus.REJECTED
                refund_request.processed_at = datetime.now()
            
            refund_request.admin_notes = admin_notes
            
            return refund_request
            
        except Exception as e:
            api_logger.error("處理退款失敗", extra={'refund_id': refund_id, 'error': str(e)})
            raise
    
    # ==================== 財務指標 ====================
    
    async def get_financial_metrics(self, period: str = "monthly") -> FinancialMetrics:
        """獲取財務指標"""
        try:
            # 模擬財務指標
            metrics = FinancialMetrics(
                period=period,
                total_revenue=Decimal("125000.00"),
                total_expenses=Decimal("85000.00"),
                net_profit=Decimal("40000.00"),
                gross_margin=0.68,
                net_margin=0.32,
                customer_acquisition_cost=Decimal("45.00"),
                customer_lifetime_value=Decimal("450.00"),
                monthly_recurring_revenue=Decimal("95000.00"),
                annual_recurring_revenue=Decimal("1140000.00"),
                churn_rate=0.05,
                revenue_growth_rate=0.15,
                cash_flow=Decimal("35000.00"),
                burn_rate=Decimal("8500.00"),
                runway_months=47,
                active_subscriptions=1250,
                average_revenue_per_user=Decimal("76.00")
            )
            
            return metrics
            
        except Exception as e:
            api_logger.error("獲取財務指標失敗", extra={'error': str(e)})
            raise 
   
    # ==================== 預算管理 ====================
    
    async def create_budget(self, budget_data: Dict[str, Any]) -> Budget:
        """創建預算"""
        try:
            budget_id = str(uuid.uuid4())
            
            budget = Budget(
                budget_id=budget_id,
                name=budget_data["name"],
                description=budget_data.get("description", ""),
                category=budget_data["category"],
                amount=Decimal(str(budget_data["amount"])),
                currency=budget_data.get("currency", "TWD"),
                period_start=budget_data["period_start"],
                period_end=budget_data["period_end"],
                status="active",
                created_by=budget_data["created_by"],
                created_at=datetime.now()
            )
            
            return budget
            
        except Exception as e:
            api_logger.error("創建預算失敗", extra={'error': str(e)})
            raise
    
    async def get_budget_utilization(self, budget_id: str) -> Dict[str, Any]:
        """獲取預算使用情況"""
        try:
            budget = await self._get_budget_by_id(budget_id)
            if not budget:
                raise ValueError(f"預算不存在: {budget_id}")
            
            # 計算實際支出
            actual_spending = await self._calculate_actual_spending(budget)
            
            utilization_rate = float(actual_spending / budget.amount) if budget.amount > 0 else 0
            remaining_amount = budget.amount - actual_spending
            
            return {
                "budget_id": budget_id,
                "budget_amount": float(budget.amount),
                "actual_spending": float(actual_spending),
                "remaining_amount": float(remaining_amount),
                "utilization_rate": utilization_rate,
                "status": "over_budget" if utilization_rate > 1.0 else "on_track",
                "days_remaining": (budget.period_end - datetime.now()).days,
                "projected_spending": float(actual_spending * 1.2)  # 預測支出
            }
            
        except Exception as e:
            api_logger.error("獲取預算使用情況失敗", extra={'budget_id': budget_id, 'error': str(e)})
            raise
    
    # ==================== 財務預測 ====================
    
    async def generate_financial_forecast(self, forecast_months: int = 12) -> FinancialForecast:
        """生成財務預測"""
        try:
            forecast_id = str(uuid.uuid4())
            
            # 基於歷史數據生成預測
            current_metrics = await self.get_financial_metrics()
            
            monthly_forecasts = []
            base_revenue = float(current_metrics.monthly_recurring_revenue)
            base_expenses = float(current_metrics.total_expenses) / 12
            
            for i in range(forecast_months):
                # 考慮增長率和季節性
                growth_factor = 1 + (current_metrics.revenue_growth_rate / 12)
                seasonal_factor = 1 + (0.1 * (i % 12 - 6) / 6)  # 簡單的季節性調整
                
                projected_revenue = base_revenue * (growth_factor ** i) * seasonal_factor
                projected_expenses = base_expenses * (1.05 ** (i / 12))  # 5% 年增長
                projected_profit = projected_revenue - projected_expenses
                
                monthly_forecasts.append({
                    "month": (datetime.now() + timedelta(days=30*i)).strftime("%Y-%m"),
                    "projected_revenue": projected_revenue,
                    "projected_expenses": projected_expenses,
                    "projected_profit": projected_profit,
                    "confidence_level": max(0.5, 0.9 - (i * 0.03))  # 信心度隨時間遞減
                })
            
            forecast = FinancialForecast(
                forecast_id=forecast_id,
                forecast_months=forecast_months,
                monthly_forecasts=monthly_forecasts,
                assumptions={
                    "revenue_growth_rate": current_metrics.revenue_growth_rate,
                    "expense_growth_rate": 0.05,
                    "churn_rate": current_metrics.churn_rate,
                    "customer_acquisition_rate": 0.08
                },
                scenarios={
                    "optimistic": {
                        "revenue_multiplier": 1.2,
                        "expense_multiplier": 0.9
                    },
                    "pessimistic": {
                        "revenue_multiplier": 0.8,
                        "expense_multiplier": 1.1
                    }
                },
                generated_at=datetime.now()
            )
            
            return forecast
            
        except Exception as e:
            api_logger.error("生成財務預測失敗", extra={'error': str(e)})
            raise
    
    # ==================== 稅務管理 ====================
    
    async def calculate_tax_liability(self, period_start: datetime, period_end: datetime) -> TaxRecord:
        """計算稅務負債"""
        try:
            tax_record_id = str(uuid.uuid4())
            
            # 獲取期間內的收入和支出
            revenue_report = await self._generate_revenue_report(period_start, period_end)
            expense_report = await self._generate_expense_report(period_start, period_end)
            
            gross_income = Decimal(str(revenue_report["total_revenue"]))
            deductible_expenses = Decimal(str(expense_report["total_expenses"]))
            taxable_income = gross_income - deductible_expenses
            
            # 台灣營業稅率（簡化計算）
            business_tax_rate = Decimal("0.05")  # 5% 營業稅
            income_tax_rate = Decimal("0.20")    # 20% 營所稅
            
            business_tax = gross_income * business_tax_rate
            income_tax = taxable_income * income_tax_rate if taxable_income > 0 else Decimal("0")
            total_tax = business_tax + income_tax
            
            tax_record = TaxRecord(
                tax_record_id=tax_record_id,
                period_start=period_start,
                period_end=period_end,
                gross_income=gross_income,
                deductible_expenses=deductible_expenses,
                taxable_income=taxable_income,
                business_tax=business_tax,
                income_tax=income_tax,
                total_tax=total_tax,
                currency="TWD",
                status="calculated",
                calculated_at=datetime.now()
            )
            
            return tax_record
            
        except Exception as e:
            api_logger.error("計算稅務負債失敗", extra={'error': str(e)})
            raise
    
    async def generate_tax_report(self, year: int) -> Dict[str, Any]:
        """生成年度稅務報表"""
        try:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            tax_record = await self.calculate_tax_liability(start_date, end_date)
            
            # 按季度分解
            quarterly_data = []
            for quarter in range(1, 5):
                quarter_start = datetime(year, (quarter-1)*3 + 1, 1)
                if quarter == 4:
                    quarter_end = datetime(year, 12, 31)
                else:
                    quarter_end = datetime(year, quarter*3, calendar.monthrange(year, quarter*3)[1])
                
                quarter_tax = await self.calculate_tax_liability(quarter_start, quarter_end)
                quarterly_data.append({
                    "quarter": f"Q{quarter}",
                    "gross_income": float(quarter_tax.gross_income),
                    "taxable_income": float(quarter_tax.taxable_income),
                    "total_tax": float(quarter_tax.total_tax)
                })
            
            return {
                "year": year,
                "annual_summary": {
                    "gross_income": float(tax_record.gross_income),
                    "deductible_expenses": float(tax_record.deductible_expenses),
                    "taxable_income": float(tax_record.taxable_income),
                    "business_tax": float(tax_record.business_tax),
                    "income_tax": float(tax_record.income_tax),
                    "total_tax": float(tax_record.total_tax)
                },
                "quarterly_breakdown": quarterly_data,
                "tax_payments": await self._get_tax_payments(year),
                "outstanding_amount": float(tax_record.total_tax) - sum(p["amount"] for p in await self._get_tax_payments(year))
            }
            
        except Exception as e:
            api_logger.error("生成稅務報表失敗", extra={'year': year, 'error': str(e)})
            raise
    
    # ==================== 輔助方法 ====================
    
    async def _process_successful_transaction(self, transaction: Transaction):
        """處理成功的交易"""
        try:
            # 更新用戶訂閱狀態
            if transaction.transaction_type == TransactionType.PAYMENT:
                await self._update_subscription_after_payment(transaction)
            
            # 生成發票
            if transaction.amount >= Decimal("100"):  # 超過100元自動生成發票
                await self._auto_generate_invoice(transaction)
            
            # 發送確認郵件
            await self._send_payment_confirmation(transaction)
            
        except Exception as e:
            api_logger.error("處理成功交易失敗", extra={'transaction_id': transaction.transaction_id, 'error': str(e)})
    
    async def _process_failed_transaction(self, transaction: Transaction):
        """處理失敗的交易"""
        try:
            # 發送失敗通知
            await self._send_payment_failure_notification(transaction)
            
            # 如果是訂閱付款失敗，標記訂閱為逾期
            if transaction.reference_id:
                await self._handle_subscription_payment_failure(transaction.reference_id)
            
        except Exception as e:
            api_logger.error("處理失敗交易失敗", extra={'transaction_id': transaction.transaction_id, 'error': str(e)})
    
    def _calculate_next_billing_date(self, current_date: datetime, billing_cycle: str) -> datetime:
        """計算下次計費日期"""
        if billing_cycle == "monthly":
            if current_date.month == 12:
                return current_date.replace(year=current_date.year + 1, month=1)
            else:
                return current_date.replace(month=current_date.month + 1)
        elif billing_cycle == "yearly":
            return current_date.replace(year=current_date.year + 1)
        elif billing_cycle == "weekly":
            return current_date + timedelta(weeks=1)
        else:
            return current_date + timedelta(days=30)  # 默認30天
    
    async def _generate_invoice_number(self) -> str:
        """生成發票號碼"""
        # 格式: INV-YYYYMM-NNNN
        now = datetime.now()
        prefix = f"INV-{now.strftime('%Y%m')}"
        
        # 實際實現中應該查詢數據庫獲取序號
        sequence = 1
        
        return f"{prefix}-{sequence:04d}"
    
    async def _calculate_actual_spending(self, budget: Budget) -> Decimal:
        """計算實際支出"""
        # 模擬計算實際支出
        # 實際實現中應該查詢交易記錄
        return budget.amount * Decimal("0.75")  # 假設已使用75%
    
    # 模擬數據方法
    async def _get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """根據ID獲取交易（模擬）"""
        return None
    
    async def _get_invoice_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """根據ID獲取發票（模擬）"""
        return None
    
    async def _get_subscription_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """根據ID獲取訂閱（模擬）"""
        return None
    
    async def _get_refund_by_id(self, refund_id: str) -> Optional[RefundRequest]:
        """根據ID獲取退款請求（模擬）"""
        return None
    
    async def _get_budget_by_id(self, budget_id: str) -> Optional[Budget]:
        """根據ID獲取預算（模擬）"""
        return None
    
    async def _send_invoice_email(self, invoice: Invoice):
        """發送發票郵件（模擬）"""
        pass
    
    async def _execute_refund(self, refund_request: RefundRequest) -> bool:
        """執行退款（模擬）"""
        return True
    
    async def _update_subscription_after_payment(self, transaction: Transaction):
        """付款後更新訂閱（模擬）"""
        pass
    
    async def _auto_generate_invoice(self, transaction: Transaction):
        """自動生成發票（模擬）"""
        pass
    
    async def _send_payment_confirmation(self, transaction: Transaction):
        """發送付款確認（模擬）"""
        pass
    
    async def _send_payment_failure_notification(self, transaction: Transaction):
        """發送付款失敗通知（模擬）"""
        pass
    
    async def _handle_subscription_payment_failure(self, subscription_id: str):
        """處理訂閱付款失敗（模擬）"""
        pass
    
    async def _process_subscription_refund(self, subscription: Subscription):
        """處理訂閱退款（模擬）"""
        pass
    
    async def _get_tax_payments(self, year: int) -> List[Dict[str, Any]]:
        """獲取稅務付款記錄（模擬）"""
        return [
            {"date": f"{year}-03-15", "amount": 25000.0, "type": "營業稅"},
            {"date": f"{year}-05-31", "amount": 15000.0, "type": "營所稅"}
        ]