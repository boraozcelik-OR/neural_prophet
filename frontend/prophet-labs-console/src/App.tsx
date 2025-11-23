import { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Container, CircularProgress } from '@mui/material';
import AppShell from './components/layout/AppShell';

const DashboardPage = lazy(() => import('./routes/DashboardPage'));
const MetricDetailPage = lazy(() => import('./routes/MetricDetailPage'));
const ReportsPage = lazy(() => import('./routes/ReportsPage'));
const NotFoundPage = lazy(() => import('./routes/NotFoundPage'));

export default function App() {
  return (
    <AppShell>
      <Suspense
        fallback={
          <Container sx={{ display: 'flex', justifyContent: 'center', mt: 6 }}>
            <CircularProgress />
          </Container>
        }
      >
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/metrics/:metricId" element={<MetricDetailPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </AppShell>
  );
}
