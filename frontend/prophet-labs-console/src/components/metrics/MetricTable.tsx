import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableContainer,
  Paper,
  Typography,
} from '@mui/material';
import { MetricOverview } from '../../types/metrics';
import { formatDate, formatNumber } from '../../utils/formatting';
import { TagBadge } from './TagBadge';
import TrendChip from './TrendChip';

interface Props {
  metrics: MetricOverview[];
}

export default function MetricTable({ metrics }: Props) {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small" aria-label="metric table">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Category</TableCell>
            <TableCell>Latest value</TableCell>
            <TableCell>Trend</TableCell>
            <TableCell>Tag</TableCell>
            <TableCell>Last updated</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {metrics.map((metric) => (
            <TableRow key={metric.metric_id} hover>
              <TableCell>
                <Typography variant="body2" fontWeight={600}>
                  {metric.name}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {metric.metric_id}
                </Typography>
              </TableCell>
              <TableCell>{metric.category}</TableCell>
              <TableCell>{formatNumber(metric.latest_value, metric.unit)}</TableCell>
              <TableCell>
                <TrendChip trend={metric.trend} />
              </TableCell>
              <TableCell>
                <TagBadge tag={metric.tag} />
              </TableCell>
              <TableCell>{formatDate(metric.last_updated)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
