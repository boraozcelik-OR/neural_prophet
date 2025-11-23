import { Stack } from '@mui/material';
import { ReportSummary } from '../../types/reports';
import ReportSummaryCard from './ReportSummaryCard';

interface Props {
  reports: ReportSummary[];
}

export default function ReportList({ reports }: Props) {
  return (
    <Stack spacing={2}>
      {reports.map((report) => (
        <ReportSummaryCard key={report.report_id} report={report} />
      ))}
    </Stack>
  );
}
