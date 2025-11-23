import { ReactNode, useState } from 'react';
import { Box, Toolbar, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import TopBar from './TopBar';
import SideNav from './SideNav';

interface Props {
  children: ReactNode;
}

export default function AppShell({ children }: Props) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [navOpen, setNavOpen] = useState(!isMobile);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: theme.palette.background.default }}>
      <TopBar onMenuToggle={() => setNavOpen((open) => !open)} />
      <SideNav open={navOpen} onClose={() => setNavOpen(false)} isMobile={isMobile} />
      <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, md: 3 } }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
