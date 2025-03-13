import React from 'react';
import { AppBar as MuiAppBar, Toolbar, Typography, Box } from '@mui/material';
import UserAvatar from './UserAvatar';
import useAuthStore from '../store/auth';

const AppBar: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <MuiAppBar position="fixed">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Data Dictionary System
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {user && <UserAvatar user={user} />}
        </Box>
      </Toolbar>
    </MuiAppBar>
  );
};

export default AppBar; 