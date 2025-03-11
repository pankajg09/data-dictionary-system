import { ComponentProps } from 'react';
import { ButtonProps } from '@mui/material';

declare module '@mui/material/Button' {
  interface ButtonPropsVariantOverrides {
    dashed: true;
  }
}

declare module '@mui/material/styles' {
  interface Theme {
    status: {
      danger: string;
    };
  }
  interface ThemeOptions {
    status?: {
      danger?: string;
    };
  }
}

declare module '@mui/material/styles' {
  interface Palette {
    neutral: Palette['primary'];
  }
  interface PaletteOptions {
    neutral?: PaletteOptions['primary'];
  }
}

export interface ExtendedButtonProps extends ButtonProps {
  component?: React.ElementType;
} 