import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../utils/test-utils';
import Analysis from '../Analysis';
import api from '../../config/api';
import { AnalysisResult } from '../../types/api';

// Mock the API
jest.mock('../../config/api');

describe('Analysis Component', () => {
  const mockApiPost = api.post as jest.MockedFunction<typeof api.post>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders analysis page elements', () => {
    render(<Analysis />);
    
    expect(screen.getByText('Code Analysis')).toBeInTheDocument();
    expect(screen.getByText('Upload Code File')).toBeInTheDocument();
    expect(screen.getByText('Or paste your code:')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Analyze' })).toBeInTheDocument();
  });

  it('allows file upload with valid file type', () => {
    render(<Analysis />);
    
    const file = new File(['console.log("test")'], 'test.js', { type: 'text/javascript' });
    const fileInput = screen.getByLabelText('Upload Code File');
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    expect(screen.getByText(`Selected file: ${file.name}`)).toBeInTheDocument();
  });

  it('prevents upload of invalid file type', () => {
    render(<Analysis />);
    
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });
    const fileInput = screen.getByLabelText('Upload Code File');
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    expect(screen.getByText('Invalid file type. Please upload a Python or JavaScript/TypeScript file.')).toBeInTheDocument();
  });

  it('allows code analysis with pasted code', async () => {
    const mockAnalysisResult: AnalysisResult = {
      tables: [],
      relationships: [],
      code_snippets: []
    };

    mockApiPost.mockResolvedValue({
      data: mockAnalysisResult,
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {
        url: '/api/analysis/analyze',
        method: 'post'
      }
    });

    render(<Analysis />);
    
    const codeTextarea = screen.getByPlaceholderText('Paste your code here...');
    const analyzeButton = screen.getByRole('button', { name: 'Analyze' });

    fireEvent.change(codeTextarea, { target: { value: 'console.log("test")' } });
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalledWith(
        '/api/analysis/analyze', 
        expect.any(FormData), 
        expect.any(Object)
      );
    });
  });

  it('shows error when no code or file is provided', () => {
    render(<Analysis />);
    
    const analyzeButton = screen.getByRole('button', { name: 'Analyze' });
    fireEvent.click(analyzeButton);

    expect(screen.getByText('Please upload a file or enter code to analyze.')).toBeInTheDocument();
  });
}); 