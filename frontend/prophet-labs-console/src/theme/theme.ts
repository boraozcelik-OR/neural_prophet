import { createTheme } from '@mui/material/styles';
import { palette } from './palette';

export const theme = createTheme({
  palette: {
    primary: {
      main: palette.primary,
    },
    secondary: {
      main: palette.secondary,
    },
    background: {
      default: palette.background,
      paper: palette.surface,
    },
    text: {
      primary: palette.text,
      secondary: palette.mutedText,
    },
  },
  typography: {
    fontFamily: 'Inter, "Helvetica Neue", Arial, sans-serif',
    h1: { fontSize: '1.5rem', fontWeight: 600 },
    h2: { fontSize: '1.25rem', fontWeight: 600 },
    h3: { fontSize: '1.125rem', fontWeight: 600 },
    subtitle1: { fontSize: '1rem', fontWeight: 500 },
    body1: { fontSize: '0.95rem' },
    body2: { fontSize: '0.875rem' },
    caption: { fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: 0.4 },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderColor: palette.border,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          borderBottom: `1px solid ${palette.border}`,
        },
      },
    },
  },
});
