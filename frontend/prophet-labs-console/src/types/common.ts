export type TrafficTag = 'RED' | 'GREEN' | 'WHITE' | 'BLACK';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}
