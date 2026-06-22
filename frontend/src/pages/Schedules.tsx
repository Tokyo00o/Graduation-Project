import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { schedulesApi } from '../api/client';
import ScheduleForm from './ScheduleForm';

export default function Schedules() {
  const { projectId } = useParams<{ projectId: string }>();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);

  const { data: schedules } = useQuery({
    queryKey: ['schedules', projectId],
    queryFn: () => schedulesApi.list(projectId!),
    enabled: !!projectId,
  });

  const toggleMut = useMutation({
    mutationFn: (id: string) => schedulesApi.toggle(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['schedules', projectId] }),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => schedulesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['schedules', projectId] }),
  });

  const runMut = useMutation({
    mutationFn: (id: string) => schedulesApi.runNow(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['schedules', projectId] }),
  });

  const testNotifMut = useMutation({
    mutationFn: (id: string) => schedulesApi.testNotification(id),
    onSuccess: (res: any) => {
      setTestResult(res.status === 'ok' ? 'Notifications sent' : res.message || 'Failed');
      setTimeout(() => setTestResult(null), 3000);
    },
    onError: () => {
      setTestResult('Test failed');
      setTimeout(() => setTestResult(null), 3000);
    },
  });

  const handleEdit = (s: any) => {
    setEditing(s);
    setShowForm(true);
  };

  const handleClose = () => {
    setShowForm(false);
    setEditing(null);
  };

  const getNextRun = (s: any) => {
    if (!s.is_active) return '—';
    if (!s.next_run_at) return 'N/A';
    return new Date(s.next_run_at).toLocaleString();
  };

  const hasWebhook = (s: any) => s.slack_webhook_url || s.webhook_url;

  return (
    <div>
      <div className="flex-between mb-3">
        <h3>Schedule</h3>
        <button className="btn btn-primary btn-sm" onClick={() => { setEditing(null); setShowForm(true); }}>+ New Schedule</button>
      </div>

      {testResult && <div className="alert alert-info text-sm mb-2">{testResult}</div>}

      {(!schedules || schedules.length === 0) ? (
        <div className="empty"><p>No schedules yet. Create one to run recurring fuzzing jobs.</p></div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Cron</th>
                <th>Budget</th>
                <th>Last Run</th>
                <th>Next Run</th>
                <th>Threshold</th>
                <th>Notifications</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {schedules.map((s: any) => (
                <tr key={s.id}>
                  <td><strong>{s.name}</strong></td>
                  <td><code>{s.cron_expression}</code></td>
                  <td>{s.budget}</td>
                  <td className="text-muted text-sm">{s.last_run_at ? new Date(s.last_run_at).toLocaleString() : '—'}</td>
                  <td className="text-sm">{getNextRun(s)}</td>
                  <td>{s.asr_threshold != null ? `${(s.asr_threshold * 100).toFixed(0)}%` : '—'}</td>
                  <td>
                    {s.slack_webhook_url && <span className="badge badge-completed" title="Slack">Slack</span>}
                    {s.webhook_url && <span className="badge badge-pending" title="Webhook">Web</span>}
                    {!hasWebhook(s) && <span className="text-muted text-sm">—</span>}
                  </td>
                  <td><span className={`badge ${s.is_active ? 'badge-running' : 'badge-pending'}`}>{s.is_active ? 'Active' : 'Paused'}</span></td>
                  <td>
                    <div className="flex gap-2">
                      <button className="btn btn-secondary btn-sm" onClick={() => handleEdit(s)}>Edit</button>
                      <button className="btn btn-secondary btn-sm" onClick={() => toggleMut.mutate(s.id)}>{s.is_active ? 'Pause' : 'Activate'}</button>
                      <button className="btn btn-secondary btn-sm" onClick={() => runMut.mutate(s.id)} disabled={runMut.isPending}>Run</button>
                      {hasWebhook(s) && <button className="btn btn-secondary btn-sm" onClick={() => testNotifMut.mutate(s.id)} disabled={testNotifMut.isPending}>Test</button>}
                      <button className="btn btn-danger btn-sm" onClick={() => { if (confirm('Delete this schedule?')) deleteMut.mutate(s.id); }}>Del</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <ScheduleForm
          projectId={projectId!}
          schedule={editing}
          onClose={handleClose}
        />
      )}
    </div>
  );
}
