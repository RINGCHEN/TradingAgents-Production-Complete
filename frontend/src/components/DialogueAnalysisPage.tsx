import React from 'react';

interface DialogueAnalysisPageProps {
  stockSymbol: string;
  stockName: string;
  apiBaseUrl: string;
  onAnalysisComplete: (result: any) => void;
}

export const DialogueAnalysisPage: React.FC<DialogueAnalysisPageProps> = ({
  stockSymbol,
  stockName,
  apiBaseUrl,
  onAnalysisComplete
}) => {
  return (
    <div className="dialogue-analysis-page">
      <h2>對話分析頁面</h2>
      <p>股票代碼: {stockSymbol}</p>
      <p>股票名稱: {stockName}</p>
      <p>API URL: {apiBaseUrl}</p>
    </div>
  );
};