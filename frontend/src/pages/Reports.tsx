import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { reportsApi } from '../api/client';

export default function Reports() {
  const navigate = useNavigate();
  const [selectedJob, setSelectedJob] = useState<string | null>(null);

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['reports-summary'],
    queryFn: () => reportsApi.summary({ limit: 100 }),
  });

  const { data: compliance } = useQuery({
    queryKey: ['compliance', selectedJob],
    queryFn: () => reportsApi.compliance(selectedJob!),
    enabled: !!selectedJob,
  });

  const { data: frameworks } = useQuery({
    queryKey: ['frameworks'],
    queryFn: () => reportsApi.frameworks(),
  });

  const doExport = (jobId: string, format: 'json' | 'csv' | 'html' | 'pdf') => {
    const url = `/api/v1/reports/${jobId}/export/${format}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `report_${jobId}.${format}`;
    a.click();
  };

  if (isLoading) {
    return <div className="empty"><div className="spinner" /></div>;
  }

  if (!jobs?.length) {
    return (
      <div className="empty">
        <h3>No reports yet</h3>
        <p className="mb-4">Complete a fuzzing job to generate a report.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex-between mb-4">
        <h2>Reports</h2>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>Project</th>
              <th>Strategy</th>
              <th>Status</th>
              <th>ASR</th>
              <th>Budget</th>
              <th>Created</th>
              <th>Compliance</th>
              <th>Export</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j: any) => (
              <tr key={j.job_id}>
                <td>
                  <a href="#" onClick={(e) => { e.preventDefault(); navigate(`/jobs/${j.job_id}`); }} className="link">
                    {j.job_id}
                  </a>
                </td>
                <td className="text-muted">{j.project_name || '—'}</td>
                <td className="text-sm">{j.strategy}</td>
                <td>
                  <span className={`badge ${j.status === 'completed' ? 'badge-green' : j.status === 'failed' ? 'badge-red' : 'badge-yellow'}`}>
                    {j.status}
                  </span>
                </td>
                <td className="font-mono">{(j.asr * 100).toFixed(1)}%</td>
                <td className="text-sm">{j.queries_used}/{j.budget}</td>
                <td className="text-sm text-muted">{new Date(j.created_at).toLocaleDateString()}</td>
                <td>
                  <button className="btn btn-secondary btn-xs" onClick={() => setSelectedJob(selectedJob === j.job_id ? null : j.job_id)}>
                    {selectedJob === j.job_id ? 'Hide' : 'Compliance'}
                  </button>
                </td>
                <td>
                  <div className="flex gap-1">
                    <button className="btn btn-secondary btn-xs" onClick={() => doExport(j.job_id, 'pdf')}>PDF</button>
                    <button className="btn btn-secondary btn-xs" onClick={() => doExport(j.job_id, 'json')}>JSON</button>
                    <button className="btn btn-secondary btn-xs" onClick={() => doExport(j.job_id, 'csv')}>CSV</button>
                    <button className="btn btn-secondary btn-xs" onClick={() => doExport(j.job_id, 'html')}>HTML</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedJob && compliance && (
        <div className="card mt-4">
          <div className="card-header">
            <h3>Compliance Mapping — {selectedJob}</h3>
          </div>
          <div className="card-body">
            <div className="flex gap-4 mb-3" style={{ alignItems: 'baseline' }}>
              <span style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)' }}>{compliance.overall_compliance_score}%</span>
              <span className="text-muted text-sm">Overall Compliance Score</span>
            </div>
            <div className="flex gap-3 mb-4">
              <div className="stat-sm"><span className="stat-val">{compliance.total_jailbreaks}</span><span className="stat-lbl">Jailbreaks</span></div>
              <div className="stat-sm"><span className="stat-val">{(compliance.asr_top1 * 100).toFixed(1)}%</span><span className="stat-lbl">ASR</span></div>
            </div>
            {Object.entries(compliance.frameworks as Record<string, any>).map(([key, fw]) => (
              <div key={key} className="mb-4">
                <div className="flex-between">
                  <h4 style={{ fontSize: 14 }}>{fw.name}</h4>
                  <span className={`badge ${fw.compliance_score >= 80 ? 'badge-green' : fw.compliance_score >= 50 ? 'badge-yellow' : 'badge-red'}`}>
                    {fw.compliance_score}%
                  </span>
                </div>
                {Object.keys(fw.categories).length > 0 ? (
                  <div className="table-wrap" style={{ marginTop: 8 }}>
                    <table>
                      <thead>
                        <tr><th>Category</th><th>Findings</th><th>Max Severity</th></tr>
                      </thead>
                      <tbody>
                        {Object.entries(fw.categories as Record<string, any>).map(([cid, cat]) => (
                          <tr key={cid}>
                            <td><strong>{cid}</strong>: {cat.title}</td>
                            <td>{cat.finding_count}</td>
                            <td>
                              <span className={`badge ${cat.max_severity === 'critical' || cat.max_severity === 'high' ? 'badge-red' : cat.max_severity === 'medium' ? 'badge-yellow' : 'badge-green'}`}>
                                {cat.max_severity}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-muted text-sm">No findings for this framework.</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
