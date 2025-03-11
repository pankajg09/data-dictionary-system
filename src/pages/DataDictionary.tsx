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
} from '@mui/material';
import {
  Edit as EditIcon,
  History as HistoryIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import type { DataDictionaryEntry, HistoryEntry } from '../types/api';
import api from '../config/api';

const DataDictionary: React.FC = () => {
  const [entries, setEntries] = useState<DataDictionaryEntry[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEntry, setSelectedEntry] = useState<DataDictionaryEntry | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    try {
      const response = await api.get<DataDictionaryEntry[]>('/api/dictionary/entries');
      setEntries(response.data);
    } catch (error) {
      console.error('Error fetching dictionary entries:', error);
      setError('Failed to load dictionary entries');
    }
  };

  const handleEdit = (entry: DataDictionaryEntry) => {
    setSelectedEntry({ ...entry });
    setEditDialogOpen(true);
  };

  const handleSave = async () => {
    if (!selectedEntry) return;

    try {
      if (selectedEntry.id) {
        await api.put<DataDictionaryEntry>(`/api/dictionary/entries/${selectedEntry.id}`, selectedEntry);
      } else {
        await api.post<DataDictionaryEntry>('/api/dictionary/entries', selectedEntry);
      }
      await fetchEntries();
      setEditDialogOpen(false);
      setSelectedEntry(null);
    } catch (error) {
      console.error('Error saving entry:', error);
      setError('Failed to save entry');
    }
  };

  const handleViewHistory = async (entryId: string) => {
    try {
      const response = await api.get<HistoryEntry[]>(`/api/dictionary/history/${entryId}`);
      setHistory(response.data);
      setHistoryDialogOpen(true);
    } catch (error) {
      console.error('Error fetching entry history:', error);
      setError('Failed to load history');
    }
  };

  const filteredEntries = entries.filter((entry) =>
    Object.values(entry).some((value) =>
      String(value).toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Data Dictionary
      </Typography>

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
          onChange={(e) => setSearchTerm(e.target.value)}
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
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredEntries.map((entry) => (
              <TableRow key={entry.id}>
                <TableCell>{entry.table_name}</TableCell>
                <TableCell>{entry.column_name}</TableCell>
                <TableCell>{entry.data_type}</TableCell>
                <TableCell>{entry.description}</TableCell>
                <TableCell>
                  <IconButton onClick={() => handleEdit(entry)} size="small">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleViewHistory(entry.id)} size="small">
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
          />
          <TextField
            fullWidth
            label="Column Name"
            value={selectedEntry?.column_name || ''}
            onChange={(e) => setSelectedEntry(prev => prev ? { ...prev, column_name: e.target.value } : null)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Data Type"
            value={selectedEntry?.data_type || ''}
            onChange={(e) => setSelectedEntry(prev => prev ? { ...prev, data_type: e.target.value } : null)}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Description"
            value={selectedEntry?.description || ''}
            onChange={(e) => setSelectedEntry(prev => prev ? { ...prev, description: e.target.value } : null)}
            margin="normal"
            multiline
            rows={4}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)} startIcon={<CancelIcon />}>
            Cancel
          </Button>
          <Button onClick={handleSave} variant="contained" startIcon={<SaveIcon />}>
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