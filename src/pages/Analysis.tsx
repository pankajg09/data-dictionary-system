import React, { useState } from 'react';
import {
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Box,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import { CloudUpload as UploadIcon } from '@mui/icons-material';
import api from '../config/api';
import { AnalysisResult } from '../types/api';

const Analysis: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      const validExtensions = ['.py', '.js', '.ts', '.jsx', '.tsx'];
      const fileExtension = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
      
      if (validExtensions.includes(fileExtension)) {
        setFile(selectedFile);
        setError(null);
      } else {
        setError('Invalid file type. Please upload a Python or JavaScript/TypeScript file.');
        setFile(null);
      }
    }
  };

  const handleCodeChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCode(event.target.value);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!file && !code) {
      setError('Please upload a file or enter code to analyze.');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let formData = new FormData();
      if (file) {
        formData.append('file', file);
      } else {
        formData.append('code', code);
      }

      console.log('Sending analysis request to:', '/api/analysis/analyze');
      console.log('Request payload:', {
        fileProvided: !!file,
        codeLength: code.length
      });

      const response = await api.post<AnalysisResult>('/api/analysis/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000, // 30 second timeout
      });

      if (!response.data) {
        throw new Error('No data received from server');
      }

      setResult(response.data);
    } catch (err: any) {
      console.error('Full error object:', err);
      
      // More detailed error logging
      if (err.response) {
        // The request was made and the server responded with a status code
        console.error('Response error details:', {
          status: err.response.status,
          data: err.response.data,
          headers: err.response.headers
        });
        
        setError(`Server Error: ${err.response.status} - ${err.response.data?.message || 'Unknown error'}`);
      } else if (err.request) {
        // The request was made but no response was received
        console.error('No response received:', err.request);
        setError('No response from server. Please check your network connection.');
      } else {
        // Something happened in setting up the request
        console.error('Error setting up request:', err.message);
        setError(`Request setup error: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Code Analysis
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ mb: 3 }}>
              <input
                accept=".py,.js,.ts,.jsx,.tsx"
                style={{ display: 'none' }}
                id="file-upload"
                type="file"
                onChange={handleFileChange}
              />
              <label htmlFor="file-upload">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<UploadIcon />}
                >
                  Upload Code File
                </Button>
              </label>
              {file && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Selected file: {file.name}
                </Typography>
              )}
            </Box>

            <Typography variant="h6" gutterBottom>
              Or paste your code:
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={10}
              variant="outlined"
              placeholder="Paste your code here..."
              value={code}
              onChange={handleCodeChange}
            />

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}

            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Analyze'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {result && (
          <>
            <Grid item xs={12}>
              <Typography variant="h5" gutterBottom>
                Analysis Results
              </Typography>
            </Grid>

            {/* Tables and Fields */}
            {result.tables.map((table) => (
              <Grid item xs={12} md={6} key={table.name}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {table.name}
                    </Typography>
                    {table.fields.map((field, index) => (
                      <Box key={index} sx={{ mb: 1 }}>
                        <Typography variant="subtitle2">
                          {field.name}{' '}
                          <Chip
                            label={field.type}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {field.description}
                        </Typography>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            ))}

            {/* Relationships */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Relationships
                  </Typography>
                  {result.relationships.map((rel, index) => (
                    <Box key={index} sx={{ mb: 1 }}>
                      <Typography variant="body1">
                        {rel.from} → {rel.to} ({rel.type})
                      </Typography>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>

            {/* Code Snippets */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Code Snippets
                  </Typography>
                  {result.code_snippets.map((snippet, index) => (
                    <Box key={index} sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">
                        {snippet.file}:{snippet.line}
                      </Typography>
                      <Paper
                        sx={{
                          p: 2,
                          bgcolor: 'grey.100',
                          fontFamily: 'monospace',
                          mt: 1,
                        }}
                      >
                        <pre style={{ margin: 0 }}>{snippet.code}</pre>
                      </Paper>
                      <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                        {snippet.description}
                      </Typography>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>
    </Container>
  );
};

export default Analysis; 