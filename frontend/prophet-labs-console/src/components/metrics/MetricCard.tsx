import { Card, CardContent, Typography, Stack, Box } from '@mui/material';
import { MetricOverview } from '../../types/metrics';
import { formatDate, formatNumber } from '../../utils/formatting';
import { TagBadge } from './TagBadge';
import TrendChip from './TrendChip';

interface Props {
  metric: MetricOverview;
  onClick?: () => void;
}

export default function MetricCard({ metric, onClick }: Props) {
  return (
    <Card
      variant="outlined"
      onClick={onClick}
      sx={{ cursor: onClick ? 'pointer' : 'default', ':hover': { boxShadow: 3 } }}
      aria-label={`Metric ${metric.name}`}
    >
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
          <Box>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              {metric.name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {metric.category} · {metric.jurisdiction}
            </Typography>
          </Box>
          <TagBadge tag={metric.tag} />
        </Stack>
        <Box mt={2} display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h3">{formatNumber(metric.latest_value, metric.unit)}</Typography>
          <TrendChip trend={metric.trend} />
        </Box>
        <Typography variant="body2" color="text.secondary" mt={1}>
          Updated {formatDate(metric.last_updated)}
        </Typography>
      </CardContent>
    </Card>
  );
}
