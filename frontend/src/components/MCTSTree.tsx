import { useCallback, useRef, useState } from 'react';

interface MCTSNode {
  id: string;
  parent_id?: string;
  content: string;
  visits: number;
  reward: number;
  win_rate: number;
  ucb_score: number;
  depth: number;
  children: MCTSNode[];
}

interface MCTSTreeProps {
  tree: MCTSNode | null;
}

const NODE_WIDTH = 200;
const NODE_HEIGHT = 56;
const H_SPACING = 80;
const V_SPACING = 8;
const PADDING = 40;
const ROW_HEIGHT = NODE_HEIGHT + V_SPACING;
const COL_WIDTH = NODE_WIDTH + H_SPACING;

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n) + '...' : s;
}

function winRateColor(winRate: number): string {
  if (winRate >= 0.7) return '#22c55e';
  if (winRate >= 0.4) return '#eab308';
  if (winRate > 0) return '#ef4444';
  return '#6b7280';
}

function countLeafNodes(node: MCTSNode): number {
  if (node.children.length === 0) return 1;
  return node.children.reduce((sum, c) => sum + countLeafNodes(c), 0);
}

function getNodeRadius(node: MCTSNode): number {
  const base = 6;
  if (node.visits <= 1) return base;
  return Math.min(base + Math.log2(node.visits) * 3, 20);
}

interface LayoutNode {
  node: MCTSNode;
  x: number;
  y: number;
  collapsed: boolean;
}

function layoutTree(
  root: MCTSNode,
  collapsed: Set<string>,
  expandRoot: boolean,
): LayoutNode[] {
  const result: LayoutNode[] = [];

  function walk(n: MCTSNode, depth: number, yOffset: number): number {
    const x = PADDING + depth * COL_WIDTH;
    const isCollapsed = depth > 0 && collapsed.has(n.id) && !(depth === 1 && expandRoot);
    result.push({ node: n, x, y: yOffset, collapsed: isCollapsed });

    if (isCollapsed || n.children.length === 0) {
      return yOffset + ROW_HEIGHT;
    }

    let currentY = yOffset;
    for (const child of n.children) {
      currentY = walk(child, depth + 1, currentY);
    }
    return currentY;
  }

  walk(root, 0, PADDING);
  return result;
}

