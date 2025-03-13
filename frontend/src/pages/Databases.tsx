import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Button,
  Collapse,
  IconButton,
  Tooltip,
  TextField,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Chip,
  MenuItem,
  TablePagination
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import InfoIcon from '@mui/icons-material/Info';
import CodeIcon from '@mui/icons-material/Code';
import StorageIcon from '@mui/icons-material/Storage';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PeopleIcon from '@mui/icons-material/People';
import api from '../config/api';
import { DataDictionaryEntry } from '../types/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      style={{ display: value === index ? 'block' : 'none', height: '100%' }}
      {...other}
    >
      {value === index && (
        <Box sx={{ height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface Column {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  description?: string;
}

interface TableInfo {
  name: string;
  columns: Column[];
  row_count: number;
}

interface Database {
  name: string;
  tables: TableInfo[];
}

interface SQLAnalysisResult {
  tables: SQLTable[];
  relationships: SQLRelationship[];
  type: string;
  model_used: string;
  documentation_summary: string;
}

interface SQLTable {
  name: string;
  fields: SQLField[];
  relationships: SQLRelationship[];
}

interface SQLField {
  name: string;
  type: string;
  description: string;
  constraints: string[];
}

interface SQLRelationship {
  type: string;
  from_table: string;
  from_fields: string[];
  to_table: string;
  to_fields: string[];
}

interface SQLAnalysisResponse {
  result: SQLAnalysisResult;
}

interface User {
  id: number;
  email: string;
  name: string;
  picture: string | null;
  role: string;
  google_id: string;
  first_login_at: string;
  last_login_at: string;
  login_count: number;
  created_at: string;
  updated_at: string;
}

interface TableData {
  data: Record<string, any>[];
  total: number;
  page: number;
  page_size: number;
}

const Databases: React.FC = (): JSX.Element => {
  const location = useLocation();
  const [databases, setDatabases] = useState<Database[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDb, setSelectedDb] = useState(0);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [tableData, setTableData] = useState<Record<string, any>[]>([]);
  const [totalRows, setTotalRows] = useState(0);
  const [tabValue, setTabValue] = useState(0);
  const [expandedTables, setExpandedTables] = useState<Record<string, boolean>>({});
  const [sqlCode, setSqlCode] = useState<string>('');
  const [sqlAnalysisResult, setSqlAnalysisResult] = useState<SQLAnalysisResult | null>(null);
  const [analyzingSql, setAnalyzingSql] = useState<boolean>(false);
  const [sqlAnalysisError, setSqlAnalysisError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'databases' | 'sqlAnalysis' | 'dataDictionary'>('databases');
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [sqlQueryResult, setSqlQueryResult] = useState<any | null>(null);
  const [executingSql, setExecutingSql] = useState<boolean>(false);
  const [sqlExecutionError, setSqlExecutionError] = useState<string | null>(null);
  const [dictionaryEntries, setDictionaryEntries] = useState<DataDictionaryEntry[]>([]);
  const [loadingDictionary, setLoadingDictionary] = useState<boolean>(false);
  const [dictionaryError, setDictionaryError] = useState<string | null>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const toggleTableExpand = (tableName: string) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }));
  };

  const fetchDatabases = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/databases');
      setDatabases(response.data as Database[]);
    } catch (err) {
      console.error('Error fetching databases:', err);
      setError('Failed to load databases. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const fetchDictionaryEntries = async () => {
    setLoadingDictionary(true);
    setDictionaryError(null);
    try {
      const response = await api.get<DataDictionaryEntry[]>('/api/dictionary/entries');
      setDictionaryEntries(response.data);
    } catch (err) {
      console.error('Error fetching dictionary entries:', err);
      setDictionaryError('Failed to load data dictionary entries. Please try again later.');
    } finally {
      setLoadingDictionary(false);
    }
  };

  useEffect(() => {
    fetchDatabases();
  }, []);

  useEffect(() => {
    if (viewMode === 'dataDictionary') {
      fetchDictionaryEntries();
    }
  }, [viewMode]);

  useEffect(() => {
    if (selectedDb >= 0 && databases[selectedDb] && databases[selectedDb].tables.length > 0) {
      setSelectedTable(databases[selectedDb].tables[0].name);
    }
  }, [selectedDb, databases]);

  useEffect(() => {
    if (selectedDb >= 0 && selectedTable) {
      fetchTableData();
    }
  }, [selectedDb, selectedTable, page, rowsPerPage]);

  const fetchTableData = async () => {
    if (!databases[selectedDb] || !selectedTable) return;

    try {
      setLoading(true);
      const response = await api.get<TableData>(`/api/databases/${databases[selectedDb].name}/tables/${selectedTable}`, {
        params: {
          page: page + 1,
          page_size: rowsPerPage
        }
      });
      setTableData(response.data.data);
      setTotalRows(response.data.total);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Error fetching table data');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const renderTableData = (table: TableInfo) => {
    const isExpanded = expandedTables[table.name] || false;

    return (
      <Box key={table.name} sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <IconButton 
            onClick={() => toggleTableExpand(table.name)}
            size="small"
          >
            {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
          <Typography variant="h6" component="div">
            {table.name}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }}>
            ({table.row_count} rows)
          </Typography>
        </Box>
        
        <Collapse in={isExpanded}>
          <TableContainer 
            component={Paper} 
            sx={{ 
              maxHeight: 400,
              '& .MuiTable-root': {
                borderCollapse: 'separate',
                borderSpacing: 0,
              },
              '& .MuiTableHead-root': {
                position: 'sticky',
                top: 0,
                backgroundColor: 'background.paper',
                zIndex: 1,
              }
            }}
          >
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  {table.columns.map((column) => (
                    <TableCell 
                      key={column.name}
                      sx={{
                        backgroundColor: 'background.paper',
                        fontWeight: 'bold'
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {column.name}
                        <Typography variant="caption" display="block" color="text.secondary">
                          {column.type}
                        </Typography>
                      </Box>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {tableData.map((row, rowIndex) => (
                  <TableRow key={rowIndex}>
                    {table.columns.map((column) => (
                      <TableCell key={column.name}>
                        {row[column.name] !== null && row[column.name] !== undefined
                          ? String(row[column.name])
                          : <span style={{ color: '#999' }}>NULL</span>}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Collapse>
      </Box>
    );
  };

  const handleSqlCodeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSqlCode(event.target.value);
  };

  const analyzeSql = async () => {
    if (!sqlCode.trim()) {
      setSqlAnalysisError('Please enter SQL code to analyze');
      return;
    }

    setAnalyzingSql(true);
    setSqlAnalysisError(null);
    setSqlAnalysisResult(null);

    try {
      const response = await api.post<SQLAnalysisResponse>('/api/databases/analyze-sql', {
        sql_code: sqlCode
      });
      setSqlAnalysisResult(response.data.result);
    } catch (err) {
      console.error('Error analyzing SQL:', err);
      setSqlAnalysisError('Failed to analyze SQL. Please check your SQL syntax and try again.');
    } finally {
      setAnalyzingSql(false);
    }
  };

  const executeSql = async () => {
    if (!sqlCode.trim()) {
      setSqlExecutionError('Please enter SQL code to execute');
      return;
    }

    if (!selectedDatabase) {
      setSqlExecutionError('Please select a database to execute the query on');
      return;
    }

    setExecutingSql(true);
    setSqlExecutionError(null);
    setSqlQueryResult(null);

    try {
      interface SqlQueryResult {
        columns: Array<{ name: string; type: string }>;
        rows: Array<Record<string, any>>;
        rowCount: number;
      }
      
      const response = await api.post(`/api/databases/${selectedDatabase}/execute-sql`, {
        sql_query: sqlCode
      });
      
      const queryResult = response.data as SqlQueryResult;
      setSqlQueryResult(queryResult);
    } catch (err: any) {
      console.error('Error executing SQL:', err);
      setSqlExecutionError(err.response?.data?.detail || 'Failed to execute SQL. Please check your SQL syntax and try again.');
    } finally {
      setExecutingSql(false);
    }
  };

  const renderSqlAnalysis = () => {
    return (
      <Box>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            SQL Code Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Enter SQL code (CREATE TABLE statements) to analyze and extract data dictionary information.
            You can also execute SQL queries on the sample databases.
          </Typography>
          
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={8}>
              <TextField
                label="SQL Code"
                multiline
                rows={8}
                value={sqlCode}
                onChange={handleSqlCodeChange}
                fullWidth
                variant="outlined"
                placeholder="CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL, ...);"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" gutterBottom>
                Actions
              </Typography>
              <Button
                variant="contained"
                onClick={analyzeSql}
                disabled={analyzingSql || !sqlCode.trim()}
                startIcon={<CodeIcon />}
                fullWidth
                sx={{ mb: 2 }}
              >
                Analyze SQL
              </Button>
              
              <Typography variant="subtitle2" gutterBottom>
                Execute Query
              </Typography>
              <TextField
                select
                label="Select Database"
                value={selectedDatabase}
                onChange={(e) => setSelectedDatabase(e.target.value)}
                fullWidth
                variant="outlined"
                sx={{ mb: 2 }}
              >
                {databases.map((db) => (
                  <MenuItem key={db.name} value={db.name}>
                    {db.name}
                  </MenuItem>
                ))}
              </TextField>
              
              <Button
                variant="contained"
                color="secondary"
                onClick={executeSql}
                disabled={executingSql || !sqlCode.trim() || !selectedDatabase}
                startIcon={<PlayArrowIcon />}
                fullWidth
              >
                Execute SQL
              </Button>
            </Grid>
          </Grid>
        </Box>

        {(analyzingSql || executingSql) && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {sqlAnalysisError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {sqlAnalysisError}
          </Alert>
        )}

        {sqlExecutionError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {sqlExecutionError}
          </Alert>
        )}

        {sqlQueryResult && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Query Results
            </Typography>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {sqlQueryResult.columns.map((column: any) => (
                      <TableCell key={column.name}>{column.name}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sqlQueryResult.rows.map((row: any, index: number) => (
                    <TableRow key={index}>
                      {sqlQueryResult.columns.map((column: any) => (
                        <TableCell key={column.name}>
                          {row[column.name] !== null && row[column.name] !== undefined
                            ? String(row[column.name])
                            : <span style={{ color: '#999' }}>NULL</span>}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {sqlQueryResult.rowCount} rows returned
            </Typography>
          </Box>
        )}

        {sqlAnalysisResult && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Analysis Results
            </Typography>
            
            {sqlAnalysisResult.tables.length === 0 ? (
              <Alert severity="info">
                No tables found in the SQL code.
              </Alert>
            ) : (
              <Grid container spacing={3}>
                {sqlAnalysisResult.tables.map((table) => (
                  <Grid item xs={12} key={table.name}>
                    <Card>
                      <CardHeader 
                        title={table.name} 
                        subheader={`${table.fields.length} columns`}
                        avatar={<StorageIcon />}
                      />
                      <Divider />
                      <CardContent>
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Column Name</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Constraints</TableCell>
                                <TableCell>Description</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {table.fields.map((field) => (
                                <TableRow key={field.name}>
                                  <TableCell>{field.name}</TableCell>
                                  <TableCell>{field.type}</TableCell>
                                  <TableCell>
                                    {field.constraints.map((constraint) => (
                                      <Chip 
                                        key={constraint} 
                                        label={constraint} 
                                        size="small" 
                                        sx={{ mr: 0.5, mb: 0.5 }} 
                                      />
                                    ))}
                                  </TableCell>
                                  <TableCell>{field.description}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}

                {sqlAnalysisResult.relationships.length > 0 && (
                  <Grid item xs={12}>
                    <Card>
                      <CardHeader 
                        title="Relationships" 
                        subheader={`${sqlAnalysisResult.relationships.length} relationships found`}
                      />
                      <Divider />
                      <CardContent>
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>From Table</TableCell>
                                <TableCell>From Column</TableCell>
                                <TableCell>To Table</TableCell>
                                <TableCell>To Column</TableCell>
                                <TableCell>Type</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {sqlAnalysisResult.relationships.map((rel, index) => (
                                <TableRow key={index}>
                                  <TableCell>{rel.from_table}</TableCell>
                                  <TableCell>{rel.from_fields.join(', ')}</TableCell>
                                  <TableCell>{rel.to_table}</TableCell>
                                  <TableCell>{rel.to_fields.join(', ')}</TableCell>
                                  <TableCell>{rel.type}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </CardContent>
                    </Card>
                  </Grid>
                )}
              </Grid>
            )}
          </Box>
        )}
      </Box>
    );
  };

  const renderDataDictionary = () => {
    if (loadingDictionary) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      );
    }

    if (dictionaryError) {
      return (
        <Alert severity="error" sx={{ mb: 3 }}>
          {dictionaryError}
        </Alert>
      );
    }

    if (dictionaryEntries.length === 0) {
      return (
        <Alert severity="info">
          No data dictionary entries found.
        </Alert>
      );
    }

    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Table Name</TableCell>
              <TableCell>Column Name</TableCell>
              <TableCell>Data Type</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Relationships</TableCell>
              <TableCell>Last Updated</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {dictionaryEntries.map((entry) => (
              <TableRow key={`${entry.table_name}-${entry.column_name}`}>
                <TableCell>{entry.table_name}</TableCell>
                <TableCell>{entry.column_name}</TableCell>
                <TableCell>
                  <Chip label={entry.data_type} color="primary" variant="outlined" size="small" />
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
                  {entry.relationships && Array.isArray(entry.relationships) && entry.relationships.map((rel, index) => (
                    <Chip
                      key={index}
                      label={rel}
                      color="info"
                      variant="outlined"
                      size="small"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </TableCell>
                <TableCell>
                  {entry.updated_at ? new Date(entry.updated_at).toLocaleString() : 'N/A'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (location.pathname !== '/databases') {
    return <></>;
  }

  return (
    <Box sx={{ 
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      <Box sx={{ 
        p: 2, 
        borderBottom: 1, 
        borderColor: 'divider',
        backgroundColor: 'background.paper',
        zIndex: 1
      }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5" component="h1">
            Databases
          </Typography>
          <Box>
            <Button
              variant={viewMode === 'databases' ? 'contained' : 'outlined'}
              onClick={() => setViewMode('databases')}
              sx={{ mr: 1 }}
            >
              View Databases
            </Button>
            <Button
              variant={viewMode === 'sqlAnalysis' ? 'contained' : 'outlined'}
              onClick={() => setViewMode('sqlAnalysis')}
              sx={{ mr: 1 }}
            >
              SQL Analysis
            </Button>
            <Button
              variant={viewMode === 'dataDictionary' ? 'contained' : 'outlined'}
              onClick={() => setViewMode('dataDictionary')}
            >
              Data Dictionary
            </Button>
          </Box>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mx: 2, mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ 
        flex: 1,
        overflow: 'auto',
        position: 'relative'
      }}>
        {loading && databases.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {viewMode === 'databases' && (
              <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', backgroundColor: 'background.paper' }}>
                  <Tabs 
                    value={selectedDb} 
                    onChange={(e, newValue) => setSelectedDb(newValue)}
                    variant="scrollable"
                    scrollButtons="auto"
                  >
                    {databases.map((db, index) => (
                      <Tab label={db.name} id={`database-tab-${index}`} key={db.name} />
                    ))}
                  </Tabs>
                </Box>
                
                <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
                  {databases.map((database, index) => (
                    <TabPanel value={selectedDb} index={index} key={database.name}>
                      {database.tables.length === 0 ? (
                        <Alert severity="info">
                          No tables found in this database.
                        </Alert>
                      ) : (
                        database.tables.map(table => renderTableData(table))
                      )}
                    </TabPanel>
                  ))}
                </Box>
              </Box>
            )}
            
            {viewMode === 'sqlAnalysis' && (
              <Box sx={{ p: 2 }}>
                {renderSqlAnalysis()}
              </Box>
            )}
            
            {viewMode === 'dataDictionary' && (
              <Box sx={{ p: 2 }}>
                {renderDataDictionary()}
              </Box>
            )}
          </>
        )}
      </Box>
    </Box>
  );
};

export default Databases; 