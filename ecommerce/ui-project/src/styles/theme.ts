// src/styles/theme.ts

export const theme = {
    colors: {
        primary: '#667eea',
        secondary: '#764ba2',
        background: '#ffffff',
        text: '#333333',
        border: '#e1e5e9',
    },
    fonts: {
        main: 'Inter, sans-serif',
    },
    spacing: (factor: number) => `${0.25 * factor}rem`,
    borderRadius: '12px',
};