import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from '../components/ui/button';
import { PasswordInput } from '../components/ui/password-input';
import { Label } from '../components/ui/label';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { apiClient, ApiError } from '../lib/api-client';

const ChangePasswordPage: React.FC = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    
    if (newPassword !== confirmPassword) {
      setError(t('auth.change_password.mismatch'));
      return;
    }
    
    setIsLoading(true);

    try {
      await apiClient.changePassword(currentPassword, newPassword);
      
      // After success, we need to update the local user state to remove the flag
      // We can accomplish this implicitly because the backend sets it to False,
      // but without a re-login, the JWT might still have it.
      // So, we just redirect to home and next token refresh/login will fix it.
      // Better yet, since we are doing it on client-side state:
      if (user) {
        user.requires_password_change = false;
      }
      
      navigate('/', { state: { message: t('auth.change_password.success') } });
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 dark:bg-gray-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            {t('auth.change_password.title')}
          </CardTitle>
          <CardDescription className="text-center">
            {t('auth.change_password.description')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current_password">{t('auth.change_password.current_password')}</Label>
              <PasswordInput
                id="current_password"
                value={currentPassword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCurrentPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="new_password">{t('auth.change_password.new_password')}</Label>
              <PasswordInput
                id="new_password"
                value={newPassword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="confirm_password">{t('auth.change_password.confirm_password')}</Label>
              <PasswordInput
                id="confirm_password"
                value={confirmPassword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            
            {error && (
              <p className="text-sm font-medium text-destructive text-center">
                {error}
              </p>
            )}
            
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? t('auth.change_password.submitting') : t('auth.change_password.submit')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default ChangePasswordPage;
