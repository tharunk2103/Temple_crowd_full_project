import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import AdminDashboard from '@/components/admin/AdminDashboard';

const AdminPage: React.FC = () => {
  const { isAuthenticated, role } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated || role !== 'admin') {
      navigate('/');
    }
  }, [isAuthenticated, role, navigate]);

  if (!isAuthenticated || role !== 'admin') {
    return null;
  }

  return <AdminDashboard />;
};

export default AdminPage;
