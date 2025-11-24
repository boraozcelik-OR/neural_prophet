import { Card, CardContent, Stack, Typography, Chip } from '@mui/material';
import { ReportSummary } from '../../types/reports';
import { formatDate } from '../../utils/formatting';

interface Props {
  report: ReportSummary;
}

export default function ReportSummaryCard({ report }: Props) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
          <div>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              {report.scope} report
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Generated {formatDate(report.generated_at)}
            </Typography>
          </div>
          <Stack direction="row" spacing={1}>
            {Object.entries(report.tag_counts).map(([tag, count]) => (
              <Chip key={tag} label={`${tag}: ${count}`} size="small" />
            ))}
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
