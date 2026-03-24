import apiClient from '@/api/axios';

export class UserService {
    static async getUsers() {
        try {
            const response = await apiClient.get('/user/list');
            return response.data;
        } catch (error) {
            console.error('Error getting the list of users:', error);
            return [];
        }
    }

    static async inviteUser(email, role) {
        try {
            const response = await apiClient.post('/user/invite-user', { email, role });
            if (response.status !== 200 && response.status !== 201) {
                throw new Error('User creation error');
            }
            return response.data;
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'Unknown Error';
            throw new Error(errorMessage);
        }
    }

    static async deleteUser(userId) {
        try {
            const response = await apiClient.delete(`/user/${userId}`);
            if (response.status !== 200 && response.status !== 204) {
                throw new Error('Error when deleting a user');
            }
            return response.data;
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'Unknown Error';
            throw new Error(errorMessage);
        }
    }

    static async updateUserRole(userId, newRole) {
        try {
            const response = await apiClient.put(`/user/${userId}`, { role: newRole });
            if (response.status !== 200) {
                throw new Error('Error when changing user role');
            }
            return response.data;
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'Unknown Error';
            throw new Error(errorMessage);
        }
    }
}
