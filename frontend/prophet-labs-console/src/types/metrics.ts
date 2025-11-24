import { TrafficTag } from './common';

export interface MetricOverview {
  metric_id: string;
  name: string;
  category: string;
  jurisdiction: string;
  latest_value: number | null;
  unit: string;
  tag: TrafficTag;
  trend: 'rising' | 'falling' | 'stable' | 'unknown';
  last_updated?: string;
}

export interface MetricDetail extends MetricOverview {
  tag_explanation?: string;
  evaluation?: {
    mae?: number;
    rmse?: number;
    mape?: number;
  };
  metadata?: Record<string, unknown>;
}

export interface MetricDataPoint {
  ds: string;
  value: number;
  metadata?: Record<string, unknown>;
}

export interface MetricForecastPoint {
  ds: string;
  forecast: number;
  lower?: number;
  upper?: number;
}
