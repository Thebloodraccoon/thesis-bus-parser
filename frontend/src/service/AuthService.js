import apiClient from '@/api/axios';

export class AuthService {
    static async login(email, password) {
        try {
            const response = await apiClient.post('/auth/login', {email, password});

            if (response.status !== 200) {
                throw new Error('Ошибка авторизации');
            }

            localStorage.setItem('access_token', response.data.access_token);
            return response.data;
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'Ошибка авторизации';
            throw new Error(errorMessage);
        }
    }

    static async refreshToken() {
        try {
            const response = await apiClient.post('/auth/refresh', {}, {withCredentials: true});

            if (response.status === 200) {
                localStorage.setItem('access_token', response.data.access_token);
                return response.data.access_token;
            } else {
                throw new Error('Не удалось обновить токен');
            }
        } catch (error) {
            console.error('Ошибка обновления токена:', error);
            throw error;
        }
    }

    static async logout() {
        try {
            await apiClient.post('/auth/logout');
            localStorage.removeItem('access_token');
        } catch (error) {
            console.error('Ошибка выхода:', error);
        }
    }

    static async verifyOtp(otp_code, temp_token) {
        try {
            const response = await apiClient.post('/auth/2fa/verify', {
                otp_code,
                temp_token,
            });

            if (response.status !== 200) {
                throw new Error('Ошибка подтверждения 2FA');
            }

            localStorage.setItem('access_token', response.data.access_token);
            return response.data;
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'Ошибка 2FA';
            throw new Error(errorMessage);
        }
    }
}
