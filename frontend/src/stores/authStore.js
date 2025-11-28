import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      setAuth: (token, user) => {
        set({ token, user, isAuthenticated: true });
      },
      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
      },
      updateUser: (userData) => {
        set((state) => ({ user: { ...state.user, ...userData } }));
      },
      isApproved: () => {
        const user = get().user;
        return user?.approved === true;
      },
      hasRole: (role) => {
        const user = get().user;
        return user?.role === role;
      },
      hasAnyRole: (roles) => {
        const user = get().user;
        return roles.includes(user?.role);
      },
    }),
    { name: 'beacon-auth' }
  )
);
