import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertsApi } from '../api/client';
import StatusBadge from '../components/StatusBadge';

const SEVERITY_CLASS: Record<string, string> = {
  info: 'badge-pending',
  warning: 'badge-stopped',
  critical: 'badge-failed',
};

export default function Alerts() {
  const qc = useQueryClient();

  const { data: alerts } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => alertsApi.list({ limit: 100 }),
    refetchInterval: 10000,
  });

  const markReadMut = useMutation({
    mutationFn: (id: string) => alertsApi.markRead(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['alerts'] }); qc.invalidateQueries({ queryKey: ['alertCount'] }); },
  });

  const markAllMut = useMutation({
    mutationFn: () => alertsApi.markAllRead(),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['alerts'] }); qc.invalidateQueries({ queryKey: ['alertCount'] }); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => alertsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['alerts'] }); qc.invalidateQueries({ queryKey: ['alertCount'] }); },
  });

  const unreadCount = alerts?.filter((a: any) => !a.is_read).length ?? 0;

  return (
    <div>
      <div className="flex-between mb-3">
        <h3>Alerts {unreadCount > 0 && <span className="badge badge-running">{unreadCount} unread</span>}</h3>
        {unreadCount > 0 && (
          <button className="btn btn-secondary btn-sm" onClick={() => markAllMut.mutate()}>Mark All Read</button>
        )}
      </div>

      {(!alerts || alerts.length === 0) ? (
        <div className="empty"><p>No alerts yet.</p></div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Severity</th>
                <th>Type</th>
                <th>Message</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a: any) => (
                <tr key={a.id} style={{ opacity: a.is_read ? 0.6 : 1 }}>
                  <td className="text-muted text-sm">{new Date(a.created_at).toLocaleString()}</td>
                  <td><span className={`badge ${SEVERITY_CLASS[a.severity] ?? 'badge-pending'}`}>{a.severity}</span></td>
                  <td className="mono text-sm">{a.type}</td>
                  <td>{a.message}</td>
                  <td>
                    <div className="flex gap-2">
                      {!a.is_read && <button className="btn btn-secondary btn-sm" onClick={() => markReadMut.mutate(a.id)}>Read</button>}
                      <button className="btn btn-danger btn-sm" onClick={() => deleteMut.mutate(a.id)}>Del</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
