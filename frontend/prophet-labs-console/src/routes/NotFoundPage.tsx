import { Box, Button, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import PageHeader from '../components/layout/PageHeader';

export default function NotFoundPage() {
  return (
    <Box>
      <PageHeader title="Page not found" breadcrumbs={[{ label: 'Dashboard', href: '/' }, { label: 'Not found' }]} />
      <Typography variant="body1" color="text.secondary" mb={2}>
        The page you are looking for does not exist or has been moved.
      </Typography>
      <Button variant="contained" component={RouterLink} to="/">
        Return to dashboard
      </Button>
    </Box>
  );
}
