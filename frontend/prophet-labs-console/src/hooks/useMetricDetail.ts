import { useQuery } from '@tanstack/react-query';
import { fetchMetricDetail, fetchMetricForecast, fetchMetricSeries } from '../api/metrics';
import { MetricDataPoint, MetricDetail, MetricForecastPoint } from '../types/metrics';

const metricKeys = {
  base: (metricId: string) => ['metric', metricId] as const,
  detail: (metricId: string) => [...metricKeys.base(metricId), 'detail'] as const,
  series: (metricId: string) => [...metricKeys.base(metricId), 'series'] as const,
  forecast: (metricId: string) => [...metricKeys.base(metricId), 'forecast'] as const,
};

export const useMetricDetail = (metricId: string) =>
  useQuery<MetricDetail>({
    queryKey: metricKeys.detail(metricId),
    queryFn: () => fetchMetricDetail(metricId),
    enabled: Boolean(metricId),
  });

export const useMetricSeries = (metricId: string) =>
  useQuery<MetricDataPoint[]>({
    queryKey: metricKeys.series(metricId),
    queryFn: () => fetchMetricSeries(metricId),
    enabled: Boolean(metricId),
  });

export const useMetricForecast = (metricId: string) =>
  useQuery<MetricForecastPoint[]>({
    queryKey: metricKeys.forecast(metricId),
    queryFn: () => fetchMetricForecast(metricId),
    enabled: Boolean(metricId),
  });
