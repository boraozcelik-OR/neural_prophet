import { useParams } from 'react-router-dom';
import { Box, Grid, Paper, Stack, Typography } from '@mui/material';
import PageHeader from '../components/layout/PageHeader';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import TimeSeriesChart from '../components/charts/TimeSeriesChart';
import ForecastChart from '../components/charts/ForecastChart';
import { useMetricDetail, useMetricForecast, useMetricSeries } from '../hooks/useMetricDetail';
import { formatDate, formatNumber } from '../utils/formatting';
import { TagBadge } from '../components/metrics/TagBadge';
import TrendChip from '../components/metrics/TrendChip';

export default function MetricDetailPage() {
  const { metricId = '' } = useParams();
  const detailQuery = useMetricDetail(metricId);
  const seriesQuery = useMetricSeries(metricId);
  const forecastQuery = useMetricForecast(metricId);

  if (detailQuery.isLoading) return <LoadingState label="Loading metric" />;
  if (detailQuery.isError || !detailQuery.data) return <ErrorState onRetry={() => detailQuery.refetch()} />;

  const metric = detailQuery.data;

  return (
    <Box>
      <PageHeader
        title={metric.name}
        subtitle={`${metric.category} · ${metric.jurisdiction} · ${metric.metric_id}`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/' },
          { label: 'Metric detail' },
        ]}
        actions={<TagBadge tag={metric.tag} size="medium" />}
      />

      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={3}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Latest value
            </Typography>
            <Typography variant="h3">{formatNumber(metric.latest_value, metric.unit)}</Typography>
            <Typography variant="body2" color="text.secondary">
              As of {formatDate(metric.last_updated)}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Trend
            </Typography>
            <Box mt={1}>
              <TrendChip trend={metric.trend} />
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Evaluation
            </Typography>
            <Stack spacing={0.5} mt={1}>
              <Typography variant="body2">MAE: {metric.evaluation?.mae ?? '—'}</Typography>
              <Typography variant="body2">RMSE: {metric.evaluation?.rmse ?? '—'}</Typography>
              <Typography variant="body2">MAPE: {metric.evaluation?.mape ?? '—'}</Typography>
            </Stack>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Tag explanation
            </Typography>
            <Typography variant="body2" mt={1}>
              {metric.tag_explanation || 'No explanation provided.'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} lg={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Historical series
            </Typography>
            {seriesQuery.isLoading && <LoadingState label="Loading history" />}
            {seriesQuery.isError && <ErrorState onRetry={() => seriesQuery.refetch()} />}
            {seriesQuery.data && seriesQuery.data.length > 0 && <TimeSeriesChart data={seriesQuery.data} />}
          </Paper>
        </Grid>
        <Grid item xs={12} lg={6}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Forecast
            </Typography>
            {forecastQuery.isLoading && <LoadingState label="Loading forecast" />}
            {forecastQuery.isError && <ErrorState onRetry={() => forecastQuery.refetch()} />}
            {forecastQuery.data && seriesQuery.data && (
              <ForecastChart history={seriesQuery.data.slice(-120)} forecast={forecastQuery.data} />
            )}
          </Paper>
        </Grid>
      </Grid>

      <Box mt={3}>
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Metadata
          </Typography>
          <Stack spacing={1}>
            {metric.metadata ? (
              Object.entries(metric.metadata).map(([key, value]) => (
                <Stack direction="row" key={key} spacing={1}>
                  <Typography variant="body2" fontWeight={600} width={180}>
                    {key}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {String(value)}
                  </Typography>
                </Stack>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                No metadata available.
              </Typography>
            )}
          </Stack>
        </Paper>
      </Box>
    </Box>
  );
}
