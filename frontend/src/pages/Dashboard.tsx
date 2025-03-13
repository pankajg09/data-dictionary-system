import React, { useState, useEffect } from 'react';
import { Container, Typography, Grid, Paper, CircularProgress, Alert } from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import RateReviewIcon from '@mui/icons-material/RateReview';
import PeopleIcon from '@mui/icons-material/People';
import api from '../config/api';

interface DashboardStats {
  total_entries: number;
  recent_analyses: number;
  pending_reviews: number;
  active_users: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    total_entries: 0,
    recent_analyses: 0,
    pending_reviews: 0,
    active_users: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get<DashboardStats>('/api/dashboard/stats');
        setStats(response.data);
      } catch (err) {
        console.error('Error fetching dashboard stats:', err);
        setError('Failed to load dashboard statistics');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6} lg={3}>
          <Paper 
            sx={{ 
              p: 2, 
              display: 'flex', 
              flexDirection: 'column', 
              height: 140,
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <StorageIcon 
              sx={{ 
                position: 'absolute',
                right: -20,
                bottom: -20,
                fontSize: 100,
                opacity: 0.1,
                transform: 'rotate(-10deg)'
              }} 
            />
            <Typography variant="h6" gutterBottom>
              Total Entries
            </Typography>
            <Typography component="p" variant="h4">
              {stats.total_entries}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <Paper 
            sx={{ 
              p: 2, 
              display: 'flex', 
              flexDirection: 'column', 
              height: 140,
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <AnalyticsIcon 
              sx={{ 
                position: 'absolute',
                right: -20,
                bottom: -20,
                fontSize: 100,
                opacity: 0.1,
                transform: 'rotate(-10deg)'
              }} 
            />
            <Typography variant="h6" gutterBottom>
              Recent Analyses
            </Typography>
            <Typography component="p" variant="h4">
              {stats.recent_analyses}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <Paper 
            sx={{ 
              p: 2, 
              display: 'flex', 
              flexDirection: 'column', 
              height: 140,
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <RateReviewIcon 
              sx={{ 
                position: 'absolute',
                right: -20,
                bottom: -20,
                fontSize: 100,
                opacity: 0.1,
                transform: 'rotate(-10deg)'
              }} 
            />
            <Typography variant="h6" gutterBottom>
              Pending Reviews
            </Typography>
            <Typography component="p" variant="h4">
              {stats.pending_reviews}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6} lg={3}>
          <Paper 
            sx={{ 
              p: 2, 
              display: 'flex', 
              flexDirection: 'column', 
              height: 140,
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            <PeopleIcon 
              sx={{ 
                position: 'absolute',
                right: -20,
                bottom: -20,
                fontSize: 100,
                opacity: 0.1,
                transform: 'rotate(-10deg)'
              }} 
            />
            <Typography variant="h6" gutterBottom>
              Active Users
            </Typography>
            <Typography component="p" variant="h4">
              {stats.active_users}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;