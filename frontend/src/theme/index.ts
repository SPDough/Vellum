import { createTheme, ThemeOptions } from '@mui/material/styles';

// Light purple data-focused color palette
const colors = {
  // Background colors (Light purple theme)
  background: {
    default: '#fefefe',
    paper: '#ffffff',
    sidebar: '#f8f7fd',
    hover: '#f3f2f9',
    selected: '#ebe9f7',
  },
  // Text colors
  text: {
    primary: '#2d2a3d',
    secondary: '#5e5a6f',
    disabled: '#9b98a8',
    hint: '#7c7a87',
  },
  // Purple-gray scale
  gray: {
    50: '#f8f7fd',
    100: '#f3f2f9',
    200: '#ebe9f7',
    300: '#ddd9f0',
    400: '#c7c1e3',
    500: '#9b98a8',
    600: '#7c7a87',
    700: '#5e5a6f',
    800: '#2d2a3d',
    900: '#252237',
  },
  // Data/Analytics themed colors (purple spectrum)
  data: {
    primary: '#8b5cf6', // Vibrant purple
    secondary: '#a855f7', // Light purple
    accent: '#c084fc', // Soft purple
    dark: '#6d28d9', // Deep purple
    light: '#ddd6fe', // Very light purple
  },
  // Status colors for data and workflows
  status: {
    success: '#10b981', // Green for success
    warning: '#f59e0b', // Amber for warnings
    error: '#ef4444', // Red for errors
    info: '#3b82f6', // Blue for info
    processing: '#8b5cf6', // Purple for processing
  },
};

const typography = {
  fontFamily: [
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
    '"Apple Color Emoji"',
    '"Segoe UI Emoji"',
    '"Segoe UI Symbol"',
  ].join(','),
  h1: {
    fontSize: '2.5rem',
    fontWeight: 700,
    lineHeight: 1.2,
    color: colors.text.primary,
  },
  h2: {
    fontSize: '2rem',
    fontWeight: 600,
    lineHeight: 1.3,
    color: colors.text.primary,
  },
  h3: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: 1.4,
    color: colors.text.primary,
  },
  h4: {
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.4,
    color: colors.text.primary,
  },
  h5: {
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.4,
    color: colors.text.primary,
  },
  h6: {
    fontSize: '1rem',
    fontWeight: 600,
    lineHeight: 1.4,
    color: colors.text.primary,
  },
  body1: {
    fontSize: '1rem',
    fontWeight: 400,
    lineHeight: 1.6,
    color: colors.text.primary,
  },
  body2: {
    fontSize: '0.875rem',
    fontWeight: 400,
    lineHeight: 1.5,
    color: colors.text.secondary,
  },
  caption: {
    fontSize: '0.75rem',
    fontWeight: 400,
    lineHeight: 1.4,
    color: colors.text.secondary,
  },
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
    success: {
      main: colors.status.success,
      light: '#34d399',
      dark: '#047857',
    },
    warning: {
      main: colors.status.warning,
      light: '#fbbf24',
      dark: '#d97706',
    },
    error: {
      main: colors.status.error,
      light: '#f87171',
      dark: '#dc2626',
    },
    info: {
      main: colors.status.info,
      light: '#60a5fa',
      dark: '#1d4ed8',
    },
    grey: colors.gray,
  },
  typography,
  shape: {
    borderRadius: 8,
  },
  spacing: 8,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: colors.background.default,
          color: colors.text.primary,
        },
        '*::-webkit-scrollbar': {
          width: '8px',
          height: '8px',
        },
        '*::-webkit-scrollbar-track': {
          backgroundColor: colors.gray[100],
        },
        '*::-webkit-scrollbar-thumb': {
          backgroundColor: colors.gray[400],
          borderRadius: '4px',
        },
        '*::-webkit-scrollbar-thumb:hover': {
          backgroundColor: colors.gray[500],
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          borderRadius: '6px',
          padding: '8px 16px',
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          border: `1px solid ${colors.gray[200]}`,
        },
        elevation1: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        },
        elevation2: {
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        },
        elevation3: {
          boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          border: `1px solid ${colors.gray[200]}`,
          '&:hover': {
            borderColor: colors.gray[300],
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: colors.background.paper,
          color: colors.text.primary,
          boxShadow: 'none',
          borderBottom: `1px solid ${colors.gray[200]}`,
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
    MuiListItem: {
      styleOverrides: {
        root: {
          borderRadius: '4px',
          margin: '2px 8px',
          '&:hover': {
            backgroundColor: colors.background.hover,
          },
          '&.Mui-selected': {
            backgroundColor: colors.background.selected,
            '&:hover': {
              backgroundColor: colors.background.selected,
            },
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: '4px',
          '&:hover': {
            backgroundColor: colors.background.hover,
          },
          '&.Mui-selected': {
            backgroundColor: colors.background.selected,
            '&:hover': {
              backgroundColor: colors.background.selected,
            },
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '6px',
            '& fieldset': {
              borderColor: colors.gray[300],
            },
            '&:hover fieldset': {
              borderColor: colors.gray[400],
            },
            '&.Mui-focused fieldset': {
              borderColor: colors.data.primary,
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          fontSize: '0.75rem',
          fontWeight: 500,
        },
        filled: {
          backgroundColor: colors.gray[100],
          color: colors.text.primary,
          '&:hover': {
            backgroundColor: colors.gray[200],
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${colors.gray[200]}`,
        },
        indicator: {
          backgroundColor: colors.data.primary,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          color: colors.text.secondary,
          '&.Mui-selected': {
            color: colors.data.primary,
          },
        },
      },
    },
  },
};

export const theme = createTheme(themeOptions);

// Custom theme extensions
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