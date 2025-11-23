import { apiClient } from './client';
import { MetricDetail, MetricForecastPoint, MetricOverview, MetricDataPoint } from '../types/metrics';
import { PaginatedResponse } from '../types/common';

export interface MetricsQuery {
  category?: string;
  status?: string;
  search?: string;
}

export const fetchMetrics = async (params: MetricsQuery = {}): Promise<PaginatedResponse<MetricOverview>> => {
  const response = await apiClient.get('/api/v1/metrics', { params });
  return response.data;
};

export const fetchMetricDetail = async (metricId: string): Promise<MetricDetail> => {
  const response = await apiClient.get(`/api/v1/metrics/${metricId}`);
  return response.data;
};

export const fetchMetricSeries = async (metricId: string): Promise<MetricDataPoint[]> => {
  const response = await apiClient.get(`/api/v1/metrics/${metricId}/series`);
  return response.data;
};

export const fetchMetricForecast = async (metricId: string): Promise<MetricForecastPoint[]> => {
  const response = await apiClient.get(`/api/v1/metrics/${metricId}/forecast`);
  return response.data;
};
