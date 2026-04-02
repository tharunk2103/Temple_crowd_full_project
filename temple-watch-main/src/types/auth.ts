export type UserRole = 'operator' | 'admin' | null;

export interface AuthState {
  isAuthenticated: boolean;
  role: UserRole;
}

export type CrowdStatus = 'normal' | 'warning' | 'overcrowded';

export interface ZoneData {
  id: string;
  name: string;
  count: number;
  status: CrowdStatus;
}
