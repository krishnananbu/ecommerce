// This file exports utility functions that can be used throughout the application.

// Example utility function
export const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US');
};

export const capitalizeFirstLetter = (string: string): string => {
    return string.charAt(0).toUpperCase() + string.slice(1);
};

// Add more utility functions as needed