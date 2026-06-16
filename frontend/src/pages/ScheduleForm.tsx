import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { schedulesApi } from '../api/client';

interface Props {
  projectId: string;
  schedule?: any;
  onClose: () => void;
}

const STRATEGIES = ['random', 'round_robin', 'ucb', 'mcts'];
const JUDGES = ['roberta', 'gpt-4', 'gpt-4o', 'mock'];

export default function ScheduleForm({ projectId, schedule, onClose }: Props) {
  const qc = useQueryClient();
  const [name, setName] = useState(schedule?.name ?? '');
  const [strategy, setStrategy] = useState(schedule?.strategy ?? 'random');
  const [budget, setBudget] = useState(schedule?.budget ?? 100);
  const [judge, setJudge] = useState(schedule?.judge ?? 'roberta');
  const [targetModel, setTargetModel] = useState(schedule?.target_model ?? '');
  const [cron, setCron] = useState(schedule?.cron_expression ?? '0 */6 * * *');
  const [threshold, setThreshold] = useState(schedule?.asr_threshold != null ? String(schedule.asr_threshold * 100) : '');
  const [slackUrl, setSlackUrl] = useState(schedule?.slack_webhook_url ?? '');
  const [webhookUrl, setWebhookUrl] = useState(schedule?.webhook_url ?? '');

  const saveMut = useMutation({
    mutationFn: () => {
      const data: any = { name, strategy, budget: Number(budget), judge, target_model: targetModel, cron_expression: cron };
      if (threshold) data.asr_threshold = Number(threshold) / 100;
      if (slackUrl) data.slack_webhook_url = slackUrl;
      if (webhookUrl) data.webhook_url = webhookUrl;
      if (schedule) return schedulesApi.update(schedule.id, data);
      return schedulesApi.create(projectId, data);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['schedules', projectId] });
      onClose();
    },
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>
        <h2 className="mb-3">{schedule ? 'Edit Schedule' : 'New Schedule'}</h2>

        <div className="form-group">
          <label>Name</label>
          <input className="form-input" value={name} onChange={e => setName(e.target.value)} placeholder="Daily scan" />
        </div>

        <div className="form-group">
          <label>Strategy</label>
          <select className="form-select" value={strategy} onChange={e => setStrategy(e.target.value)}>
            {STRATEGIES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label>Judge</label>
          <select className="form-select" value={judge} onChange={e => setJudge(e.target.value)}>
            {JUDGES.map(j => <option key={j} value={j}>{j}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label>Budget</label>
          <input className="form-input" type="number" min={1} value={budget} onChange={e => setBudget(Number(e.target.value))} />
        </div>

        <div className="form-group">
          <label>Target Model (optional)</label>
          <input className="form-input" value={targetModel} onChange={e => setTargetModel(e.target.value)} placeholder="gpt-4o" />
        </div>

        <div className="form-group">
          <label>Cron Expression</label>
          <input className="form-input" value={cron} onChange={e => setCron(e.target.value)} />
          <span className="text-muted text-sm">e.g. <code>0 */6 * * *</code> (every 6h)</span>
        </div>

        <div className="form-group">
          <label>ASR Alert Threshold % (optional)</label>
          <input className="form-input" type="number" min={0} max={100} value={threshold} onChange={e => setThreshold(e.target.value)} placeholder="e.g. 50" />
        </div>

        <div className="form-group">
          <label>Slack Webhook URL (optional)</label>
          <input className="form-input" value={slackUrl} onChange={e => setSlackUrl(e.target.value)} placeholder="https://hooks.slack.com/services/..." />
        </div>

        <div className="form-group">
          <label>Custom Webhook URL (optional)</label>
          <input className="form-input" value={webhookUrl} onChange={e => setWebhookUrl(e.target.value)} placeholder="https://example.com/webhook" />
        </div>

        <div className="flex gap-2" style={{ justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={() => saveMut.mutate()} disabled={!name || saveMut.isPending}>
            {schedule ? 'Save' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
}
