import { useMemo, useState } from 'react';
import { Box, Grid, Stack, TextField, MenuItem, Chip, Typography, Card, CardContent } from '@mui/material';
import PageHeader from '../components/layout/PageHeader';
import MetricCard from '../components/metrics/MetricCard';
import MetricTable from '../components/metrics/MetricTable';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import { useMetricsOverview } from '../hooks/useMetricsOverview';
import { CATEGORY_LABELS } from '../utils/categoryLabels';
import { TagBadge } from '../components/metrics/TagBadge';
import { useNavigate } from 'react-router-dom';

const TAGS = ['RED', 'GREEN', 'WHITE', 'BLACK'] as const;

export default function DashboardPage() {
  const [category, setCategory] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [search, setSearch] = useState<string>('');
  const navigate = useNavigate();

  const { data, isLoading, isError, refetch } = useMetricsOverview({ category, status, search });

  const summaries = useMemo(() => {
    const counts = { total: 0, RED: 0, GREEN: 0, WHITE: 0, BLACK: 0 } as Record<string, number>;
    if (data) {
      counts.total = data.items.length;
      data.items.forEach((item) => {
        counts[item.tag] = (counts[item.tag] || 0) + 1;
      });
    }
    return counts;
  }, [data]);

  return (
    <Box>
      <PageHeader title="Dashboard" subtitle="Whole-of-government metrics overview" />

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} mb={3}>
        <TextField select label="Category" value={category} onChange={(e) => setCategory(e.target.value)} size="small" sx={{ minWidth: 180 }}>
          <MenuItem value="">All categories</MenuItem>
          {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
            <MenuItem key={key} value={key}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <TextField select label="Status" value={status} onChange={(e) => setStatus(e.target.value)} size="small" sx={{ minWidth: 150 }}>
          <MenuItem value="">All statuses</MenuItem>
          {TAGS.map((tag) => (
            <MenuItem key={tag} value={tag}>
              {tag}
            </MenuItem>
          ))}
        </TextField>
        <TextField label="Search" value={search} onChange={(e) => setSearch(e.target.value)} size="small" fullWidth placeholder="Search metrics" />
      </Stack>

      {isLoading && <LoadingState />}
      {isError && <ErrorState onRetry={() => refetch()} />}
      {data && data.items.length === 0 && <EmptyState message="No metrics match the selected filters." />}

      {data && data.items.length > 0 && (
        <Stack spacing={3}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                    Total metrics
                  </Typography>
                  <Typography variant="h2">{summaries.total}</Typography>
                </CardContent>
              </Card>
            </Grid>
            {TAGS.map((tag) => (
              <Grid item xs={12} md={2.25} key={tag}>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <TagBadge tag={tag} />
                      <Typography variant="h3">{summaries[tag]}</Typography>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          <Grid container spacing={2}>
            {data.items.slice(0, 6).map((metric) => (
              <Grid item xs={12} sm={6} lg={4} key={metric.metric_id}>
                <MetricCard metric={metric} onClick={() => navigate(`/metrics/${metric.metric_id}`)} />
              </Grid>
            ))}
          </Grid>

          <MetricTable metrics={data.items} />
        </Stack>
      )}
    </Box>
  );
}
