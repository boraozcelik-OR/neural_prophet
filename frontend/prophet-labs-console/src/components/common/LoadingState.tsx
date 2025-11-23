import { Box, CircularProgress, Typography } from '@mui/material';

export default function LoadingState({ label = 'Loading data...' }: { label?: string }) {
  return (
    <Box display="flex" flexDirection="column" alignItems="center" py={4} gap={2}>
      <CircularProgress />
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Box>
  );
}
