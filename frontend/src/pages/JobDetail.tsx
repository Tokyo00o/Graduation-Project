import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, judgesApi } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import { useJobWebSocket } from '../api/useJobWebSocket';
import MCTSTree from '../components/MCTSTree';

type Tab = 'results' | 'metrics' | 'tree';

export default function JobDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>('results');
  const [page, setPage] = useState(1);
  const [selectedResult, setSelectedResult] = useState<any>(null);

  const { connected, liveIterations, treeSnapshot } = useJobWebSocket(jobId);

  const { data: job, isLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.get(jobId!),
    enabled: !!jobId,
    refetchInterval: (q) => {
      if (connected) return false;
      const status = q?.state?.data?.status;
      return status === 'running' || status === 'created' || status === 'pending' ? 2000 : false;
    },
  });

  const { data: mctsTree } = useQuery({
    queryKey: ['mcts-tree', jobId],
    queryFn: () => jobsApi.mctsTree(jobId!),
    enabled: !!jobId && !!job && (job.strategy === 'mcts' || job.strategy === 'ucb'),
    refetchInterval: (q) => {
      if (connected && treeSnapshot) return false;
      const status = q?.state?.data?.status;
      return status === 'running' ? 3000 : false;
    },
  });

  const { data: results } = useQuery({
    queryKey: ['results', jobId, page],
    queryFn: () => jobsApi.results(jobId!, { page, limit: 20, sort: '-iteration_number' }),
    enabled: !!jobId,
    refetchInterval: !connected && job?.status === 'running' ? 3000 : false,
  });

  const { data: metrics } = useQuery({
    queryKey: ['metrics', jobId],
    queryFn: () => judgesApi.metrics(jobId!),
    enabled: !!jobId && job?.status === 'completed',
  });

  const stopMut = useMutation({
    mutationFn: () => jobsApi.stop(jobId!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['job', jobId] }),
  });

  if (isLoading) return <div className="empty"><div className="spinner" /></div>;
  if (!job) return <div className="empty"><h3>Job not found</h3></div>;

  const totalPages = results ? Math.ceil(results.total / 20) : 0;
  const isActive = job.status === 'running' || job.status === 'created' || job.status === 'pending';

  const allItems = [
    ...(liveIterations ?? []),
    ...((results?.items ?? []).filter(
      (item: any) => !liveIterations.some((li: any) => li.id === item.id),
    )),
  ];

  return (
    <div>
      <div className="flex-between mb-4">
        <div>
          <h2 className="mb-2">Job <span className="mono">{job.id}</span></h2>
          <div className="flex gap-3 text-sm">
            <span>Strategy: <strong>{job.strategy}</strong></span>
            <span>Judge: <strong>{job.judge}</strong></span>
            <span>Budget: <strong>{job.budget}</strong></span>
            <span>Queries: <strong>{job.queries_used}</strong></span>
            <span>ASR: <strong>{(job.asr * 100).toFixed(1)}%</strong></span>
            <StatusBadge status={job.status} />
            {connected && <span className="badge badge-running">Live</span>}
          </div>
        </div>
        <div className="flex gap-2">
          {isActive && (
            <button className="btn btn-danger" onClick={() => stopMut.mutate()} disabled={stopMut.isPending}>Stop</button>
          )}
          {job.status === 'completed' && (
            <div className="flex gap-1">
              <button className="btn btn-secondary btn-sm" onClick={() => { const a = document.createElement('a'); a.href = `/api/v1/reports/${job.id}/export/json`; a.download = `report_${job.id}.json`; a.click(); }}>JSON</button>
              <button className="btn btn-secondary btn-sm" onClick={() => { const a = document.createElement('a'); a.href = `/api/v1/reports/${job.id}/export/csv`; a.download = `report_${job.id}.csv`; a.click(); }}>CSV</button>
              <button className="btn btn-secondary btn-sm" onClick={() => { const a = document.createElement('a'); a.href = `/api/v1/reports/${job.id}/export/html`; a.download = `report_${job.id}.html`; a.click(); }}>HTML</button>
              <button className="btn btn-primary btn-sm" onClick={() => navigate(`/reports/${job.id}`)}>Full Report</button>
            </div>
          )}
        </div>
      </div>

      <div className="grid-4 mb-4">
        <div className="card">
          <div className="card-title">Status</div>
          <div className="card-value" style={{ fontSize: 20 }}><StatusBadge status={job.status} /></div>
        </div>
        <div className="card">
          <div className="card-title">Queries Used</div>
          <div className="card-value">{job.queries_used} / {job.budget}</div>
        </div>
        <div className="card">
          <div className="card-title">ASR (Top-1)</div>
          <div className="card-value">{(metrics?.asr_top1 ?? job.asr ?? 0) * 100}%</div>
        </div>
        <div className="card">
          <div className="card-title">ASR (Top-5)</div>
          <div className="card-value">{((metrics?.asr_top5 ?? 0) * 100).toFixed(1)}%</div>
        </div>
      </div>

      <div className="tabs">
        <button className={`tab ${tab === 'results' ? 'active' : ''}`} onClick={() => setTab('results')}>Results</button>
        <button className={`tab ${tab === 'metrics' ? 'active' : ''}`} onClick={() => setTab('metrics')}>Metrics</button>
        {(job.strategy === 'mcts' || job.strategy === 'ucb') && (
          <button className={`tab ${tab === 'tree' ? 'active' : ''}`} onClick={() => setTab('tree')}>MCTS Tree</button>
        )}
      </div>

      {tab === 'results' && (
        <div>
          {liveIterations.length > 0 && (
            <div className="mb-3">
              <div className="flex-between mb-1">
                <h4 className="text-sm">Live Stream</h4>
                <span className="badge badge-running">{liveIterations.length} new</span>
              </div>
              <div className="live-stream">
                {liveIterations.slice(0, 5).map((r: any) => (
                  <div key={r.id} className="live-item" onClick={() => setSelectedResult(r)}>
                    <span className="text-muted">#{r.iteration_number}</span>
                    <span className="badge badge-pending">{r.mutation?.mutation_type}</span>
                    <span className="mono truncate" style={{ flex: 1 }}>{r.mutation?.content}</span>
                    <StatusBadge status={r.judgment?.classification} />
                    <span className="text-muted text-sm">{r.reward.toFixed(1)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Mutation</th>
                  <th>Prompt</th>
                  <th>Judgment</th>
                  <th>Confidence</th>
                  <th>Reward</th>
                </tr>
              </thead>
              <tbody>
                {allItems.length === 0 ? (
                  <tr><td colSpan={6}><div className="empty">{isActive ? <><div className="spinner" /><p className="mt-2">Job running...</p></> : <p>No results yet</p>}</div></td></tr>
                ) : allItems.map((r: any) => (
                  <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => setSelectedResult(r)}>
                    <td className="text-muted">{r.iteration_number}</td>
                    <td><span className="badge badge-pending">{r.mutation?.mutation_type ?? '—'}</span></td>
                    <td className="mono truncate">{r.mutation?.content ?? '—'}</td>
                    <td><StatusBadge status={r.judgment?.classification ?? 'unknown'} /></td>
                    <td>{r.judgment ? `${(r.judgment.confidence * 100).toFixed(0)}%` : '—'}</td>
                    <td>{r.reward.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex gap-2" style={{ justifyContent: 'center', marginTop: 16 }}>
              <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
              <span className="text-sm text-muted">Page {page} of {totalPages}</span>
              <button className="btn btn-secondary btn-sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</button>
            </div>
          )}

          {selectedResult && (
            <div className="modal-overlay" onClick={() => setSelectedResult(null)}>
              <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 700 }}>
                <h2 className="mb-3">Iteration #{selectedResult.iteration_number}</h2>
                <div className="form-group">
                  <label>Mutated Prompt ({selectedResult.mutation?.mutation_type})</label>
                  <pre className="form-textarea" style={{ minHeight: 60, whiteSpace: 'pre-wrap', margin: 0 }}>{selectedResult.mutation?.content}</pre>
                </div>
                <div className="form-group">
                  <label>Target Response</label>
                  <pre className="form-textarea" style={{ minHeight: 60, whiteSpace: 'pre-wrap', margin: 0 }}>{selectedResult.response?.response}</pre>
                </div>
                <div className="form-group">
                  <label>Judgment</label>
                  <div className="flex gap-3">
                    <span><StatusBadge status={selectedResult.judgment?.classification} /></span>
                    <span className="text-muted text-sm">Confidence: {selectedResult.judgment ? `${(selectedResult.judgment.confidence * 100).toFixed(1)}%` : '—'}</span>
                    <span className="text-muted text-sm">Judge: {selectedResult.judgment?.judge_model}</span>
                  </div>
                  {selectedResult.judgment?.explanation && (
                    <p className="text-muted text-sm mt-2">{selectedResult.judgment.explanation}</p>
                  )}
                </div>
                <button className="btn btn-secondary" onClick={() => setSelectedResult(null)}>Close</button>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'metrics' && metrics && (
        <div className="grid-2">
          <div className="card">
            <div className="card-header"><div className="card-title">Classification Breakdown</div></div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Classification</th><th>Count</th></tr></thead>
                <tbody>
                  {Object.entries(metrics.by_classification ?? {}).map(([cls, count]) => (
                    <tr key={cls}>
                      <td><StatusBadge status={cls} /></td>
                      <td>{count as number}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="card">
            <div className="card-header"><div className="card-title">ASR by Category</div></div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Mutation Type</th><th>ASR</th></tr></thead>
                <tbody>
                  {Object.entries(metrics.by_category ?? {}).map(([cat, asr]) => (
                    <tr key={cat}>
                      <td style={{ textTransform: 'capitalize' }}>{cat}</td>
                      <td>{(asr as number * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="card">
            <div className="card-header"><div className="card-title">Confidence Summary</div></div>
            <div className="flex gap-3">
              <div><div className="card-value">{((metrics.confidence?.mean ?? 0) * 100).toFixed(0)}%</div><div className="stat-label">Mean</div></div>
              <div><div className="card-value">{((metrics.confidence?.min ?? 0) * 100).toFixed(0)}%</div><div className="stat-label">Min</div></div>
              <div><div className="card-value">{((metrics.confidence?.max ?? 0) * 100).toFixed(0)}%</div><div className="stat-label">Max</div></div>
            </div>
          </div>
        </div>
      )}

      {tab === 'tree' && (
        <MCTSTree tree={treeSnapshot ?? mctsTree ?? null} />
      )}
    </div>
  );
}
