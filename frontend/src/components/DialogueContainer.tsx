import React from 'react';

interface DialogueContainerProps {
  apiBaseUrl: string;
  onAnalysisComplete: (result: any) => void;
}

export const DialogueContainer: React.FC<DialogueContainerProps> = ({
  apiBaseUrl,
  onAnalysisComplete
}) => {
  return (
    <div className="dialogue-container">
      <h2>對話容器</h2>
      <p>API URL: {apiBaseUrl}</p>
    </div>
  );
};