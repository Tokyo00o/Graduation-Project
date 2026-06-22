import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { projectsApi, jobsApi, judgesApi } from '../api/client';
import ASRChart from '../components/ASRChart';

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: projects } = useQuery({ queryKey: ['projects'], queryFn: projectsApi.list });
  const allJobs = useQuery({
    queryKey: ['all-jobs'],
    queryFn: async () => {
      if (!projects?.length) return [];
      const results = await Promise.allSettled(
        projects.slice(0, 5).map((p: any) => jobsApi.list(p.id))
      );
      return results.flatMap(r => r.status === 'fulfilled' ? r.value : []);
    },
    enabled: !!projects?.length,
    refetchInterval: 5000,
  });

  const jobs = allJobs.data ?? [];
  const activeJobs = jobs.filter((j: any) => j.status === 'running' || j.status === 'created');
  const completedJobs = jobs.filter((j: any) => j.status === 'completed');
  const avgAsr = completedJobs.length
    ? completedJobs.reduce((s: number, j: any) => s + j.asr, 0) / completedJobs.length
    : 0;

  const chartData = completedJobs.slice(-10).map((j: any) => ({
    name: j.id.slice(0, 8),
    value: j.asr,
  }));

  return (
    <div>
      <div className="flex-between mb-4">
        <h2>Overview</h2>
        <button className="btn btn-primary" onClick={() => navigate('/projects')}>
          + New Project
        </button>
      </div>

      <div className="grid-4">
        <div className="card">
          <div className="card-title">Total Projects</div>
          <div className="card-value">{projects?.length ?? 0}</div>
        </div>
        <div className="card">
          <div className="card-title">Active Jobs</div>
          <div className="card-value">{activeJobs.length}</div>
        </div>
        <div className="card">
          <div className="card-title">Completed Jobs</div>
          <div className="card-value">{completedJobs.length}</div>
        </div>
        <div className="card">
          <div className="card-title">Avg ASR</div>
          <div className="card-value">{(avgAsr * 100).toFixed(1)}%</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div className="card-title">ASR Trend</div>
          </div>
          {chartData.length > 0 ? <ASRChart data={chartData} /> : (
            <div className="empty"><p>No completed jobs yet</p></div>
          )}
        </div>
        <div className="card">
          <div className="card-header">
            <div className="card-title">Active Jobs</div>
          </div>
          {activeJobs.length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>Job ID</th><th>Strategy</th><th>Budget</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {activeJobs.slice(0, 5).map((j: any) => (
                    <tr key={j.id} onClick={() => navigate(`/jobs/${j.id}`)} style={{ cursor: 'pointer' }}>
                      <td className="mono">{j.id.slice(0, 12)}...</td>
                      <td>{j.strategy}</td>
                      <td>{j.budget}</td>
                      <td><span className={`badge badge-${j.status}`}>{j.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty"><p>No active jobs</p></div>
          )}
        </div>
      </div>
    </div>
  );
}
