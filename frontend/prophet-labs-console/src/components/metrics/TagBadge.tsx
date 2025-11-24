import { Chip } from '@mui/material';
import { TrafficTag } from '../../types/common';
import { palette } from '../../theme/palette';

const tagStyles: Record<TrafficTag, { color: string; bg: string }> = {
  RED: { color: '#fff', bg: palette.tags.RED },
  GREEN: { color: '#fff', bg: palette.tags.GREEN },
  WHITE: { color: palette.text, bg: palette.tags.WHITE },
  BLACK: { color: '#fff', bg: palette.tags.BLACK },
};

export function TagBadge({ tag, size = 'small' }: { tag: TrafficTag; size?: 'small' | 'medium' }) {
  const style = tagStyles[tag];
  return <Chip label={tag} size={size} sx={{ color: style.color, backgroundColor: style.bg, fontWeight: 700 }} />;
}
