import apiClient from '@/api/axios';

export class AuthService {
    static async login(email, password) {
        try {
            const response = await apiClient.post('/auth/login', {email, password});

            if (response.status !== 200) {
                throw new Error('Authorization error');
            }

            localStorage.setItem('access_token', response.data.access_token);
            return response.data;
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'Authorization error';
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
                throw new Error('Failed to update the token');
            }
        } catch (error) {
            console.error('Token update error:', error);
            throw error;
        }
    }

    static async logout() {
        try {
            await apiClient.post('/auth/logout');
            localStorage.removeItem('access_token');
        } catch (error) {
            console.error('Exit error: ', error);
        }
    }

    static async verifyOtp(otp_code, temp_token) {
        try {
            const response = await apiClient.post('/auth/2fa/verify', {
                otp_code,
                temp_token,
            });

            if (response.status !== 200) {
                throw new Error('2FA Verification Error');
            }

            localStorage.setItem('access_token', response.data.access_token);
            return response.data;
        } catch (error) {
            const errorMessage = error.response?.data?.detail || '2FA Error';
            throw new Error(errorMessage);
        }
    }
}
