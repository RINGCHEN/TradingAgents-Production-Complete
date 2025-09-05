import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  CreditCard, 
  Shield, 
  CheckCircle, 
  ArrowLeft,
  ArrowRight,
  Clock,
  AlertCircle,
  Gift,
  Zap,
  Lock
} from 'lucide-react';

// 類型定義
interface PaymentStep {
  id: number;
  title: string;
  description: string;
  completed: boolean;
}

interface PaymentMethod {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  processing_time: string;
  fees?: string;
}

interface PaymentData {
  tier: string;
  billing_cycle: 'monthly' | 'yearly';
  payment_method: string;
  amount: number;
  currency: 'TWD';
  customer_info: {
    name: string;
    email: string;
    phone?: string;
    address?: string;
  };
  card_info?: {
    card_number: string;
    expiry: string;
    cvv: string;
    cardholder_name: string;
  };
}

interface PaymentFlowProps {
  selectedTier: {
    tier_type: string;
    name: string;
    price_monthly: number;
    price_yearly: number;
    features: string[];
  };
  billingCycle: 'monthly' | 'yearly';
  onBack: () => void;
  onComplete: (paymentData: PaymentData) => void;
}

// 支付方式選項
const paymentMethods: PaymentMethod[] = [
  {
    id: 'credit_card',
    name: '信用卡 / 金融卡',
    icon: <CreditCard className="w-5 h-5" />,
    description: 'Visa, MasterCard, JCB',
    processing_time: '即時',
  },
  {
    id: 'bank_transfer',
    name: '銀行轉帳',
    icon: <Zap className="w-5 h-5" />,
    description: 'ATM轉帳或網路銀行',
    processing_time: '1-3個工作日',
    fees: '可能產生轉帳手續費'
  },
  {
    id: 'mobile_payment',
    name: '行動支付',
    icon: <Shield className="w-5 h-5" />,
    description: 'LINE Pay, Apple Pay, Google Pay',
    processing_time: '即時',
  }
];

// 支付步驟
const paymentSteps: PaymentStep[] = [
  { id: 1, title: '選擇方案', description: '確認升級方案', completed: true },
  { id: 2, title: '支付資訊', description: '填寫支付詳情', completed: false },
  { id: 3, title: '確認訂單', description: '檢查並確認', completed: false },
  { id: 4, title: '完成支付', description: '處理付款', completed: false }
];

