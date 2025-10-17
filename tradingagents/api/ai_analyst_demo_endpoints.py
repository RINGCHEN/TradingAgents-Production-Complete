"""AI Analyst Demo Endpoints (recreated)
This module provides simple mock implementations used by the admin demo
and cached analysis wrapper. All content is UTF-8 safe.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai-demo", tags=["AI Analyst Demo"])


class StockAnalysisRequest(BaseModel):
    stock_symbol: str = Field(..., description="Stock symbol", example="2330.TW")
    analysis_level: str = Field("basic", description="basic / premium / ultimate")
    user_tier: str = Field("free", description="free / gold / diamond")


class AnalystInsight(BaseModel):
    analyst_name: str
    analyst_type: str
    analysis: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComprehensiveAnalysisResponse(BaseModel):
    stock_symbol: str
    analysis_id: str
    insights: List[AnalystInsight]
    final_recommendation: str
    confidence_score: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    upgrade_message: Optional[str] = None


class PopularStocksResponse(BaseModel):
    popular_stocks: List[Dict[str, Any]]
    updated_at: datetime = Field(default_factory=datetime.utcnow)


MOCK_ANALYSTS: Dict[str, Dict[str, Any]] = {
    "technical_analyst": {
        "analyst_type": "technical",
        "display_name": "Technical Strategist",
        "base_confidence": 0.6,
    },
    "fundamentals_analyst": {
        "analyst_type": "fundamental",
        "display_name": "Fundamental Analyst",
        "base_confidence": 0.65,
    },
    "risk_analyst": {
        "analyst_type": "risk",
        "display_name": "Risk Manager",
        "base_confidence": 0.55,
    },
    "investment_planner": {
        "analyst_type": "planner",
        "display_name": "Investment Planner",
        "base_confidence": 0.7,
    },
}

POPULAR_TW_STOCKS = [
    {"symbol": "2330.TW", "name": "TSMC", "sector": "Semiconductor"},
    {"symbol": "2317.TW", "name": "Hon Hai", "sector": "Electronics"},
    {"symbol": "2454.TW", "name": "MediaTek", "sector": "IC Design"},
]

TIER_MULTIPLIER = {"free": 0.0, "gold": 0.15, "diamond": 0.3}


async def generate_enhanced_analysis(
    analyst_name: str,
    stock_symbol: str,
    user_tier: str,
    market_data: Optional[dict] = None,
) -> AnalystInsight:
    """Generate a single analyst insight. This is intentionally lightweight."""

    await asyncio.sleep(0.05)

    config = MOCK_ANALYSTS.get(
        analyst_name,
        {
            "analyst_type": "general",
            "display_name": analyst_name.replace("_", " ").title(),
            "base_confidence": 0.5,
        },
    )

    multiplier = TIER_MULTIPLIER.get(user_tier.lower(), 0.0)
    confidence = min(1.0, max(0.3, config["base_confidence"] + multiplier))

    analysis_parts = [
        f"Analyst {config['display_name']} reviewed {stock_symbol}.",
        "Detailed market data supplied." if market_data else "No external market data provided.",
    ]

    tier = user_tier.lower()
    if tier == "diamond":
        analysis_parts.append("Diamond tier gets the most comprehensive breakdown.")
    elif tier == "gold":
        analysis_parts.append("Gold tier includes extended risk metrics.")
    else:
        analysis_parts.append("Upgrade to unlock fuller insights.")

    return AnalystInsight(
        analyst_name=config["display_name"],
        analyst_type=config["analyst_type"],
        analysis=" ".join(analysis_parts),
        confidence=confidence,
    )


@router.post("/analysis", response_model=ComprehensiveAnalysisResponse)
async def get_comprehensive_analysis(
    request: StockAnalysisRequest,
    background_tasks: BackgroundTasks,
) -> ComprehensiveAnalysisResponse:
    logger.info("Generating comprehensive analysis for %s (tier=%s)", request.stock_symbol, request.user_tier)

    analyst_keys = ["technical_analyst", "fundamentals_analyst", "investment_planner"]
    insights = [
        await generate_enhanced_analysis(name, request.stock_symbol, request.user_tier)
        for name in analyst_keys
    ]

    tier = request.user_tier.lower()
    if tier == "diamond":
        final_rec = "BUY"
    elif tier == "free":
        final_rec = "WATCH"
    else:
        final_rec = "HOLD"

    response = ComprehensiveAnalysisResponse(
        stock_symbol=request.stock_symbol,
        analysis_id=f"ANA-{int(datetime.utcnow().timestamp())}",
        insights=insights,
        final_recommendation=final_rec,
        confidence_score=f"{max(i.confidence for i in insights):.0%}",
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        upgrade_message=(
            "Upgrade to diamond tier for deeper analytics" if tier == "free" else None
        ),
    )

    background_tasks.add_task(
        logger.info,
        "Comprehensive analysis prepared for %s (%s)",
        request.stock_symbol,
        request.user_tier,
    )

    return response


@router.get("/popular-stocks", response_model=PopularStocksResponse)
async def get_popular_stocks() -> PopularStocksResponse:
    return PopularStocksResponse(popular_stocks=POPULAR_TW_STOCKS)


@router.post("/analysis/insight", response_model=AnalystInsight)
async def get_single_insight(request: StockAnalysisRequest) -> AnalystInsight:
    return await generate_enhanced_analysis("technical_analyst", request.stock_symbol, request.user_tier)
