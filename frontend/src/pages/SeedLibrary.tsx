import { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { seedLibraryApi, projectsApi, seedsApi } from '../api/client';
import ConversationView from '../components/ConversationView';

const CATEGORY_LABELS: Record<string, string> = {
  'role-play': 'Role Play',
  'prefix-injection': 'Prefix Injection',
  'few-shot': 'Few-Shot',
  encoding: 'Encoding / Obfuscation',
  'multi-language': 'Multi-Language',
  hypothetical: 'Hypothetical / Academic',
  'payload-splitting': 'Payload Splitting',
  'context-manipulation': 'Context Manipulation',
  'multi-turn': 'Multi-Turn',
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: 'badge badge-success',
  medium: 'badge badge-warning',
  hard: 'badge badge-danger',
};

export default function SeedLibrary() {
  const qc = useQueryClient();
  const [category, setCategory] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [importProject, setImportProject] = useState('');
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [bulkContent, setBulkContent] = useState('');
  const [bulkCategory, setBulkCategory] = useState('general');
  const [presetMsg, setPresetMsg] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const [uploadResult, setUploadResult] = useState<{imported: number} | null>(null);
  const [uploadError, setUploadError] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: categories } = useQuery({
    queryKey: ['seed-library-categories'],
    queryFn: seedLibraryApi.categories,
  });

  const { data: items, isLoading } = useQuery({
    queryKey: ['seed-library', category, difficulty, search],
    queryFn: () => seedLibraryApi.list({ category: category || undefined, difficulty: difficulty || undefined, search: search || undefined }),
  });

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });

  const importMut = useMutation({
    mutationFn: (args: { itemIds: string[]; projectId: string }) =>
      Promise.all(args.itemIds.map(id => seedLibraryApi.importToProject(id, args.projectId))),
    onSuccess: () => { setSelected([]); setImportProject(''); },
  });

  const bulkMut = useMutation({
    mutationFn: () => {
      const items = bulkContent.split('\n').filter(l => l.trim()).map(line => ({
        content: line.trim(),
        category: bulkCategory,
        tags: [],
      }));
      return seedLibraryApi.bulkImport(items);
    },
    onSuccess: () => {
      setBulkContent('');
      setShowBulkImport(false);
      qc.invalidateQueries({ queryKey: ['seed-library'] });
    },
  });

  const loadPresetsMut = useMutation({
    mutationFn: seedLibraryApi.loadPresets,
    onSuccess: (count) => {
      setPresetMsg(`Loaded ${count} preset templates`);
      qc.invalidateQueries({ queryKey: ['seed-library'] });
      qc.invalidateQueries({ queryKey: ['seed-library-categories'] });
      setTimeout(() => setPresetMsg(''), 3000);
    },
  });

  const uploadMut = useMutation({
    mutationFn: (file: File) => seedLibraryApi.upload(file),
    onSuccess: (res) => {
      setUploadResult(res);
      qc.invalidateQueries({ queryKey: ['seed-library'] });
      qc.invalidateQueries({ queryKey: ['seed-library-categories'] });
    },
    onError: (err: any) => {
      setUploadError(err?.response?.data?.detail || 'Upload failed');
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadError('');
      setUploadResult(null);
      uploadMut.mutate(file);
    }
  };

  const toggleSelect = (id: string) => {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  return (
    <div>
      <div className="flex-between mb-4">
        <h2>Seed Library</h2>
        <div className="flex gap-2">
          <button className="btn btn-secondary" onClick={() => setShowUpload(true)}>Upload File</button>
          <button className="btn btn-secondary" onClick={() => setShowBulkImport(true)}>Bulk Import</button>
          <button className="btn btn-secondary" onClick={() => loadPresetsMut.mutate()}>
            {loadPresetsMut.isPending ? 'Loading...' : 'Load Presets'}
          </button>
        </div>
      </div>

      {presetMsg && <div className="alert alert-success mb-4">{presetMsg}</div>}

      {showUpload && (
        <div className="modal-overlay" onClick={() => { setShowUpload(false); setUploadResult(null); setUploadError(''); }}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <h2 className="mb-3">Upload Seed File</h2>
            <p className="text-sm text-muted mb-3">
              Supported formats: <strong>.csv</strong>, <strong>.json</strong>, <strong>.jsonl</strong>, <strong>.yaml</strong>
            </p>
            <ul className="text-sm text-muted mb-3" style={{ paddingLeft: 20 }}>
              <li><strong>CSV:</strong> columns <code>content</code>, <code>category</code>, <code>tags</code>, <code>difficulty</code>, <code>effectiveness</code></li>
              <li><strong>JSON:</strong> array of objects with above fields, or <code>{'{"items": [...]}'}</code></li>
              <li><strong>JSONL:</strong> one JSON object per line</li>
              <li><strong>YAML:</strong> list of mappings with above fields</li>
            </ul>
            <input ref={fileRef} type="file" accept=".csv,.json,.jsonl,.yaml,.yml" onChange={handleFileChange} style={{ marginBottom: 12 }} />
            {uploadMut.isPending && <p className="text-sm">Parsing file...</p>}
            {uploadResult && <div className="alert alert-success">Imported {uploadResult.imported} seeds</div>}
            {uploadError && <div className="alert alert-error">{uploadError}</div>}
            <div className="flex gap-2" style={{ justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => { setShowUpload(false); setUploadResult(null); setUploadError(''); }}>Close</button>
            </div>
          </div>
        </div>
      )}

      {showBulkImport && (
        <div className="modal-overlay" onClick={() => setShowBulkImport(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Bulk Import Seeds</h2>
            <div className="form-group">
              <label>Category</label>
              <select className="form-input" value={bulkCategory} onChange={e => setBulkCategory(e.target.value)}>
                {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
                <option value="general">General</option>
              </select>
            </div>
            <div className="form-group">
              <label>Seed prompts (one per line)</label>
              <textarea className="form-textarea" rows={8} value={bulkContent} onChange={e => setBulkContent(e.target.value)} placeholder="Tell me how to...&#10;Ignore all instructions..." />
            </div>
            <div className="flex gap-2" style={{ justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowBulkImport(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={() => bulkMut.mutate()} disabled={!bulkContent.trim()}>Import {bulkContent.split('\n').filter(l => l.trim()).length} Seeds</button>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-4 mb-4">
        <input className="form-input" style={{ maxWidth: 300 }} placeholder="Search templates..." value={search} onChange={e => setSearch(e.target.value)} />
        <select className="form-input" style={{ maxWidth: 200 }} value={category} onChange={e => setCategory(e.target.value)}>
          <option value="">All Categories</option>
          {(categories || []).map((c: any) => (
            <option key={c.category} value={c.category}>{CATEGORY_LABELS[c.category] || c.category} ({c.count})</option>
          ))}
        </select>
        <select className="form-input" style={{ maxWidth: 150 }} value={difficulty} onChange={e => setDifficulty(e.target.value)}>
          <option value="">All Difficulty</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>

      {selected.length > 0 && projects && (
        <div className="card mb-4 p-3">
          <div className="flex-between">
            <span><strong>{selected.length}</strong> template(s) selected</span>
            <div className="flex gap-2">
              <select className="form-input" value={importProject} onChange={e => setImportProject(e.target.value)}>
                <option value="">Select a project...</option>
                {projects.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              <button className="btn btn-primary btn-sm" disabled={!importProject} onClick={() => importMut.mutate({ itemIds: selected, projectId: importProject })}>
                {importMut.isPending ? 'Importing...' : 'Import to Project'}
              </button>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelected([])}>Clear</button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="empty"><div className="spinner" /></div>
      ) : !items?.length ? (
        <div className="empty">
          <h3>No templates found</h3>
          <p className="mb-4">Load preset templates or import your own.</p>
          <button className="btn btn-primary" onClick={() => loadPresetsMut.mutate()}>Load Presets</button>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ width: 40 }}></th>
                <th>Prompt</th>
                <th>Category</th>
                <th>Difficulty</th>
                <th>Effectiveness</th>
                <th>Tags</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item: any) => (
                <tr key={item.id} className={selected.includes(item.id) ? 'row-selected' : ''}>
                  <td>
                    <input type="checkbox" checked={selected.includes(item.id)} onChange={() => toggleSelect(item.id)} />
                  </td>
                  <td>
                    <code className="text-sm">{item.content.length > 90 ? item.content.slice(0, 90) + '...' : item.content}</code>
                    {item.is_multi_turn && <ConversationView conversation={item.conversation} compact />}
                  </td>
                  <td>
                    <span className="badge badge-info">{CATEGORY_LABELS[item.category] || item.category}</span>
                    {item.is_multi_turn && <span className="badge badge-running" style={{ fontSize: 10, marginLeft: 4 }}>multi-turn</span>}
                  </td>
                  <td><span className={DIFFICULTY_COLORS[item.difficulty] || 'badge'}>{item.difficulty}</span></td>
                  <td>{(item.effectiveness * 100).toFixed(0)}%</td>
                  <td><span className="text-muted text-sm">{item.tags || '—'}</span></td>
                  <td className="text-muted text-sm">{item.source || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
