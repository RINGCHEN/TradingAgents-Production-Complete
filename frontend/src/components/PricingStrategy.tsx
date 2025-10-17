import React from 'react';
import { MembershipPlans } from './PaymentSystem/MembershipPlans';

interface PricingStrategyProps {
  apiBaseUrl: string;
  userId?: number;
  sessionId: string;
  onPlanSelected: (planId: string, price: number) => void;
}

/**
 * 定價策略組件
 * 整合PayUni支付系統的完整定價頁面
 */
const PricingStrategy: React.FC<PricingStrategyProps> = ({
  apiBaseUrl,
  userId,
  sessionId,
  onPlanSelected
}) => {
  return (
    <div className="pricing-strategy-container">
      {/* 使用完整的會員方案組件，包含PayUni支付整合 */}
      <MembershipPlans
        apiBaseUrl={apiBaseUrl}
        userId={userId}
        sessionId={sessionId}
        onPlanSelected={onPlanSelected}
      />
    </div>
  );
};

export default PricingStrategy;