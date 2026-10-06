import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Form from './Form';

describe('Form Component', () => {
    const mockOnSubmit = jest.fn();

    beforeEach(() => {
        render(<Form onSubmit={mockOnSubmit}>Test Form</Form>);
    });

    test('renders the form with children', () => {
        expect(screen.getByText('Test Form')).toBeInTheDocument();
    });

    test('calls onSubmit when the form is submitted', () => {
        fireEvent.submit(screen.getByRole('form'));
        expect(mockOnSubmit).toHaveBeenCalled();
    });
});