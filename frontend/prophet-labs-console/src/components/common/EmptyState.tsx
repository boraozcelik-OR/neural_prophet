import { Box, Typography } from '@mui/material';

export default function EmptyState({ message = 'No data available.' }: { message?: string }) {
  return (
    <Box py={4} textAlign="center">
      <Typography variant="body2" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}
