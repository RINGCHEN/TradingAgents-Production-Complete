import React, { useState } from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { render, createMockUser, testAccessibility } from '../test-utils';

// Simple test component
const TestComponent: React.FC<{ user?: any }> = ({ user }) => {
  const [count, setCount] = useState(0);

  return (
    <div>
      <h1>Test Component</h1>
      {user && <p>Welcome, {user.name}!</p>}
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
};

describe('TestComponent', () => {
  it('should render correctly', () => {
    render(<TestComponent />);
    expect(screen.getByText('Test Component')).toBeInTheDocument();
    expect(screen.getByText('Count: 0')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Increment' })).toBeInTheDocument();
  });

  it('should display user information when provided', () => {
    const mockUser = createMockUser({ name: 'John Doe' });
    render(<TestComponent user={mockUser} />);
    expect(screen.getByText('Welcome, John Doe!')).toBeInTheDocument();
  });

  it('should increment count when button is clicked', () => {
    render(<TestComponent />);
    const button = screen.getByRole('button', { name: 'Increment' });
    
    expect(screen.getByText('Count: 0')).toBeInTheDocument();
    
    fireEvent.click(button);
    expect(screen.getByText('Count: 1')).toBeInTheDocument();
    
    fireEvent.click(button);
    expect(screen.getByText('Count: 2')).toBeInTheDocument();
  });

  it('should be accessible', async () => {
    await testAccessibility(<TestComponent />);
  });

  it('should handle user interactions correctly', () => {
    const mockUser = createMockUser({ name: 'Jane Smith' });
    render(<TestComponent user={mockUser} />);
    
    // Test initial state
    expect(screen.getByText('Welcome, Jane Smith!')).toBeInTheDocument();
    expect(screen.getByText('Count: 0')).toBeInTheDocument();
    
    // Test interaction
    const button = screen.getByRole('button', { name: 'Increment' });
    fireEvent.click(button);
    expect(screen.getByText('Count: 1')).toBeInTheDocument();
    expect(screen.getByText('Welcome, Jane Smith!')).toBeInTheDocument();
  });
});