import React from 'react';
import { render, screen, fireEvent } from '../../setup/test-utils';
import { PasswordInput } from '../../../src/components/ui/password-input';

describe('PasswordInput Component', () => {
  it('renders correctly', () => {
    render(<PasswordInput placeholder="Enter password" />);
    const input = screen.getByPlaceholderText('Enter password');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('type', 'password');
  });

  it('toggles password visibility when the eye button is clicked', () => {
    render(<PasswordInput placeholder="Enter password" />);
    const input = screen.getByPlaceholderText('Enter password');
    const button = screen.getByRole('button', { name: /show password/i });

    expect(input).toHaveAttribute('type', 'password');

    // Click to show password
    fireEvent.click(button);
    expect(input).toHaveAttribute('type', 'text');
    expect(button).toHaveAttribute('aria-label', 'Hide password');

    // Click to hide password
    fireEvent.click(button);
    expect(input).toHaveAttribute('type', 'password');
    expect(button).toHaveAttribute('aria-label', 'Show password');
  });

  it('passes other props correctly', () => {
    render(<PasswordInput id="my-password" data-testid="pwd-input" required disabled />);
    const inputById = screen.getByTestId('pwd-input');
    expect(inputById).toBeInTheDocument();
    expect(inputById).toBeRequired();
    expect(inputById).toBeDisabled();
  });
});
