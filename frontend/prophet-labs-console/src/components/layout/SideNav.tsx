import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Divider } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import BarChartIcon from '@mui/icons-material/BarChart';
import DescriptionIcon from '@mui/icons-material/Description';
import { Link, useLocation } from 'react-router-dom';

interface Props {
  open: boolean;
  onClose: () => void;
  isMobile: boolean;
}

const width = 260;

export default function SideNav({ open, onClose, isMobile }: Props) {
  const location = useLocation();
  const navItems = [
    { label: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { label: 'Metrics', icon: <BarChartIcon />, path: '/' },
    { label: 'Reports', icon: <DescriptionIcon />, path: '/reports' },
  ];

  return (
    <Drawer
      variant={isMobile ? 'temporary' : 'persistent'}
      open={open}
      onClose={onClose}
      ModalProps={{ keepMounted: true }}
      sx={{
        width,
        '& .MuiDrawer-paper': {
          width,
          boxSizing: 'border-box',
          backgroundColor: '#0B3D91',
          color: 'white',
        },
      }}
    >
      <Toolbar />
      <Divider sx={{ borderColor: 'rgba(255,255,255,0.12)' }} />
      <List>
        {navItems.map((item) => {
          const selected = location.pathname === item.path;
          return (
            <ListItemButton
              key={item.label}
              component={Link}
              to={item.path}
              selected={selected}
              onClick={isMobile ? onClose : undefined}
              sx={{
                color: 'white',
                '&.Mui-selected': { backgroundColor: 'rgba(255,255,255,0.12)' },
              }}
            >
              <ListItemIcon sx={{ color: 'inherit' }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          );
        })}
      </List>
    </Drawer>
  );
}
