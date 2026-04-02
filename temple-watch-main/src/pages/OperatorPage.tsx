import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import OperatorDashboard from '@/components/operator/OperatorDashboard';

const OperatorPage: React.FC = () => {
  const { isAuthenticated, role } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated || role !== 'operator') {
      navigate('/');
    }
  }, [isAuthenticated, role, navigate]);

  if (!isAuthenticated || role !== 'operator') {
    return null;
  }

  return <OperatorDashboard />;
};

export default OperatorPage;
