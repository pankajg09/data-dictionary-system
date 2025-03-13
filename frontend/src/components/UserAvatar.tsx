import React from 'react';
import { Avatar, Box, Typography } from '@mui/material';
import type { User } from '../types/auth';

interface UserAvatarProps {
  user: User;
}

const UserAvatar: React.FC<UserAvatarProps> = ({ user }) => {
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase();
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Typography variant="body1" sx={{ mr: 1 }}>
        {user.name}
      </Typography>
      <Avatar
        alt={user.name}
        src={user.picture}
        sx={{ width: 32, height: 32 }}
      >
        {!user.picture && getInitials(user.name)}
      </Avatar>
    </Box>
  );
};

export default UserAvatar; 