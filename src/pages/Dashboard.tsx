import React, { useEffect, useState } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  CircularProgress,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  Storage as StorageIcon,
  RateReview as ReviewIcon,
  Group as GroupIcon,
} from '@mui/icons-material';
import type { DashboardStats } from '../types/api';
import api from '../config/api';

const StatCard: React.FC<{
  title: string;
  value: number;
  icon: React.ReactNode;
}> = ({ title, value, icon }) => (
  <Paper
    sx={{
      p: 3,
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
    }}
  >
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
      {icon}
      <Typography variant="h6" component="h2" sx={{ ml: 1 }}>
        {title}
      </Typography>
    </Box>
    <Typography variant="h4" component="p">
      {value}
    </Typography>
  </Paper>
);

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    total_entries: 0,
    recent_analyses: 0,
    pending_reviews: 0,
    active_users: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get<DashboardStats>('/api/dashboard/stats');
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        setError('Failed to load dashboard statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="80vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container>
        <Typography color="error" sx={{ mt: 4 }}>
          {error}
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Entries"
            value={stats.total_entries}
            icon={<StorageIcon color="primary" sx={{ fontSize: 40 }} />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Recent Analyses"
            value={stats.recent_analyses}
            icon={<AssessmentIcon color="secondary" sx={{ fontSize: 40 }} />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending Reviews"
            value={stats.pending_reviews}
            icon={<ReviewIcon color="warning" sx={{ fontSize: 40 }} />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Users"
            value={stats.active_users}
            icon={<GroupIcon color="success" sx={{ fontSize: 40 }} />}
          />
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard; 