import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { keysApi, providersApi } from '../api/client';

export default function ApiKeys() {
  const qc = useQueryClient();
  const [editProvider, setEditProvider] = useState<string | null>(null);
  const [keyValue, setKeyValue] = useState('');
  const [keyLabel, setKeyLabel] = useState('');
  const [testResult, setTestResult] = useState<{ provider: string; status: string; response_preview: string } | null>(null);
  const [testLoading, setTestLoading] = useState<string | null>(null);

  const { data: keys, isLoading: keysLoading } = useQuery({
    queryKey: ['keys'],
    queryFn: keysApi.list,
  });

  const { data: providers, isLoading: provLoading } = useQuery({
    queryKey: ['providers'],
    queryFn: providersApi.list,
  });

  const setMut = useMutation({
    mutationFn: (args: { provider: string; api_key: string; label: string }) =>
      keysApi.set(args.provider, { api_key: args.api_key, label: args.label }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['keys'] }); qc.invalidateQueries({ queryKey: ['providers'] }); setEditProvider(null); setKeyValue(''); setKeyLabel(''); },
  });

  const deleteMut = useMutation({
    mutationFn: (provider: string) => keysApi.delete(provider),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['keys'] }); qc.invalidateQueries({ queryKey: ['providers'] }); },
  });

  const testMut = useMutation({
    mutationFn: async (provider: string) => {
      setTestLoading(provider);
      const r = await keysApi.test(provider);
      setTestResult({ provider, status: r.status, response_preview: r.response_preview });
      setTestLoading(null);
    },
  });

  const isLoading = keysLoading || provLoading;
  const merged = Array.isArray(providers) && Array.isArray(keys)
    ? providers.map((p: any) => {
        const k = keys.find((x: any) => x.provider === p.name);
        return { ...p, key_preview: k?.key_preview || p.key_preview || '', has_key: k?.has_key || p.has_key || false };
      })
    : [];

  if (isLoading) {
    return <div className="empty"><div className="spinner" /></div>;
  }

  return (
    <div>
      <div className="flex-between mb-4">
        <h2>API Keys</h2>
      </div>

      {testResult && (
        <div className={`alert ${testResult.status === 'ok' ? 'alert-success' : 'alert-danger'} mb-4`}>
          <strong>{testResult.provider}:</strong> {testResult.status === 'ok' ? 'Connected' : 'Failed'} —
          <span className="text-sm ml-2">{testResult.response_preview}</span>
          <button className="btn btn-sm btn-secondary ml-4" onClick={() => setTestResult(null)}>Dismiss</button>
        </div>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Provider</th>
              <th>Key Status</th>
              <th>Last 4 chars</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {merged.map((p: any) => (
              <tr key={p.name}>
                <td><strong>{p.name}</strong></td>
                <td>
                  {p.has_key
                    ? <span className="badge badge-success">Configured</span>
                    : <span className="badge badge-danger">Not set</span>}
                </td>
                <td className="text-muted font-mono">{p.has_key ? `****${p.key_preview}` : '—'}</td>
                <td>
                  <div className="flex gap-2">
                    <button className="btn btn-secondary btn-sm" onClick={() => { setEditProvider(p.name); setKeyValue(''); setKeyLabel(''); }}>{p.has_key ? 'Update' : 'Set Key'}</button>
                    {p.has_key && (
                      <>
                        <button className="btn btn-secondary btn-sm" onClick={() => testMut.mutate(p.name)} disabled={testLoading === p.name}>
                          {testLoading === p.name ? 'Testing...' : 'Test'}
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => { if (confirm(`Delete API key for ${p.name}?`)) deleteMut.mutate(p.name); }}>Remove</button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editProvider && (
        <div className="modal-overlay" onClick={() => setEditProvider(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Set API Key — {editProvider}</h2>
            <p className="text-muted text-sm mb-4">
              The key will be encrypted at rest. It is used to query models from this provider during fuzzing jobs.
            </p>
            <div className="form-group">
              <label>Label (optional)</label>
              <input className="form-input" value={keyLabel} onChange={e => setKeyLabel(e.target.value)} placeholder="e.g. Production key" />
            </div>
            <div className="form-group">
              <label>API Key</label>
              <input className="form-input font-mono" value={keyValue} onChange={e => setKeyValue(e.target.value)} placeholder="sk-..." type="password" autoFocus />
            </div>
            <div className="flex gap-2" style={{ justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setEditProvider(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={() => setMut.mutate({ provider: editProvider, api_key: keyValue, label: keyLabel })} disabled={!keyValue}>Save Key</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
