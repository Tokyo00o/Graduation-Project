import { useState } from 'react';

interface Turn {
  role: 'user' | 'assistant';
  content: string;
}

interface Props {
  conversation: string | Turn[];
  compact?: boolean;
}

function parseConversation(conv: string | Turn[]): Turn[] {
  if (Array.isArray(conv)) return conv;
  try {
    return JSON.parse(conv) as Turn[];
  } catch {
    return [];
  }
}

export default function ConversationView({ conversation, compact }: Props) {
  const turns = parseConversation(conversation);
  const [expanded, setExpanded] = useState(false);
  const displayTurns = compact && !expanded ? turns.slice(0, 2) : turns;

  if (!turns.length) return null;

  return (
    <div className="conversation-view">
      <div className="flex gap-1 mb-1" style={{ alignItems: 'center' }}>
        <span className="badge badge-running" style={{ fontSize: 10 }}>Multi-Turn</span>
        <span className="text-muted text-xs">{turns.length} turns</span>
        {compact && turns.length > 2 && (
          <button
            className="btn btn-sm text-xs"
            style={{ padding: '0 6px', fontSize: 11 }}
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Show less' : `Show all (${turns.length})`}
          </button>
        )}
      </div>
      <div style={{ borderLeft: '2px solid var(--border)', paddingLeft: 10, fontSize: 12 }}>
        {displayTurns.map((turn, i) => (
          <div key={i} style={{ marginBottom: 6 }}>
            <span style={{ fontWeight: 600, color: turn.role === 'user' ? 'var(--accent)' : 'var(--success)' }}>
              {turn.role === 'user' ? '👤 User' : '🤖 Assistant'}:
            </span>
            <span style={{ marginLeft: 4, color: 'var(--text-muted)' }}>
              {turn.content.length > 200 ? turn.content.slice(0, 200) + '...' : turn.content}
            </span>
          </div>
        ))}
      </div>
      <style>{`
        .conversation-view { margin: 4px 0; }
        .text-xs { font-size: 11px; }
        .btn-sm { background: none; border: 1px solid var(--border); border-radius: 4px; cursor: pointer; }
        .btn-sm:hover { background: var(--bg-secondary); }
      `}</style>
    </div>
  );
}