export const PaymentFlow: React.FC<PaymentFlowProps> = ({
  selectedTier,
  billingCycle,
  onBack,
  onComplete
}) => {
  const [currentStep, setCurrentStep] = useState(2);
  const [steps, setSteps] = useState(paymentSteps);
  const [paymentMethod, setPaymentMethod] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentError, setPaymentError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    cardNumber: '',
    expiry: '',
    cvv: '',
    cardholderName: ''
  });
  
  // 計算價格
  const calculatePrice = () => {
    const basePrice = billingCycle === 'monthly' 
      ? selectedTier.price_monthly 
      : selectedTier.price_yearly;
    
    const discount = billingCycle === 'yearly' ? 0.17 : 0;
    const finalPrice = basePrice * (1 - discount);
    const savings = basePrice - finalPrice;
    
    return { finalPrice, savings, basePrice };
  };
  
  const { finalPrice, savings } = calculatePrice();
  
  // 更新步驟狀態
  const updateStepStatus = (stepId: number, completed: boolean) => {
    setSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, completed } : step
    ));
  };
  
  // 處理表單輸入
  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setPaymentError('');
  };
  
  // 驗證表單
  const validateForm = (): boolean => {
    if (!formData.name || !formData.email) {
      setPaymentError('請填寫必要的個人資訊');
      return false;
    }
    
    if (paymentMethod === 'credit_card') {
      if (!formData.cardNumber || !formData.expiry || !formData.cvv || !formData.cardholderName) {
        setPaymentError('請完整填寫信用卡資訊');
        return false;
      }
      
      // 簡單的信用卡號驗證
      if (formData.cardNumber.replace(/\s/g, '').length !== 16) {
        setPaymentError('請輸入有效的信用卡號');
        return false;
      }
    }
    
    return true;
  };
  
  // 處理下一步
  const handleNextStep = () => {
    if (currentStep === 2) {
      if (!paymentMethod) {
        setPaymentError('請選擇支付方式');
        return;
      }
      updateStepStatus(2, true);
      setCurrentStep(3);
    } else if (currentStep === 3) {
      if (!validateForm()) return;
      updateStepStatus(3, true);
      setCurrentStep(4);
      processPayment();
    }
  };
  
  // 處理上一步
  const handlePreviousStep = () => {
    if (currentStep === 2) {
      onBack();
    } else {
      setCurrentStep(prev => prev - 1);
      updateStepStatus(currentStep, false);
    }
  };
  
  // 處理支付
  const processPayment = async () => {
    setIsProcessing(true);
    setPaymentError('');
    
    try {
      // 模擬支付處理
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // 準備支付數據
      const paymentData: PaymentData = {
        tier: selectedTier.tier_type,
        billing_cycle: billingCycle,
        payment_method: paymentMethod,
        amount: finalPrice,
        currency: 'TWD',
        customer_info: {
          name: formData.name,
          email: formData.email,
          phone: formData.phone,
        },
        ...(paymentMethod === 'credit_card' && {
          card_info: {
            card_number: `****-****-****-${formData.cardNumber.slice(-4)}`,
            expiry: formData.expiry,
            cvv: '***',
            cardholder_name: formData.cardholderName
          }
        })
      };
      
      updateStepStatus(4, true);
      onComplete(paymentData);
      
    } catch (error) {
      setPaymentError('支付處理失敗，請重試');
      setIsProcessing(false);
    }
  };
  
  // 渲染步驟指示器
  const renderStepIndicator = () => (
    <div className="flex items-center justify-between mb-8">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center">
          <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
            step.completed 
              ? 'bg-green-500 border-green-500 text-white'
              : currentStep === step.id 
                ? 'border-blue-500 text-blue-500'
                : 'border-gray-300 text-gray-400'
          }`}>
            {step.completed ? <CheckCircle className="w-4 h-4" /> : step.id}
          </div>
          <div className="ml-3">
            <div className={`text-sm font-medium ${
              step.completed ? 'text-green-600' : 
              currentStep === step.id ? 'text-blue-600' : 'text-gray-400'
            }`}>
              {step.title}
            </div>
            <div className="text-xs text-gray-500">{step.description}</div>
          </div>
          {index < steps.length - 1 && (
            <div className={`w-16 h-0.5 mx-4 ${
              step.completed ? 'bg-green-500' : 'bg-gray-200'
            }`} />
          )}
        </div>
      ))}
    </div>
  );
  
  // 渲染訂單摘要
  const renderOrderSummary = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">訂單摘要</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-between">
          <span>{selectedTier.name}</span>
          <span>{billingCycle === 'monthly' ? '月付方案' : '年付方案'}</span>
        </div>
        
        <div className="flex justify-between text-sm text-gray-600">
          <span>原價</span>
          <span>${selectedTier[billingCycle === 'monthly' ? 'price_monthly' : 'price_yearly']?.toLocaleString() || '0'}</span>
        </div>
        
        {savings > 0 && (
          <div className="flex justify-between text-sm text-green-600">
            <span>年付優惠</span>
            <span>-${Math.round(savings)?.toLocaleString() || '0'}</span>
          </div>
        )}
        
        <Separator />
        
        <div className="flex justify-between font-semibold text-lg">
          <span>總計</span>
          <span>${Math.round(finalPrice)?.toLocaleString() || '0'} TWD</span>
        </div>
        
        {billingCycle === 'yearly' && (
          <Badge variant="secondary" className="w-full justify-center">
            <Gift className="w-3 h-3 mr-1" />
            年付省17%
          </Badge>
        )}
        
        <div className="text-xs text-gray-500 text-center">
          {billingCycle === 'monthly' ? '每月自動扣款' : '一次性年費付款'}
        </div>
      </CardContent>
    </Card>
  );
  
  // 渲染支付方式選擇
  const renderPaymentMethodSelection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">選擇支付方式</h3>
      <div className="space-y-3">
        {paymentMethods.map((method) => (
          <Card 
            key={method.id}
            className={`cursor-pointer transition-all ${
              paymentMethod === method.id ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
            }`}
            onClick={() => setPaymentMethod(method.id)}
          >
            <CardContent className="p-4">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-full ${
                  paymentMethod === method.id ? 'bg-blue-500 text-white' : 'bg-gray-100'
                }`}>
                  {method.icon}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{method.name}</div>
                  <div className="text-sm text-gray-600">{method.description}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    處理時間: {method.processing_time}
                    {method.fees && ` • ${method.fees}`}
                  </div>
                </div>
                <div className={`w-4 h-4 rounded-full border-2 ${
                  paymentMethod === method.id 
                    ? 'border-blue-500 bg-blue-500' 
                    : 'border-gray-300'
                }`}>
                  {paymentMethod === method.id && (
                    <div className="w-full h-full rounded-full bg-white scale-50" />
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
  
  // 渲染個人資訊表單
  const renderPersonalInfoForm = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">個人資訊</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="name">姓名 *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e: any) => handleInputChange('name', e.target.value)}
            placeholder="請輸入姓名"
          />
        </div>
        <div>
          <Label htmlFor="email">電子郵件 *</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e: any) => handleInputChange('email', e.target.value)}
            placeholder="請輸入電子郵件"
          />
        </div>
        <div className="md:col-span-2">
          <Label htmlFor="phone">電話號碼</Label>
          <Input
            id="phone"
            value={formData.phone}
            onChange={(e: any) => handleInputChange('phone', e.target.value)}
            placeholder="請輸入電話號碼"
          />
        </div>
      </div>
    </div>
  );
  
  // 渲染信用卡表單
  const renderCreditCardForm = () => (
    paymentMethod === 'credit_card' && (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center">
          <Lock className="w-4 h-4 mr-2" />
          信用卡資訊
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <Label htmlFor="cardholderName">持卡人姓名</Label>
            <Input
              id="cardholderName"
              value={formData.cardholderName}
              onChange={(e: any) => handleInputChange('cardholderName', e.target.value)}
              placeholder="請輸入持卡人姓名"
            />
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="cardNumber">信用卡號</Label>
            <Input
              id="cardNumber"
              value={formData.cardNumber}
              onChange={(e: any) => {
                const value = e.target.value.replace(/\D/g, '');
                const formatted = value.replace(/(\d{4})(?=\d)/g, '$1 ');
                handleInputChange('cardNumber', formatted);
              }}
              placeholder="1234 5678 9012 3456"
              maxLength={19}
            />
          </div>
          <div>
            <Label htmlFor="expiry">到期日期</Label>
            <Input
              id="expiry"
              value={formData.expiry}
              onChange={(e: any) => {
                const value = e.target.value.replace(/\D/g, '');
                const formatted = value.length >= 2 ? 
                  value.substring(0, 2) + '/' + value.substring(2, 4) : value;
                handleInputChange('expiry', formatted);
              }}
              placeholder="MM/YY"
              maxLength={5}
            />
          </div>
          <div>
            <Label htmlFor="cvv">CVV</Label>
            <Input
              id="cvv"
              value={formData.cvv}
              onChange={(e: any) => {
                const value = e.target.value.replace(/\D/g, '');
                handleInputChange('cvv', value);
              }}
              placeholder="123"
              maxLength={3}
            />
          </div>
        </div>
        
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            您的支付資訊經過SSL加密保護，我們不會儲存您的信用卡資訊。
          </AlertDescription>
        </Alert>
      </div>
    )
  );
  
  // 渲染確認頁面
  const renderConfirmation = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">確認訂單資訊</h3>
      
      <Card>
        <CardContent className="p-4 space-y-4">
          <div>
            <h4 className="font-medium">方案資訊</h4>
            <p className="text-sm text-gray-600">{selectedTier.name} - {billingCycle === 'monthly' ? '月付' : '年付'}</p>
          </div>
          
          <div>
            <h4 className="font-medium">支付方式</h4>
            <p className="text-sm text-gray-600">
              {paymentMethods.find(m => m.id === paymentMethod)?.name}
            </p>
          </div>
          
          <div>
            <h4 className="font-medium">聯絡資訊</h4>
            <p className="text-sm text-gray-600">{formData.name}</p>
            <p className="text-sm text-gray-600">{formData.email}</p>
          </div>
          
          <div>
            <h4 className="font-medium">付款金額</h4>
            <p className="text-lg font-semibold text-green-600">
              ${Math.round(finalPrice)?.toLocaleString() || '0'} TWD
            </p>
          </div>
        </CardContent>
      </Card>
      
      <Alert>
        <Clock className="h-4 w-4" />
        <AlertDescription>
          確認後將立即開始處理您的付款，並啟用您的新方案。
        </AlertDescription>
      </Alert>
    </div>
  );
  
  // 渲染處理中狀態
  const renderProcessing = () => (
    <div className="text-center space-y-6">
      <div className="flex justify-center">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
      <h3 className="text-lg font-semibold">處理支付中...</h3>
      <p className="text-gray-600">請稍候，不要關閉此頁面</p>
      <Progress value={75} className="max-w-sm mx-auto" />
    </div>
  );
  
  return (
    <div className="max-w-4xl mx-auto p-6">
      {renderStepIndicator()}
      
      <div className="grid lg:grid-cols-3 gap-8">
        {/* 主要內容 */}
        <div className="lg:col-span-2 space-y-6">
          {paymentError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{paymentError}</AlertDescription>
            </Alert>
          )}
          
          {currentStep === 2 && (
            <Card>
              <CardContent className="p-6 space-y-6">
                {renderPaymentMethodSelection()}
                {renderPersonalInfoForm()}
                {renderCreditCardForm()}
              </CardContent>
            </Card>
          )}
          
          {currentStep === 3 && (
            <Card>
              <CardContent className="p-6">
                {renderConfirmation()}
              </CardContent>
            </Card>
          )}
          
          {currentStep === 4 && isProcessing && (
            <Card>
              <CardContent className="p-6">
                {renderProcessing()}
              </CardContent>
            </Card>
          )}
          
          {/* 操作按鈕 */}
          {currentStep < 4 && (
            <div className="flex justify-between">
              <Button variant="outline" onClick={handlePreviousStep}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                上一步
              </Button>
              
              <Button onClick={handleNextStep} disabled={isProcessing}>
                {currentStep === 3 ? '確認支付' : '下一步'}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>
        
        {/* 訂單摘要 */}
        <div className="lg:col-span-1">
          {renderOrderSummary()}
        </div>
      </div>
    </div>
  );
};

export default PaymentFlow;