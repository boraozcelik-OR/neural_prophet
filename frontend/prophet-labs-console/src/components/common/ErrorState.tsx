import { Alert, AlertTitle, Button, Stack } from '@mui/material';

interface Props {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({ message = 'Unable to load data.', onRetry }: Props) {
  return (
    <Stack spacing={2} py={3} alignItems="flex-start">
      <Alert severity="error">
        <AlertTitle>Error</AlertTitle>
        {message}
      </Alert>
      {onRetry && (
        <Button variant="outlined" onClick={onRetry} size="small">
          Retry
        </Button>
      )}
    </Stack>
  );
}
