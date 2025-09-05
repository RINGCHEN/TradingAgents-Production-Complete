import React from 'react';

export const Button = ({ children, ...props }: any) => {
  return <button {...props}>{children}</button>;
};
