import { apiClient } from './client';
import { PaginatedResponse } from '../types/common';
import { ReportDetail, ReportSummary } from '../types/reports';

export const fetchReports = async (): Promise<PaginatedResponse<ReportSummary>> => {
  const response = await apiClient.get('/api/v1/reports');
  return response.data;
};

export const fetchReportDetail = async (reportId: string): Promise<ReportDetail> => {
  const response = await apiClient.get(`/api/v1/reports/${reportId}`);
  return response.data;
};
