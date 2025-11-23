import { Box } from '@mui/material';
import PageHeader from '../components/layout/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import ReportList from '../components/reports/ReportList';
import { useReports } from '../hooks/useReports';

export default function ReportsPage() {
  const { data, isLoading, isError, refetch } = useReports();

  return (
    <Box>
      <PageHeader title="Reports" subtitle="Operational and oversight reports" breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Reports' }]} />

      {isLoading && <LoadingState />}
      {isError && <ErrorState onRetry={() => refetch()} />}

      {data && data.items.length === 0 && <EmptyState message="No reports available yet." />}
      {data && data.items.length > 0 && <ReportList reports={data.items} />}
    </Box>
  );
}
