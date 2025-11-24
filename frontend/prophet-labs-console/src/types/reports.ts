import { TrafficTag } from './common';

export interface ReportSummary {
  report_id: string;
  scope: string;
  generated_at: string;
  tag_counts: Record<TrafficTag, number>;
}

export interface ReportDetail extends ReportSummary {
  highlights: {
    top_risks: string[];
    improving: string[];
    worsening: string[];
  };
  notes?: string;
}
