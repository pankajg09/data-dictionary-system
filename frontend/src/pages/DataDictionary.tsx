import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  IconButton,
  Alert,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Edit as EditIcon,
  History as HistoryIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import type { DataDictionaryEntry, HistoryEntry } from '../types/api';
import api from '../config/api';
import { useAuth } from '../hooks/useAuth';
import useAuthStore from '../store/auth';

interface NewDictionaryEntry {
  table_name: string;
  column_name: string;
  data_type: string;
  description: string;
  created_by: number;
}

const DataDictionary: React.FC = () => {
  const { user } = useAuth();
  const [entries, setEntries] = useState<DataDictionaryEntry[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEntry, setSelectedEntry] = useState<DataDictionaryEntry | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { user: authUser } = useAuthStore();

  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    try {
      setLoading(true);
      const response = await api.get<DataDictionaryEntry[]>('/api/dictionary');
      console.log('API Response:', response.data);
      if (Array.isArray(response.data)) {
        setEntries(response.data);
      } else {
        console.error('Invalid response format:', response.data);
        setError('Invalid response format from server');
      }
    } catch (error) {
      console.error('Error fetching dictionary entries:', error);
      setError('Failed to load dictionary entries');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (entry: DataDictionaryEntry) => {
    setSelectedEntry({ ...entry });
    setEditDialogOpen(true);
  };

  const handleSave = async () => {
    if (!selectedEntry || !user) return;

    try {
      if (selectedEntry.id) {
        await api.put<DataDictionaryEntry>(
          `/api/dictionary/entries/${selectedEntry.id}`,
          selectedEntry,
          { params: { current_user_id: user.id } }
        );
      } else {
        await api.post<DataDictionaryEntry>(
          '/api/dictionary/entries',
          selectedEntry,
          { params: { current_user_id: user.id } }
        );
      }
      await fetchEntries();
      setEditDialogOpen(false);
      setSelectedEntry(null);
    } catch (error: any) {
      console.error('Error saving entry:', error);
      setError(error.response?.data?.detail || 'Failed to save entry');
    }
  };

  const handleViewHistory = async (entryId: string) => {
    try {
      const response = await api.get<HistoryEntry[]>(`/api/dictionary/entries/${entryId}/history`);
      setHistory(response.data);
      setHistoryDialogOpen(true);
    } catch (error) {
      console.error('Error fetching entry history:', error);
      setError('Failed to load history');
    }
  };

  const canEdit = (entry: DataDictionaryEntry) => {
    if (!user) return false;
    return user.id === entry.created_by;
  };

  const filteredEntries = entries.filter((entry) =>
    Object.values(entry).some((value) =>
      String(value).toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleAddEntry = async () => {
    if (!user) return;

    const newEntry: NewDictionaryEntry = {
      table_name: '',
      column_name: '',
      data_type: '',
      description: '',
      created_by: user.id,
    };

    try {
      await api.post('/api/dictionary', newEntry);
      fetchEntries();
    } catch (error) {
      console.error('Failed to add dictionary entry:', error);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography>Loading...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Data Dictionary
        </Typography>
        {user && (
          <Button
            variant="contained"
            color="primary"
            onClick={() => {
              setSelectedEntry({
                id: 0,
                table_name: '',
                column_name: '',
                data_type: '',
                description: '',
                created_by: user.id,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              });
              setEditDialogOpen(true);
            }}
          >
            Add New Entry
          </Button>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="Search"
          variant="outlined"
          value={searchTerm}
          onChange={handleSearch}
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Table Name</TableCell>
              <TableCell>Column Name</TableCell>
              <TableCell>Data Type</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredEntries.map((entry) => (
              <TableRow key={entry.id}>
                <TableCell>{entry.table_name}</TableCell>
                <TableCell>{entry.column_name}</TableCell>
                <TableCell>
                  <Chip label={entry.data_type} color="primary" variant="outlined" />
                </TableCell>
                <TableCell>{entry.description}</TableCell>
                <TableCell>
                  <Chip
                    label={entry.source || 'manual'}
                    color={entry.source === 'analysis' ? 'secondary' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Tooltip title={canEdit(entry) ? 'Edit' : 'No permission to edit'}>
                    <span>
                      <IconButton
                        onClick={() => handleEdit(entry)}
                        size="small"
                        disabled={!canEdit(entry)}
                      >
                        {canEdit(entry) ? <EditIcon /> : <LockIcon />}
                      </IconButton>
                    </span>
                  </Tooltip>
                  <IconButton onClick={() => handleViewHistory(entry.id.toString())} size="small">
                    <HistoryIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedEntry?.id ? 'Edit Entry' : 'New Entry'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Table Name"
            value={selectedEntry?.table_name || ''}
            onChange={(e) => setSelectedEntry(prev => prev ? { ...prev, table_name: e.target.value } : null)}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Column Name"
            value={selectedEntry?.column_name || ''}
            onChange={(e) => setSelectedEntry(prev => prev ? { ...prev, column_name: e.target.value } : null)}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Data Type"
            value={selectedEntry?.data_type || ''}
            onChange={(e) => setSelectedEntry(prev => prev ? { ...prev, data_type: e.target.value } : null)}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Description"
            value={selectedEntry?.description || ''}
            onChange={(e) => setSelectedEntry(prev => prev ? { ...prev, description: e.target.value } : null)}
            margin="normal"
            multiline
            rows={4}
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)} startIcon={<CancelIcon />}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
            disabled={!selectedEntry?.table_name || !selectedEntry?.column_name || !selectedEntry?.data_type}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Entry History</DialogTitle>
        <DialogContent>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>User</TableCell>
                <TableCell>Changes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {history.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell>{new Date(entry.timestamp).toLocaleString()}</TableCell>
                  <TableCell>{entry.user}</TableCell>
                  <TableCell>
                    <pre>{JSON.stringify(entry.changes, null, 2)}</pre>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DataDictionary; 