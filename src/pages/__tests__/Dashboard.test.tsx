import React from 'react';
import { render, screen } from '../../utils/test-utils';
import Dashboard from '../Dashboard';

describe('Dashboard Component', () => {
  it('renders dashboard title', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders four statistic cards', () => {
    render(<Dashboard />);
    
    const statCards = [
      'Total Entries',
      'Recent Analyses',
      'Pending Reviews',
      'Active Users'
    ];

    statCards.forEach(cardTitle => {
      const card = screen.getByText(cardTitle);
      expect(card).toBeInTheDocument();
    });
  });

  it('displays initial zero values for statistics', () => {
    render(<Dashboard />);
    
    const zeroValues = screen.getAllByText('0');
    expect(zeroValues).toHaveLength(4);
  });

  it('renders with correct layout and styling', () => {
    const { container } = render(<Dashboard />);
    
    const gridContainer = container.querySelector('[class*="MuiGrid-container"]');
    expect(gridContainer).toBeInTheDocument();

    const paperElements = screen.getAllByRole('presentation');
    expect(paperElements).toHaveLength(4);
  });
}); 