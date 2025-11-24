import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import HorizontalRuleIcon from '@mui/icons-material/HorizontalRule';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { Chip } from '@mui/material';

interface Props {
  trend: 'rising' | 'falling' | 'stable' | 'unknown';
}

export default function TrendChip({ trend }: Props) {
  const map = {
    rising: { icon: <ArrowUpwardIcon fontSize="small" />, label: 'Rising', color: 'success' as const },
    falling: { icon: <ArrowDownwardIcon fontSize="small" />, label: 'Falling', color: 'error' as const },
    stable: { icon: <HorizontalRuleIcon fontSize="small" />, label: 'Stable', color: 'default' as const },
    unknown: { icon: <HelpOutlineIcon fontSize="small" />, label: 'Unknown', color: 'default' as const },
  };

  const { icon, label, color } = map[trend];
  return <Chip icon={icon} label={label} color={color} size="small" variant={color === 'default' ? 'outlined' : 'filled'} />;
}