export default function MCTSTree({ tree }: MCTSTreeProps) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [expandRoot, setExpandRoot] = useState(true);
  const svgRef = useRef<SVGSVGElement>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const dragRef = useRef<{ startX: number; startY: number; panX: number; panY: number } | null>(null);

  if (!tree) {
    return (
      <div className="empty">
        <p>No MCTS tree data available. Run a job with <strong>mcts</strong> or <strong>ucb</strong> strategy to generate a tree.</p>
      </div>
    );
  }

  const nodes = layoutTree(tree, collapsed, expandRoot);
  const maxY = nodes.reduce((m, n) => Math.max(m, n.y + NODE_HEIGHT + PADDING), 0);
  const maxX = nodes.reduce((m, n) => Math.max(m, n.x + NODE_WIDTH + PADDING), 0);
  const svgW = Math.max(600, maxX);
  const svgH = Math.max(300, maxY);

  const toggleCollapse = (id: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.max(0.3, Math.min(3, z * delta)));
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0 && e.shiftKey) {
      dragRef.current = { startX: e.clientX, startY: e.clientY, panX: pan.x, panY: pan.y };
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (dragRef.current && e.shiftKey) {
      setPan({
        x: dragRef.current.panX + (e.clientX - dragRef.current.startX),
        y: dragRef.current.panY + (e.clientY - dragRef.current.startY),
      });
    } else {
      dragRef.current = null;
    }
  };

  const handleMouseUp = () => {
    dragRef.current = null;
  };

  const nodeMap = new Map(nodes.map((n) => [n.node.id, n]));

  return (
    <div className="mcts-tree-container" style={{ position: 'relative', overflow: 'hidden', border: '1px solid var(--border)', borderRadius: 8 }}>
      <div className="flex gap-3 text-sm" style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', background: 'var(--bg-card)' }}>
        <label className="flex gap-1" style={{ alignItems: 'center', cursor: 'pointer' }}>
          <input type="checkbox" checked={expandRoot} onChange={() => setExpandRoot((v) => !v)} />
          Show root
        </label>
        <span className="text-muted">{countLeafNodes(tree)} leaves</span>
        <span className="text-muted">{nodes.length} nodes</span>
        <span className="text-muted" style={{ marginLeft: 'auto' }}>Scroll to zoom · Shift+drag to pan</span>
      </div>
      <svg
        ref={svgRef}
        width="100%"
        height={500}
        viewBox={`${pan.x} ${pan.y} ${svgW / zoom} ${500 / zoom}`}
        style={{ background: 'var(--bg-canvas, #1a1a2e)' }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#555" />
          </marker>
        </defs>

        {nodes.map((ln) => {
          if (ln.node.parent_id && nodeMap.has(ln.node.parent_id)) {
            const parentLn = nodeMap.get(ln.node.parent_id)!;
            const sx = parentLn.x + NODE_WIDTH;
            const sy = parentLn.y + NODE_HEIGHT / 2;
            const ex = ln.x;
            const ey = ln.y + NODE_HEIGHT / 2;
            const mx = (sx + ex) / 2;
            return (
              <path
                key={`edge-${ln.node.id}`}
                d={`M ${sx} ${sy} C ${mx} ${sy}, ${mx} ${ey}, ${ex} ${ey}`}
                fill="none"
                stroke="#555"
                strokeWidth={1}
                markerEnd="url(#arrowhead)"
              />
            );
          }
          return null;
        })}

        {nodes.map((ln) => {
          const isRoot = ln.node.depth === 0;
          const wr = ln.node.win_rate;
          const barColor = winRateColor(wr);
          const barW = (NODE_WIDTH - 20) * Math.min(wr, 1);
          const isHovered = hoveredId === ln.node.id;
          const isCollapsed = ln.collapsed && !(ln.node.depth === 0 && expandRoot);
          const nodeRadius = getNodeRadius(ln.node);

          return (
            <g
              key={ln.node.id}
              transform={`translate(${ln.x}, ${ln.y})`}
              onMouseEnter={() => setHoveredId(ln.node.id)}
              onMouseLeave={() => setHoveredId(null)}
              onClick={() => !isRoot && toggleCollapse(ln.node.id)}
              style={{ cursor: isRoot ? 'default' : 'pointer' }}
            >
              <rect
                x={0}
                y={0}
                width={NODE_WIDTH}
                height={NODE_HEIGHT}
                rx={nodeRadius}
                ry={nodeRadius}
                fill={isRoot ? '#1e3a5f' : '#16213e'}
                stroke={isHovered ? '#60a5fa' : barColor}
                strokeWidth={isHovered ? 2 : 1.5}
                opacity={ln.node.visits === 0 ? 0.5 : 1}
              />
              <text x={10} y={18} fill="#e0e0e0" fontSize={12} fontWeight={isRoot ? 700 : 500}>
                {isRoot ? 'Root' : truncate(ln.node.content, 28)}
              </text>
              <rect x={10} y={26} width={NODE_WIDTH - 20} height={6} rx={3} fill="#333" />
              <rect x={10} y={26} width={barW} height={6} rx={3} fill={barColor} opacity={0.8} />
              <text x={10} y={48} fill="#aaa" fontSize={11}>
                visits: {ln.node.visits}
              </text>
              <text x={100} y={48} fill="#aaa" fontSize={11}>
                reward: {ln.node.reward.toFixed(1)}
              </text>
              <text x={NODE_WIDTH - 10} y={18} fill="#60a5fa" fontSize={11} textAnchor="end">
                UCB {ln.node.ucb_score.toFixed(2)}
              </text>
              {isCollapsed && ln.node.children.length > 0 && (
                <text x={NODE_WIDTH / 2} y={NODE_HEIGHT / 2 + 4} fill="#60a5fa" fontSize={16} textAnchor="middle" fontWeight={700}>
                  +{ln.node.children.length}
                </text>
              )}
              {!isRoot && ln.node.children.length > 0 && (
                <text
                  x={NODE_WIDTH - 8}
                  y={NODE_HEIGHT / 2 + 4}
                  fill="#999"
                  fontSize={14}
                  textAnchor="end"
                >
                  {isCollapsed ? '▶' : '▼'}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {hoveredId && (() => {
        const ln = nodes.find((n) => n.node.id === hoveredId);
        if (!ln) return null;
        const n = ln.node;
        return (
          <div
            className="mcts-tooltip"
            style={{
              position: 'absolute',
              bottom: 8,
              left: 8,
              right: 8,
              background: 'rgba(15, 23, 42, 0.95)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '10px 14px',
              fontSize: 13,
              zIndex: 10,
              maxHeight: 200,
              overflow: 'auto',
            }}
          >
            <div className="flex gap-3" style={{ flexWrap: 'wrap' }}>
              <span><strong>Visits:</strong> {n.visits}</span>
              <span><strong>Reward:</strong> {n.reward.toFixed(2)}</span>
              <span><strong>Win Rate:</strong> {(n.win_rate * 100).toFixed(1)}%</span>
              <span><strong>UCB:</strong> {n.ucb_score.toFixed(3)}</span>
              {n.depth === 0 && <span><strong>Depth:</strong> root</span>}
              {n.depth > 0 && <span><strong>Depth:</strong> {n.depth}</span>}
              <span><strong>Children:</strong> {n.children.length}</span>
            </div>
            {n.depth > 0 && (
              <div style={{ marginTop: 6, color: '#ccc', wordBreak: 'break-word' }}>
                <strong>Prompt:</strong> {n.content}
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
}
