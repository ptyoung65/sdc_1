import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { User, AuthState } from '@/types'

interface AuthStore extends AuthState {
  // Actions
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (data: {
    username: string
    email: string
    password: string
    confirmPassword: string
    terms: boolean
  }) => Promise<void>
  updateProfile: (data: Partial<User>) => Promise<void>
  refreshToken: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,

      // Actions
      login: async (email: string, password: string) => {
        try {
          set({ isLoading: true })

          // TODO: Replace with actual API call
          // const response = await authApi.login({ email, password })

          // Mock API call for development
          await new Promise(resolve => setTimeout(resolve, 1000))

          if (email === 'demo@sdc.com' && password === 'demo123') {
            const mockUser: User = {
              id: 'user-1',
              username: 'demo_user',
              email: 'demo@sdc.com',
              displayName: '데모 사용자',
              avatar: '',
              role: 'USER' as any,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
            }

            set({
              user: mockUser,
              isAuthenticated: true,
              isLoading: false,
            })

            // Store token in localStorage (mock)
            localStorage.setItem('sdc_access_token', 'mock-jwt-token')
          } else {
            throw new Error('잘못된 이메일 또는 비밀번호입니다.')
          }
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '로그인 중 오류가 발생했습니다.',
            isLoading: false,
            isAuthenticated: false,
            user: null,
          })
          throw error
        }
      },

      logout: () => {
        // Clear tokens
        localStorage.removeItem('sdc_access_token')
        localStorage.removeItem('sdc_refresh_token')
        
        // Clear user state
        set({
          user: null,
          isAuthenticated: false,
        } as Partial<AuthStore>)
      },

      register: async (data) => {
        try {
          set({ isLoading: true })

          // Validate passwords match
          if (data.password !== data.confirmPassword) {
            throw new Error('비밀번호가 일치하지 않습니다.')
          }

          if (!data.terms) {
            throw new Error('이용약관에 동의해야 합니다.')
          }

          // TODO: Replace with actual API call
          // const response = await authApi.register(data)

          // Mock API call
          await new Promise(resolve => setTimeout(resolve, 1500))

          const mockUser: User = {
            id: 'user-' + Date.now(),
            username: data.username,
            email: data.email,
            displayName: data.username,
            avatar: '',
            role: 'USER' as any,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }

          set({
            user: mockUser,
            isAuthenticated: true,
            isLoading: false,
          })

          // Store mock token
          localStorage.setItem('sdc_access_token', 'mock-jwt-token')
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '회원가입 중 오류가 발생했습니다.',
            isLoading: false,
          })
          throw error
        }
      },

      updateProfile: async (data) => {
        try {
          set({ isLoading: true })

          const currentUser = get().user
          if (!currentUser) {
            throw new Error('로그인이 필요합니다.')
          }

          // TODO: Replace with actual API call
          // const response = await authApi.updateProfile(data)

          // Mock API call
          await new Promise(resolve => setTimeout(resolve, 800))

          const updatedUser: User = {
            ...currentUser,
            ...data,
            updatedAt: new Date().toISOString(),
          }

          set({
            user: updatedUser,
            isLoading: false,
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '프로필 업데이트 중 오류가 발생했습니다.',
            isLoading: false,
          })
          throw error
        }
      },

      refreshToken: async () => {
        try {
          const refreshToken = localStorage.getItem('sdc_refresh_token')
          if (!refreshToken) {
            throw new Error('Refresh token not found')
          }

          // TODO: Replace with actual API call
          // const response = await authApi.refreshToken(refreshToken)

          // Mock refresh
          localStorage.setItem('sdc_access_token', 'new-mock-jwt-token')
        } catch (error) {
          // If refresh fails, logout user
          get().logout()
          throw error
        }
      },

      clearError: () => {
        const state = get()
        delete (state as any).error
        set(state)
      },
    }),
    {
      name: 'sdc-auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)