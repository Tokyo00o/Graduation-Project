import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { alertsApi } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from './Sidebar';

export default function Layout() {
  const loc = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { data: alertCount } = useQuery({
    queryKey: ['alertCount'],
    queryFn: () => alertsApi.unreadCount(),
    refetchInterval: 15000,
    enabled: !!user,
  });

  const pageTitle = (() => {
    if (loc.pathname === '/') return 'Dashboard';
    if (loc.pathname.startsWith('/projects')) return 'Projects';
    if (loc.pathname.startsWith('/jobs')) return 'Jobs';
    if (loc.pathname.startsWith('/keys')) return 'API Keys';
    if (loc.pathname.startsWith('/reports')) return 'Reports';
    if (loc.pathname.startsWith('/alerts')) return 'Alerts';
    if (loc.pathname.startsWith('/seed-library')) return 'Seed Library';
    return 'FuzzGuard';
  })();

  const roleColors: Record<string, string> = { viewer: 'badge-pending', analyst: 'badge-stopped', engineer: 'badge-running', admin: 'badge-completed' };

  return (
    <div className="layout">
      <Sidebar />
      <div className="main-area">
        <header className="header">
          <h1 className="header-title">{pageTitle}</h1>
          <div className="header-right">
            <span style={{ cursor: 'pointer' }} onClick={() => navigate('/alerts')}>
              🔔 {alertCount?.count > 0 && <span className="badge badge-running" style={{ fontSize: 10 }}>{alertCount.count}</span>}
            </span>
            {user && (
              <span className="text-sm" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>{user.name || user.email}</span>
                <span className={`badge ${roleColors[user.role] ?? 'badge-pending'}`} style={{ fontSize: 10 }}>{user.role}</span>
                <button className="btn btn-secondary btn-sm" onClick={logout}>Logout</button>
              </span>
            )}
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
