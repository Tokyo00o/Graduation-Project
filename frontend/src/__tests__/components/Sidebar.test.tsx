import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../../contexts/AuthContext';
import Sidebar from '../../components/Sidebar';

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });

function renderSidebar() {
  return render(
    <AuthProvider>
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      </QueryClientProvider>
    </AuthProvider>
  );
}

describe('Sidebar', () => {
  it('renders all nav links', () => {
    renderSidebar();
    for (const label of ['Dashboard', 'Projects', 'Alerts']) {
      expect(screen.queryByText(label)).toBeInTheDocument();
    }
  });

  it('renders the logo', () => {
    renderSidebar();
    expect(screen.getByText('FuzzGuard')).toBeInTheDocument();
  });
});
