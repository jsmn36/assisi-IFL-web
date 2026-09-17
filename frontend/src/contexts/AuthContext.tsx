import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { supabase } from '@/lib/supabase';
import type { User, Session } from '@supabase/supabase-js';

export interface AuthUser {
  id: string;
  email: string;
  role: string;
  username?: string;
  first_name?: string | null;
  last_name?: string | null;
}

export interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUserProfile = async (authUser: User) => {
    try {
      // In the future, you might want to fetch additional role/profile data from a 'profiles' table
      // For now, we'll assign a default 'student' role if they log in
      
      // Try to get profile from database
      const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', authUser.id)
        .single();

      setUser({
        id: authUser.id,
        email: authUser.email || '',
        role: profile?.role || 'student', // Default role
        username: profile?.username || authUser.email?.split('@')[0],
        first_name: profile?.first_name,
        last_name: profile?.last_name,
      });
    } catch (err) {
      console.error('Error fetching user profile:', err);
      // Fallback user
      setUser({
        id: authUser.id,
        email: authUser.email || '',
        role: 'student',
      });
    }
  };

  useEffect(() => {
    // Check active sessions and sets the user
    const initializeAuth = async () => {
      try {
        const mockUserStr = localStorage.getItem('mock_user');
        if (mockUserStr) {
          const mockUser = JSON.parse(mockUserStr);
          setUser(mockUser);
          setIsLoading(false);
          return;
        }

        const { data: { session }, error } = await supabase.auth.getSession();
        if (error) throw error;
        
        setSession(session);
        if (session?.user) {
          await fetchUserProfile(session.user);
        } else {
          setUser(null);
        }
      } catch (err) {
        console.error('Error fetching session:', err);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();

    // Listen for changes on auth state (log in, log out, etc.)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, newSession) => {
        setSession(newSession);
        if (newSession?.user) {
          await fetchUserProfile(newSession.user);
        } else {
          setUser(null);
        }
        setIsLoading(false);
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);


  const login = async (email: string, password: string) => {
    setIsLoading(true);

    // Mock Login for Super Admin
    if (email === 'admin@assisi.edu' && password === 'adminpass') {
      const mockUser = {
        id: 'super_admin_1',
        email: 'admin@assisi.edu',
        role: 'admin',
        username: 'Super Admin',
        first_name: 'Platform',
      };
      setUser(mockUser);
      localStorage.setItem('mock_user', JSON.stringify(mockUser));
      setIsLoading(false);
      return;
    }

    // Mock Login for Branches
    const { mockBranches } = await import('@/lib/mockData');
    const branch = mockBranches.find(b => b.username === email || b.name === email);
    if (branch && branch.password === password) {
      const mockUser = {
        id: `branch_${branch.id}`,
        email: `${branch.username}@assisi.edu`,
        role: 'manager',
        username: branch.username,
        first_name: branch.name,
      };
      setUser(mockUser);
      localStorage.setItem('mock_user', JSON.stringify(mockUser));
      setIsLoading(false);
      return;
    }

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    
    if (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const logout = async () => {
    setIsLoading(true);
    localStorage.removeItem('mock_user');
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
    setIsLoading(false);
  };

  const hasRole = (...roles: string[]): boolean => {
    if (!user) return false;
    const upperUserRole = user.role.toUpperCase();
    return roles.map((r) => r.toUpperCase()).includes(upperUserRole);
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    hasRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
