import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { projectsApi } from '../api/client';

export default function Projects() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });

  const createMut = useMutation({
    mutationFn: () => projectsApi.create({ name, description: desc }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['projects'] }); setShowModal(false); setName(''); setDesc(''); },
  });

  return (
    <div>
      <div className="flex-between mb-4">
        <h2>Projects</h2>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ New Project</button>
      </div>

      {isLoading ? <div className="empty"><div className="spinner" /></div> : !projects?.length ? (
        <div className="empty">
          <h3>No projects yet</h3>
          <p className="mb-4">Create your first project to start fuzzing.</p>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>Create Project</button>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p: any) => (
                <tr key={p.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/projects/${p.id}`)}>
                  <td><strong>{p.name}</strong></td>
                  <td className="text-muted truncate">{p.description || '—'}</td>
                  <td className="text-muted text-sm">{new Date(p.created_at).toLocaleDateString()}</td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={(e) => { e.stopPropagation(); navigate(`/projects/${p.id}`); }}>Open</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>New Project</h2>
            <div className="form-group">
              <label>Name</label>
              <input className="form-input" value={name} onChange={e => setName(e.target.value)} placeholder="My Project" />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea className="form-textarea" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Optional description" />
            </div>
            <div className="flex gap-2" style={{ justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={() => createMut.mutate()} disabled={!name}>Create</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
