export const CATEGORY_LABELS: Record<string, string> = {
  economy: 'Economy',
  health: 'Health & Hospitals',
  crime: 'Crime & Justice',
  defence: 'Defence & Security',
  education: 'Education',
  labour: 'Labour & Demographics',
  energy: 'Energy & Environment',
  budget: 'Budget & Finance',
};

export const getCategoryLabel = (category?: string): string => {
  if (!category) return 'All Categories';
  return CATEGORY_LABELS[category] || category;
};
