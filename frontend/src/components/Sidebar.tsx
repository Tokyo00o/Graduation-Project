import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { alertsApi } from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const allLinks = [
  { to: '/', label: 'Dashboard', icon: '📊', minRole: 'viewer' },
  { to: '/projects', label: 'Projects', icon: '📁', minRole: 'viewer' },
  { to: '/keys', label: 'API Keys', icon: '🔑', minRole: 'engineer' },
  { to: '/reports', label: 'Reports', icon: '📄', minRole: 'viewer' },
  { to: '/seed-library', label: 'Seed Library', icon: '📝', minRole: 'analyst' },
  { to: '/alerts', label: 'Alerts', icon: '🔔', minRole: 'viewer' },
];

const roleRank: Record<string, number> = { viewer: 0, analyst: 1, engineer: 2, admin: 3 };

export default function Sidebar() {
  const { user } = useAuth();
  const { data: alertCount } = useQuery({
    queryKey: ['alertCount'],
    queryFn: () => alertsApi.unreadCount(),
    refetchInterval: 15000,
    enabled: !!user,
  });

  const userRank = roleRank[user?.role ?? 'viewer'] ?? 0;
  const visibleLinks = allLinks.filter(l => userRank >= (roleRank[l.minRole] ?? 0));

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">FuzzGuard</div>
      <nav className="sidebar-nav">
        {visibleLinks.map(l => (
          <NavLink
            key={l.to + l.label}
            to={l.to}
            end={l.to === '/'}
            className={({ isActive }) => 'sidebar-link' + (isActive ? ' active' : '')}
          >
            <span className="icon">{l.icon}</span>
            {l.label}
            {l.label === 'Alerts' && alertCount?.count > 0 && (
              <span className="badge badge-running" style={{ marginLeft: 'auto', fontSize: 10 }}>{alertCount.count}</span>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
