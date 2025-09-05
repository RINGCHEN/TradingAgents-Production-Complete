import React from 'react';

export const Badge = ({ children, ...props }: any) => {
  return <span {...props}>{children}</span>;
};
