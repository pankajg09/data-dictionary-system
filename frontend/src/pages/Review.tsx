import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  List,
  ListItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Rating,
  Box,
  Paper,
  Alert,
} from '@mui/material';
import type { Review as ReviewType, ReviewDetail } from '../types/api';
import api from '../config/api';

const Review: React.FC = () => {
  const [reviews, setReviews] = useState<ReviewType[]>([]);
  const [selectedReview, setSelectedReview] = useState<ReviewDetail | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [comment, setComment] = useState('');
  const [rating, setRating] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReviews();
  }, []);

  const fetchReviews = async () => {
    try {
      const response = await api.get<ReviewType[]>('/api/review/list');
      setReviews(response.data);
    } catch (error) {
      console.error('Error fetching reviews:', error);
      setError('Failed to load reviews');
    }
  };

  const handleReviewClick = async (reviewId: string) => {
    try {
      const response = await api.get<ReviewDetail>(`/api/review/${reviewId}`);
      setSelectedReview(response.data);
      setDialogOpen(true);
    } catch (error) {
      console.error('Error fetching review details:', error);
      setError('Failed to load review details');
    }
  };

  const handleSubmitReview = async () => {
    if (!selectedReview || !rating) return;

    try {
      await api.post(`/api/review/${selectedReview.id}/submit`, {
        comment,
        rating,
      });
      setDialogOpen(false);
      setComment('');
      setRating(null);
      fetchReviews();
    } catch (error) {
      console.error('Error submitting review:', error);
      setError('Failed to submit review');
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Code Reviews
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <List>
        {reviews.map((review) => (
          <ListItem
            key={review.id}
            button
            onClick={() => handleReviewClick(review.id)}
            component={Paper}
            sx={{ mb: 2, p: 2 }}
          >
            <ListItemText
              primary={`Review #${review.id}`}
              secondary={
                <>
                  <Typography component="span" variant="body2" color="text.primary">
                    Status: {review.status}
                  </Typography>
                  <br />
                  <Typography component="span" variant="body2">
                    Created: {new Date(review.created_at).toLocaleString()}
                  </Typography>
                </>
              }
            />
          </ListItem>
        ))}
      </List>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Review Details</DialogTitle>
        <DialogContent>
          {selectedReview && (
            <>
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Code Snippet
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                    {selectedReview.code_snippet}
                  </pre>
                </Paper>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Previous Comments
                </Typography>
                {selectedReview.comments.map((comment, index) => (
                  <Paper key={index} sx={{ p: 2, mb: 1 }}>
                    <Typography>{comment}</Typography>
                  </Paper>
                ))}
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Add Your Review
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Comment"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  sx={{ mb: 2 }}
                />
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography component="legend">Rating:</Typography>
                  <Rating
                    value={rating}
                    onChange={(_, newValue) => setRating(newValue)}
                  />
                </Box>
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitReview}
            variant="contained"
            disabled={!comment || !rating}
          >
            Submit Review
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Review; 