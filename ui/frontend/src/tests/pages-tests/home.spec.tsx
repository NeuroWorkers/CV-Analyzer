import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { MantineProvider } from '@mantine/core';
import { Home } from '../../pages/home/Home';
import cardsReducer from '../../core/store/slices/cardsSlice';
import '@mantine/core/styles.css';
import { vi } from 'vitest';


Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});


const mockStore = configureStore({
  reducer: {
    cards: cardsReducer,
    config: () => ({ url: 'http://127.0.0.1:24637' }),
  },
  preloadedState: {
    cards: {
      cards: [],
      searchQuery: '',
      totalCount: 0,
      connectionError: false,
    },
  },
});


const defaultProps = {
  isLoading: false,
  page: 1,
  totalCount: 10,
  handlePageChange: vi.fn(),
};

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <MantineProvider>
      <Provider store={mockStore}>{ui}</Provider>
    </MantineProvider>
  );
}

describe('Home', () => {
  it('renders home component with all core parts', () => {
    renderWithProviders(<Home {...defaultProps} />);

    expect(screen.getByTestId('search')).toBeInTheDocument();
  });
});