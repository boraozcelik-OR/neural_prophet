import MenuIcon from '@mui/icons-material/Menu';
import { AppBar, Box, IconButton, Toolbar, Typography, Chip } from '@mui/material';
import { ENV } from '../../config/env';

interface Props {
  onMenuToggle: () => void;
}

export default function TopBar({ onMenuToggle }: Props) {
  return (
    <AppBar position="fixed" color="inherit" sx={{ backgroundColor: 'white' }}>
      <Toolbar>
        <IconButton edge="start" color="inherit" aria-label="menu" onClick={onMenuToggle} sx={{ mr: 2 }}>
          <MenuIcon />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 700 }}>
            Prophet Labs
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Australian Government Analytics Console
          </Typography>
        </Box>
        <Chip label={ENV.appEnv.toUpperCase()} color="primary" variant="outlined" size="small" />
      </Toolbar>
    </AppBar>
  );
}
