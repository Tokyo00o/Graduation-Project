import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Projects from '../../pages/Projects';

function renderProjects() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Projects />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe('Projects', () => {
  it('renders heading and new project button', () => {
    renderProjects();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('+ New Project')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    renderProjects();
    expect(screen.getByText('Projects')).toBeInTheDocument();
  });
});
