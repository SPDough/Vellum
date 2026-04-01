import { createTheme, ThemeOptions } from '@mui/material/styles';

const colors = {
  background: {
    default: '#fafbff',
    paper: '#ffffff',
    sidebar: '#f7f5ff',
    hover: '#f2efff',
    selected: '#ece7ff',
  },
  text: {
    primary: '#1f2233',
    secondary: '#68657a',
    disabled: '#9b98a8',
    hint: '#7c7a87',
  },
  gray: {
    50: '#f8f7fd',
    100: '#f1eff8',
    200: '#e6e1f2',
    300: '#d8d1ea',
    400: '#beb6d6',
    500: '#9b98a8',
    600: '#7c7a87',
    700: '#5e5a6f',
    800: '#312d43',
    900: '#232037',
  },
  data: {
    primary: '#8b5cf6',
    secondary: '#a855f7',
    accent: '#c084fc',
    dark: '#6d28d9',
    light: '#ede9fe',
  },
  status: {
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',
    processing: '#8b5cf6',
  },
};

const typography = {
  fontFamily: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
  ].join(','),
  h1: { fontSize: '2.75rem', fontWeight: 700, lineHeight: 1.15, color: colors.text.primary },
  h2: { fontSize: '2.2rem', fontWeight: 700, lineHeight: 1.2, color: colors.text.primary },
  h3: { fontSize: '1.7rem', fontWeight: 600, lineHeight: 1.3, color: colors.text.primary },
  h4: { fontSize: '1.35rem', fontWeight: 600, lineHeight: 1.35, color: colors.text.primary },
  h5: { fontSize: '1.15rem', fontWeight: 600, lineHeight: 1.4, color: colors.text.primary },
  h6: { fontSize: '1rem', fontWeight: 600, lineHeight: 1.4, color: colors.text.primary },
  body1: { fontSize: '1rem', fontWeight: 400, lineHeight: 1.65, color: colors.text.primary },
  body2: { fontSize: '0.875rem', fontWeight: 400, lineHeight: 1.55, color: colors.text.secondary },
  caption: { fontSize: '0.75rem', fontWeight: 500, lineHeight: 1.4, color: colors.text.secondary },
};

const themeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: colors.data.primary,
      light: colors.data.accent,
      dark: colors.data.dark,
      contrastText: '#ffffff',
    },
    secondary: {
      main: colors.data.secondary,
      light: colors.data.light,
      dark: colors.data.dark,
      contrastText: '#ffffff',
    },
    background: {
      default: colors.background.default,
      paper: colors.background.paper,
    },
    text: {
      primary: colors.text.primary,
      secondary: colors.text.secondary,
      disabled: colors.text.disabled,
    },
    success: { main: colors.status.success, light: '#34d399', dark: '#047857' },
    warning: { main: colors.status.warning, light: '#fbbf24', dark: '#d97706' },
    error: { main: colors.status.error, light: '#f87171', dark: '#dc2626' },
    info: { main: colors.status.info, light: '#60a5fa', dark: '#1d4ed8' },
    grey: colors.gray,
  },
  typography,
  shape: { borderRadius: 10 },
  spacing: 8,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: { backgroundColor: colors.background.default, color: colors.text.primary },
        '*::-webkit-scrollbar': { width: '8px', height: '8px' },
        '*::-webkit-scrollbar-track': { backgroundColor: colors.gray[100] },
        '*::-webkit-scrollbar-thumb': { backgroundColor: colors.gray[400], borderRadius: '4px' },
        '*::-webkit-scrollbar-thumb:hover': { backgroundColor: colors.gray[500] },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: '10px',
          padding: '9px 18px',
        },
        contained: {
          boxShadow: '0 8px 20px rgba(139, 92, 246, 0.18)',
          '&:hover': { boxShadow: '0 10px 24px rgba(139, 92, 246, 0.22)' },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(15, 23, 42, 0.06)',
          border: `1px solid ${colors.gray[200]}`,
        },
        elevation1: { boxShadow: '0 1px 3px rgba(15, 23, 42, 0.06)' },
        elevation2: { boxShadow: '0 10px 24px rgba(15, 23, 42, 0.08)' },
        elevation3: { boxShadow: '0 16px 32px rgba(15, 23, 42, 0.1)' },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '14px',
          border: `1px solid ${colors.gray[200]}`,
          boxShadow: '0 10px 24px rgba(15, 23, 42, 0.04)',
          '&:hover': {
            borderColor: colors.gray[300],
            boxShadow: '0 16px 32px rgba(15, 23, 42, 0.08)',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(255,255,255,0.92)',
          color: colors.text.primary,
          boxShadow: '0 1px 3px rgba(15, 23, 42, 0.06)',
          borderBottom: `1px solid ${colors.gray[200]}`,
          backdropFilter: 'blur(12px)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: colors.background.sidebar,
          borderRight: `1px solid ${colors.gray[200]}`,
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: '10px',
          '&:hover': { backgroundColor: colors.background.hover },
          '&.Mui-selected': {
            backgroundColor: colors.background.selected,
            '&:hover': { backgroundColor: colors.background.selected },
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '10px',
            '& fieldset': { borderColor: colors.gray[300] },
            '&:hover fieldset': { borderColor: colors.gray[400] },
            '&.Mui-focused fieldset': { borderColor: colors.data.primary },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          fontSize: '0.75rem',
          fontWeight: 600,
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: { borderBottom: `1px solid ${colors.gray[200]}` },
        indicator: { backgroundColor: colors.data.primary, height: 3, borderRadius: 3 },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          color: colors.text.secondary,
          '&.Mui-selected': { color: colors.data.primary },
        },
      },
    },
  },
};

export const theme = createTheme(themeOptions);

declare module '@mui/material/styles' {
  interface Palette {
    data: {
      primary: string;
      secondary: string;
      accent: string;
      dark: string;
      light: string;
    };
    status: {
      success: string;
      warning: string;
      error: string;
      info: string;
      processing: string;
    };
  }

  interface PaletteOptions {
    data?: {
      primary?: string;
      secondary?: string;
      accent?: string;
      dark?: string;
      light?: string;
    };
    status?: {
      success?: string;
      warning?: string;
      error?: string;
      info?: string;
      processing?: string;
    };
  }

  interface TypeBackground {
    sidebar: string;
    hover: string;
    selected: string;
  }
}

export { colors };
export type { ThemeOptions };
