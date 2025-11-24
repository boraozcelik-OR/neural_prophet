import { format, parseISO } from 'date-fns';

export const formatNumber = (value: number | null | undefined, unit?: string): string => {
  if (value === null || value === undefined) return '—';
  const formatter = new Intl.NumberFormat('en-AU', {
    maximumFractionDigits: 2,
  });
  return `${formatter.format(value)}${unit ? ` ${unit}` : ''}`.trim();
};

export const formatDate = (dateString?: string): string => {
  if (!dateString) return '—';
  try {
    return format(parseISO(dateString), 'dd MMM yyyy');
  } catch (error) {
    console.error('Failed to format date', error);
    return dateString;
  }
};
