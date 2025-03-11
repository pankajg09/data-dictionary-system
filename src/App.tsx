import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Components
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import Review from './pages/Review';
import DataDictionary from './pages/DataDictionary';

// Theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/analysis"
            element={
              <PrivateRoute>
                <Layout>
                  <Analysis />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/review"
            element={
              <PrivateRoute>
                <Layout>
                  <Review />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/dictionary"
            element={
              <PrivateRoute>
                <Layout>
                  <DataDictionary />
                </Layout>
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App; 