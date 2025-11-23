import { useQuery } from '@tanstack/react-query';
import { fetchMetrics, MetricsQuery } from '../api/metrics';
import { MetricOverview } from '../types/metrics';
import { PaginatedResponse } from '../types/common';

export const metricsKeys = {
  all: ['metrics'] as const,
  list: (params: MetricsQuery) => [...metricsKeys.all, params] as const,
};

export const useMetricsOverview = (params: MetricsQuery) =>
  useQuery<PaginatedResponse<MetricOverview>>({
    queryKey: metricsKeys.list(params),
    queryFn: () => fetchMetrics(params),
  });
