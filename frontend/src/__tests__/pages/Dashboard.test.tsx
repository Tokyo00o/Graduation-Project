import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from '../../pages/Dashboard';

function renderDashboard() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Dashboard', () => {
  it('renders heading and new project button', () => {
    renderDashboard();
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('+ New Project')).toBeInTheDocument();
  });

  it('renders stat card labels', () => {
    renderDashboard();
    expect(screen.getByText('Total Projects')).toBeInTheDocument();
    expect(screen.getAllByText('Active Jobs').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Completed Jobs')).toBeInTheDocument();
    expect(screen.getByText('Avg ASR')).toBeInTheDocument();
  });
});
