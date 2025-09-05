import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Navigation from '../components/Navigation';

// Mock CSS import
jest.mock('../components/Navigation.css', () => ({}));

const MockRouter = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('Navigation Component', () => {
  test('renders TradingAgents brand', () => {
    render(
      <MockRouter>
        <Navigation />
      </MockRouter>
    );
    
    expect(screen.getByText('TradingAgents')).toBeInTheDocument();
  });

  test('shows login and register buttons when user is not logged in', () => {
    render(
      <MockRouter>
        <Navigation />
      </MockRouter>
    );
    
    expect(screen.getByText('登入')).toBeInTheDocument();
    expect(screen.getByText('註冊')).toBeInTheDocument();
  });

  test('shows user menu when user is logged in', () => {
    const mockUser = {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      tier: 'free' as const
    };

    render(
      <MockRouter>
        <Navigation user={mockUser} />
      </MockRouter>
    );
    
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('免費版')).toBeInTheDocument();
  });

  test('renders navigation items', () => {
    render(
      <MockRouter>
        <Navigation />
      </MockRouter>
    );
    
    expect(screen.getByText('首頁')).toBeInTheDocument();
    expect(screen.getByText('投資人格測試')).toBeInTheDocument();
    expect(screen.getByText('方案價格')).toBeInTheDocument();
  });
});