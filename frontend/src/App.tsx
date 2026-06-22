import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import CreateJob from './pages/CreateJob';
import JobDetail from './pages/JobDetail';
import ApiKeys from './pages/ApiKeys';
import Reports from './pages/Reports';
import SeedLibrary from './pages/SeedLibrary';
import Schedules from './pages/Schedules';
import Alerts from './pages/Alerts';
import Login from './pages/Login';
import Signup from './pages/Signup';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:projectId" element={<ProjectDetail />} />
            <Route path="/projects/:projectId/jobs/new" element={<CreateJob />} />
            <Route path="/projects/:projectId/schedules" element={<Schedules />} />
            <Route path="/jobs/:jobId" element={<JobDetail />} />
            <Route path="/keys" element={<ApiKeys />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/seed-library" element={<SeedLibrary />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  );
}
