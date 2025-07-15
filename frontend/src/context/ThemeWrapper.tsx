import { ReactNode, createContext, useMemo, useState, useEffect } from 'react';
import { NeedleThemeProvider, useMediaQuery } from '@neo4j-ndl/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
export const ThemeWrapperContext = createContext({
  toggleColorMode: () => {},
  colorMode: localStorage.getItem('mode') as 'light' | 'dark',
});

// Wrapper component to filter out unsupported props
const FilteredThemeProvider = ({ children, theme, ...props }: any) => {
  // Only pass the theme prop to ThemeProvider
  return (
    <ThemeProvider theme={theme}>
      {children}
    </ThemeProvider>
  );
};
interface ThemeWrapperProps {
  children: ReactNode;
  className?: string; // Accept className but don't use it
  [key: string]: any; // Accept any other props but filter them out
}
const ThemeWrapper = ({ children, className, ...otherProps }: ThemeWrapperProps) => {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');
  const defaultMode = localStorage.getItem('mode') as 'light' | 'dark';
  const [mode, setMode] = useState<'light' | 'dark'>(defaultMode ?? (prefersDarkMode ? 'dark' : 'light'));
  const [usingPreferredMode, setUsingPreferredMode] = useState<boolean>(!defaultMode);

  useEffect(() => {
    // Ensure the body class is updated on initial load
    themeBodyInjection(mode);
  }, [mode]);
  // Create MUI theme that integrates with NDL theme
  const muiTheme = useMemo(() => {
    return createTheme({
      palette: {
        mode: mode,
        ...(mode === 'dark' 
          ? {
              // Dark mode colors using NDL CSS variables
              background: {
                default: 'rgb(var(--theme-palette-neutral-bg-default, 24 24 24))',
                paper: 'rgb(var(--theme-palette-neutral-bg-weak, 32 32 32))',
              },
              text: {
                primary: 'rgb(var(--theme-palette-neutral-text-default, 255 255 255))',
                secondary: 'rgb(var(--theme-palette-neutral-text-weak, 178 178 178))',
              },
              primary: {
                main: 'rgb(var(--theme-palette-primary-bg-strong, 81 166 177))',
                light: 'rgb(var(--theme-palette-primary-bg-weak, 65 133 142))',
                dark: 'rgb(var(--theme-palette-primary-bg-stronger, 45 101 108))',
              },
              divider: 'rgb(var(--theme-palette-neutral-border-weak, 64 64 64))',
              action: {
                hover: 'rgba(255, 255, 255, 0.08)',
                selected: 'rgba(255, 255, 255, 0.12)',
              },
            }
          : {
              // Light mode colors using NDL CSS variables  
              background: {
                default: 'rgb(var(--theme-palette-neutral-bg-default, 255 255 255))',
                paper: 'rgb(var(--theme-palette-neutral-bg-weak, 248 248 248))',
              },
              text: {
                primary: 'rgb(var(--theme-palette-neutral-text-default, 0 0 0))',
                secondary: 'rgb(var(--theme-palette-neutral-text-weak, 102 102 102))',
              },
              primary: {
                main: 'rgb(var(--theme-palette-primary-bg-strong, 1 64 99))',
                light: 'rgb(var(--theme-palette-primary-bg-weak, 43 131 186))',
                dark: 'rgb(var(--theme-palette-primary-bg-stronger, 0 43 69))',
              },
              divider: 'rgb(var(--theme-palette-neutral-border-weak, 228 228 228))',
              action: {
                hover: 'rgba(0, 0, 0, 0.04)',
                selected: 'rgba(0, 0, 0, 0.08)',
              },
            }),
      },
      components: {
        MuiPaper: {
          styleOverrides: {
            root: {
              backgroundImage: 'none', // Remove MUI default gradients
            },
          },
        },
        MuiSelect: {
          styleOverrides: {
            root: {
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: mode === 'dark' 
                  ? 'rgb(var(--theme-palette-neutral-border-weak, 64 64 64))' 
                  : 'rgb(var(--theme-palette-neutral-border-weak, 228 228 228))',
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: mode === 'dark' 
                  ? 'rgb(var(--theme-palette-primary-bg-weak, 65 133 142))' 
                  : 'rgb(var(--theme-palette-primary-bg-weak, 43 131 186))',
              },
            },
          },
        },
        MuiMenuItem: {
          styleOverrides: {
            root: {
              '&:hover': {
                backgroundColor: mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.08)' 
                  : 'rgba(0, 0, 0, 0.04)',
              },
            },
          },
        },
        MuiAlert: {
          styleOverrides: {
            root: {
              '&.MuiAlert-standardInfo': {
                backgroundColor: mode === 'dark' 
                  ? 'rgba(81, 166, 177, 0.15)' 
                  : 'rgba(1, 64, 99, 0.1)',
                color: mode === 'dark' 
                  ? 'rgb(var(--theme-palette-neutral-text-default, 255 255 255))' 
                  : 'rgb(var(--theme-palette-neutral-text-default, 0 0 0))',
              },
              '&.MuiAlert-standardSuccess': {
                backgroundColor: mode === 'dark' 
                  ? 'rgba(76, 175, 80, 0.15)' 
                  : 'rgba(76, 175, 80, 0.1)',
              },
              '&.MuiAlert-standardWarning': {
                backgroundColor: mode === 'dark' 
                  ? 'rgba(255, 152, 0, 0.15)' 
                  : 'rgba(255, 152, 0, 0.1)',
              },
            },
          },
        },
        MuiChip: {
          styleOverrides: {
            root: {
              '&.MuiChip-outlined': {
                borderColor: mode === 'dark' 
                  ? 'rgb(var(--theme-palette-neutral-border-weak, 64 64 64))' 
                  : 'rgb(var(--theme-palette-neutral-border-weak, 228 228 228))',
              },
            },
          },
        },
        MuiLinearProgress: {
          styleOverrides: {
            root: {
              backgroundColor: mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.1)' 
                : 'rgba(0, 0, 0, 0.1)',
            },
            bar: {
              backgroundColor: mode === 'dark' 
                ? 'rgb(var(--theme-palette-primary-bg-strong, 81 166 177))' 
                : 'rgb(var(--theme-palette-primary-bg-strong, 1 64 99))',
            },
          },
        },
        MuiFormControl: {
          styleOverrides: {
            root: {
              '& .MuiInputLabel-root': {
                color: mode === 'dark' 
                  ? 'rgb(var(--theme-palette-neutral-text-weak, 178 178 178))' 
                  : 'rgb(var(--theme-palette-neutral-text-weak, 102 102 102))',
              },
            },
          },
        },
        MuiButton: {
          styleOverrides: {
            root: {
              '&.MuiButton-outlined': {
                borderColor: mode === 'dark' 
                  ? 'rgb(var(--theme-palette-neutral-border-weak, 64 64 64))' 
                  : 'rgb(var(--theme-palette-neutral-border-weak, 228 228 228))',
                '&:hover': {
                  borderColor: mode === 'dark' 
                    ? 'rgb(var(--theme-palette-primary-bg-weak, 65 133 142))' 
                    : 'rgb(var(--theme-palette-primary-bg-weak, 43 131 186))',
                  backgroundColor: mode === 'dark' 
                    ? 'rgba(81, 166, 177, 0.08)' 
                    : 'rgba(1, 64, 99, 0.04)',
                },
              },
            },
          },
        },
      },
    });
  }, [mode]);

  const themeWrapperUtils = useMemo(
    () => ({
      colorMode: mode,
      toggleColorMode: () => {
        setMode((prevMode) => {
          const newMode = prevMode === 'light' ? 'dark' : 'light';
          setUsingPreferredMode(false);
          localStorage.setItem('mode', newMode);
          themeBodyInjection(newMode);
          return newMode;
        });
      },
    }),
    [mode]
  );
  const themeBodyInjection = (mode: string) => {
    if (mode === 'dark') {
      document.body.classList.add('ndl-theme-dark');
    } else {
      document.body.classList.remove('ndl-theme-dark');
    }
  };

  if (usingPreferredMode) {
    prefersDarkMode ? themeBodyInjection('light') : themeBodyInjection('dark');
  }
  return (
    <ThemeWrapperContext.Provider value={themeWrapperUtils}>
      <NeedleThemeProvider theme={mode as 'light' | 'dark' | undefined} wrapperProps={{ isWrappingChildren: false }}>
        <FilteredThemeProvider theme={muiTheme}>
          <CssBaseline />
          {children}
        </FilteredThemeProvider>
      </NeedleThemeProvider>
    </ThemeWrapperContext.Provider>
  );
};
export default ThemeWrapper;
