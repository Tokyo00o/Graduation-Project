import { render, screen } from '@testing-library/react';
import StatusBadge from '../../components/StatusBadge';

describe('StatusBadge', () => {
  it('renders the status text', () => {
    render(<StatusBadge status="running" />);
    expect(screen.getByText('running')).toBeInTheDocument();
  });

  it('renders with the correct CSS class', () => {
    render(<StatusBadge status="completed" />);
    const span = screen.getByText('completed');
    expect(span.className).toBe('badge badge-completed');
  });
});
