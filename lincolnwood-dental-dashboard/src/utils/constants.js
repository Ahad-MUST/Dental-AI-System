// Lincolnwood Family Dental Design System - Minimalist 2025 Standards
// Inspired by the clean, professional aesthetic of the Lincolnwood website

// Primary Color Palette - Clean, minimalist with medical professionalism
export const COLORS = {
  // Primary Background - Cool off-white for clean, spacious feel
  background: {
    primary: '#F8F9FA',
    secondary: '#FFFFFF',
    tertiary: '#ECECEC'
  },
  
  // Accent Color 1 - Gentle muted teal-blue for trust and calm
  accent: {
    50: '#F0F8F8',
    100: '#E1F1F2', 
    200: '#C3E3E5',
    300: '#A5D5D8',
    400: '#87C7CB',
    500: '#5BA4A7', // Primary accent color
    600: '#4A8A8D',
    700: '#3A6B6E',
    800: '#294C4E',
    900: '#192D2F'
  },
  
  // Text Colors - Professional hierarchy
  text: {
    primary: '#333333',   // Charcoal gray for headings
    secondary: '#555555', // Medium gray for body text
    tertiary: '#777777',  // Light gray for captions
    muted: '#999999'      // Very light gray for disabled text
  },
  
  // Neutral Grays - Clean, medical aesthetic
  neutral: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#ECECEC', // Secondary background
    300: '#DDDDDD', // Border color
    400: '#CCCCCC',
    500: '#AAAAAA',
    600: '#888888',
    700: '#666666',
    800: '#444444',
    900: '#222222'
  },
  
  // Status Colors - Subtle, professional
  success: {
    50: '#F0FDF4',
    100: '#DCFCE7',
    200: '#BBF7D0',
    300: '#86EFAC',
    400: '#4ADE80',
    500: '#22C55E',
    600: '#16A34A',
    700: '#15803D'
  },
  
  warning: {
    50: '#FFFBEB',
    100: '#FEF3C7',
    200: '#FDE68A',
    300: '#FCD34D',
    400: '#FBBF24',
    500: '#F59E0B',
    600: '#D97706'
  },
  
  error: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    200: '#FECACA',
    300: '#FCA5A5',
    400: '#F87171',
    500: '#EF4444',
    600: '#DC2626'
  }
};

// Typography System - Clean, readable hierarchy
export const TYPOGRAPHY = {
  fontFamily: {
    sans: ['Inter', 'Open Sans', '-apple-system', 'BlinkMacSystemFont', 'sans-serif']
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem'     // 48px
  },
  fontWeight: {
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700'
  },
  lineHeight: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75'
  }
};

// Spacing System - 16px base with 1.5x scaling
export const SPACING = {
  xs: '0.5rem',   // 8px
  sm: '0.75rem',  // 12px
  base: '1rem',   // 16px (base unit)
  lg: '1.5rem',   // 24px (1.5x base)
  xl: '2rem',     // 32px (2x base)
  '2xl': '2.5rem', // 40px
  '3xl': '3rem',  // 48px (3x base)
  '4xl': '4rem',  // 64px (4x base)
  '5xl': '6rem'   // 96px (6x base)
};

// Border Radius - Subtle, professional curves
export const RADIUS = {
  none: '0',
  sm: '0.25rem',  // 4px - buttons, inputs
  md: '0.5rem',   // 8px - cards
  lg: '0.75rem',  // 12px - larger cards
  xl: '1rem',     // 16px - modals
  full: '9999px'  // pills, badges
};

// Shadows - Subtle depth for clean aesthetics
export const SHADOWS = {
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 2px 4px 0 rgba(0, 0, 0, 0.1)',  // Primary card shadow
  lg: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  xl: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
};

// Animation - Smooth, professional transitions
export const ANIMATIONS = {
  duration: {
    fast: '150ms',
    normal: '200ms', // Primary duration
    slow: '300ms'
  },
  easing: {
    default: 'cubic-bezier(0.4, 0, 0.2, 1)',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    inOut: 'cubic-bezier(0.4, 0, 0.2, 1)'
  }
};

// Chart Colors - Harmonious with accent palette
export const CHART_COLORS = [
  COLORS.accent[500],    // Primary teal-blue
  COLORS.accent[300],    // Light teal-blue
  COLORS.success[500],   // Success green
  COLORS.warning[500],   // Warning orange
  COLORS.neutral[500],   // Neutral gray
  COLORS.accent[700]     // Dark teal-blue
];

// Component Specifications
export const COMPONENTS = {
  button: {
    height: {
      sm: '2rem',    // 32px
      md: '2.5rem',  // 40px - touch-friendly
      lg: '3rem'     // 48px
    },
    padding: {
      sm: '0.5rem 1rem',
      md: '0.75rem 1.5rem',
      lg: '1rem 2rem'
    }
  },
  card: {
    padding: {
      sm: '1rem',
      md: '1.5rem',
      lg: '2rem'
    },
    radius: RADIUS.md,
    shadow: SHADOWS.md
  },
  input: {
    height: '2.5rem', // 40px - touch-friendly
    padding: '0.75rem',
    borderColor: COLORS.neutral[300],
    focusColor: COLORS.accent[500]
  }
};

// Breakpoints for responsive design
export const BREAKPOINTS = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px'
};

// Chart Configuration
export const CHART_CONFIG = {
  height: {
    small: 250,
    default: 300,
    large: 400
  },
  margins: {
    top: 20,
    right: 30,
    bottom: 20,
    left: 20
  }
};