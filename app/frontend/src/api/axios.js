import axios from 'axios';
import router from '@/router';
import { API_BASE_URL } from '@/config';
import { AuthService } from '@/service/AuthService';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    },
    withCredentials: true
});

apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

let isRefreshing = false;

apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) return Promise.reject(error);
            isRefreshing = true;

            try {
                console.log('Attempting to upgrade the token...');
                await AuthService.refreshToken();
                originalRequest._retry = true;
                return apiClient(originalRequest);
            } catch (refreshError) {
                console.error('Error when updating the token:', refreshError);
                localStorage.removeItem('access_token');
                await router.push('/auth/login');
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }
        return Promise.reject(error);
    }
);

export default apiClient;
