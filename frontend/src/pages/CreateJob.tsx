import { useState } from 'react';
type MutationKey = 'generate' | 'crossover' | 'expand' | 'shorten' | 'rephrase';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi, seedsApi, jobsApi, judgesApi } from '../api/client';
import ConversationView from '../components/ConversationView';

const STEPS = ['Target', 'Seeds', 'Mutation', 'Strategy', 'Budget', 'Review'];

const STRATEGIES = [
  { value: 'random', desc: 'Uniform random sampling from seed pool' },
  { value: 'round_robin', desc: 'Sequential rotation through seeds' },
  { value: 'ucb', desc: 'Upper Confidence Bound exploration' },
  { value: 'mcts', desc: 'Monte Carlo Tree Search-guided exploration' },
];

const JUDGES = [
  { value: 'roberta', desc: 'ML classifier (TF-IDF + Logistic Regression)' },
  { value: 'rule', desc: 'Pattern-based rule engine' },
  { value: 'gpt4', desc: 'GPT-4 API judge (requires API key)' },
];

export default function CreateJob() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [step, setStep] = useState(0);
  const [targetModel, setTargetModel] = useState('gpt-4o');
  const [selectedSeeds, setSelectedSeeds] = useState<string[]>([]);
  const [mutations, setMutations] = useState<Record<MutationKey, boolean>>({
    generate: true, crossover: true, expand: true, shorten: true, rephrase: true,
  });
  const [strategy, setStrategy] = useState('mcts');
  const [judge, setJudge] = useState('roberta');
  const [budget, setBudget] = useState(1000);

  const { data: project } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  });

  const { data: seeds } = useQuery({
    queryKey: ['seeds', projectId],
    queryFn: () => seedsApi.list(projectId!),
    enabled: !!projectId,
  });

  const { data: judgeList } = useQuery({
    queryKey: ['judges'],
    queryFn: judgesApi.list,
  });

  const createJob = useMutation({
    mutationFn: () => jobsApi.create(projectId!, {
      strategy, budget, judge, target_model: targetModel,
      seed_ids: selectedSeeds.length > 0 ? selectedSeeds : undefined,
    }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['jobs', projectId] });
      navigate(`/jobs/${data.id}`);
    },
  });

  const next = () => setStep(s => Math.min(s + 1, STEPS.length - 1));
  const prev = () => setStep(s => Math.max(s - 1, 0));

  const toggleSeed = (id: string) => {
    setSelectedSeeds(prev =>
      prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
    );
  };

  return (
    <div>
      <h2 className="mb-4">New Fuzzing Job {project ? `— ${project.name}` : ''}</h2>

      <ul className="wizard-steps">
        {STEPS.map((s, i) => (
          <li key={s}
            className={`wizard-step ${i === step ? 'active' : ''} ${i < step ? 'completed' : ''}`}
            onClick={() => i < step ? setStep(i) : null}
            style={i < step ? { cursor: 'pointer' } : {}}
          >
            <span className="step-num">{i < step ? '✓' : i + 1}</span> {s}
          </li>
        ))}
      </ul>

      {step === 0 && (
        <div className="card">
          <h3 className="mb-3">Step 1: Select Target Model</h3>
          <div className="form-group">
            <label>Provider / Model</label>
            <select className="form-select" value={targetModel} onChange={e => setTargetModel(e.target.value)}>
              <option value="gpt-4o">OpenAI — GPT-4o</option>
              <option value="gpt-4-turbo">OpenAI — GPT-4 Turbo</option>
              <option value="claude-3-opus">Anthropic — Claude 3 Opus</option>
              <option value="claude-3-sonnet">Anthropic — Claude 3 Sonnet</option>
              <option value="gemini-pro">Google — Gemini Pro</option>
              <option value="mistral-large">Mistral — Large</option>
              <option value="mock">Mock Simulator (dev mode)</option>
            </select>
          </div>
          <div className="form-group">
            <label>Judge Model</label>
            <select className="form-select" value={judge} onChange={e => setJudge(e.target.value)}>
              {JUDGES.map(j => <option key={j.value} value={j.value}>{j.value} — {j.desc}</option>)}
            </select>
          </div>
          <div className="flex gap-2" style={{ justifyContent: 'flex-end' }}>
            <button className="btn btn-primary" onClick={next}>Next</button>
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="card">
          <h3 className="mb-3">Step 2: Select Seeds</h3>
          {(!seeds || seeds.length === 0) ? (
            <div className="empty">
              <p>No seeds available. Add seeds in the project first.</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead><tr><th style={{ width: 40 }}></th><th>Content</th><th>Type</th><th>Tags</th></tr></thead>
                  <tbody>
                    {seeds.map((s: any) => (
                      <tr key={s.id}>
                        <td><input type="checkbox" checked={selectedSeeds.includes(s.id)} onChange={() => toggleSeed(s.id)} /></td>
                        <td className="mono truncate">
                          {s.content}
                          {s.is_multi_turn && <ConversationView conversation={s.conversation} compact />}
                        </td>
                        <td>{s.is_multi_turn ? <span className="badge badge-running" style={{ fontSize: 10 }}>multi-turn</span> : <span className="badge badge-pending" style={{ fontSize: 10 }}>single</span>}</td>
                        <td>{s.tags || '—'}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="flex gap-2" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <button className="btn btn-secondary" onClick={prev}>Back</button>
            <button className="btn btn-primary" onClick={next}>Next ({selectedSeeds.length || 'all'} selected)</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h3 className="mb-3">Step 3: Mutation Configuration</h3>
          <p className="text-muted text-sm mb-4">Enable or disable mutation operators for this job.</p>
          {(Object.entries(mutations) as [MutationKey, boolean][]).map(([key, val]) => (
            <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', cursor: 'pointer' }}>
              <input type="checkbox" checked={val} onChange={() => setMutations(prev => ({ ...prev, [key]: !prev[key] }))} />
              <span style={{ fontWeight: 500, textTransform: 'capitalize' }}>{key}</span>
            </label>
          ))}
          <div className="flex gap-2" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <button className="btn btn-secondary" onClick={prev}>Back</button>
            <button className="btn btn-primary" onClick={next}>Next</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card">
          <h3 className="mb-3">Step 4: Strategy Selection</h3>
          {STRATEGIES.map(s => (
            <label key={s.value} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '12px 0', cursor: 'pointer', borderBottom: '1px solid var(--border)' }}>
              <input type="radio" name="strategy" checked={strategy === s.value} onChange={() => setStrategy(s.value)} style={{ marginTop: 3 }} />
              <div>
                <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{s.value.replace('_', ' ')}</div>
                <div className="text-muted text-sm">{s.desc}</div>
              </div>
            </label>
          ))}
          <div className="flex gap-2" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <button className="btn btn-secondary" onClick={prev}>Back</button>
            <button className="btn btn-primary" onClick={next}>Next</button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="card">
          <h3 className="mb-3">Step 5: Budget</h3>
          <div className="form-group">
            <label>Query Limit</label>
            <input className="form-input" type="number" value={budget} onChange={e => setBudget(Number(e.target.value))} min={1} max={100000} />
            <span className="text-muted text-sm">Total number of mutation iterations to run</span>
          </div>
          <div className="flex gap-2" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <button className="btn btn-secondary" onClick={prev}>Back</button>
            <button className="btn btn-primary" onClick={next}>Review</button>
          </div>
        </div>
      )}

      {step === 5 && (
        <div className="card">
          <h3 className="mb-3">Step 6: Review & Launch</h3>
          <table style={{ fontSize: 14 }}>
            <tbody>
              <tr><td style={{ padding: '8px 12px', color: 'var(--text-muted)', width: 140 }}>Target Model</td><td>{targetModel}</td></tr>
              <tr><td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>Judge</td><td>{judge}</td></tr>
              <tr><td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>Strategy</td><td style={{ textTransform: 'capitalize' }}>{strategy.replace('_', ' ')}</td></tr>
              <tr><td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>Budget</td><td>{budget} queries</td></tr>
              <tr><td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>Seeds</td><td>{selectedSeeds.length || 'All available'}</td></tr>
              <tr><td style={{ padding: '8px 12px', color: 'var(--text-muted)' }}>Mutations</td>              <td>{(Object.entries(mutations) as [MutationKey, boolean][]).filter(([,v]) => v).map(([k]) => k).join(', ')}</td></tr>
            </tbody>
          </table>
          <div className="flex gap-2" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <button className="btn btn-secondary" onClick={prev}>Back</button>
            <button className="btn btn-primary" onClick={() => createJob.mutate()} disabled={createJob.isPending}>
              {createJob.isPending ? 'Launching...' : 'Launch Job'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
