import { useQuery } from '@tanstack/react-query';
import { fetchReportDetail, fetchReports } from '../api/reports';
import { PaginatedResponse } from '../types/common';
import { ReportDetail, ReportSummary } from '../types/reports';

const reportKeys = {
  all: ['reports'] as const,
  detail: (reportId: string) => [...reportKeys.all, reportId] as const,
};

export const useReports = () =>
  useQuery<PaginatedResponse<ReportSummary>>({
    queryKey: reportKeys.all,
    queryFn: fetchReports,
  });

export const useReportDetail = (reportId: string) =>
  useQuery<ReportDetail>({
    queryKey: reportKeys.detail(reportId),
    queryFn: () => fetchReportDetail(reportId),
    enabled: Boolean(reportId),
  });
