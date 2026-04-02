import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { UserRole } from '@/types/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Building2, Shield, User } from 'lucide-react';

const API_BASE = 'http://localhost:5001';

const LoginPage: React.FC = () => {
  const [selectedRole, setSelectedRole] = useState<UserRole>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!selectedRole || !username || !password) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          password,
          role: selectedRole,
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        login(selectedRole);
        navigate(selectedRole === 'admin' ? '/admin' : '/operator');
      } else {
        setError(data.error || 'Invalid credentials');
      }
    } catch (err) {
      setError('Failed to connect to server. Please check if the backend is running.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary mb-4">
            <Building2 className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold text-foreground">Temple Crowd Management</h1>
          <p className="text-muted-foreground mt-2">Secure monitoring system</p>
        </div>

        {/* Login Card */}
        <div className="card-elevated p-8">
          <form onSubmit={handleLogin} className="space-y-6">
            {/* Role Selection */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Select Role</Label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedRole('operator')}
                  className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all ${
                    selectedRole === 'operator'
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <User className={`w-6 h-6 ${selectedRole === 'operator' ? 'text-primary' : 'text-muted-foreground'}`} />
                  <span className={`text-sm font-medium ${selectedRole === 'operator' ? 'text-primary' : 'text-foreground'}`}>
                    Operator
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedRole('admin')}
                  className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all ${
                    selectedRole === 'admin'
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <Shield className={`w-6 h-6 ${selectedRole === 'admin' ? 'text-primary' : 'text-muted-foreground'}`} />
                  <span className={`text-sm font-medium ${selectedRole === 'admin' ? 'text-primary' : 'text-foreground'}`}>
                    Admin
                  </span>
                </button>
              </div>
            </div>

            {/* Username Field */}
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="h-11"
              />
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Login Button */}
            <Button
              type="submit"
              className="w-full h-11 text-base font-medium"
              disabled={!selectedRole || !username || !password || loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          © 2026 Temple Crowd Management System
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
