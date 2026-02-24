import apiClient from '@/api/axios';

export const SiteService = {
    getAllSites() {
        return apiClient.get('/sites/');
    },

    getSiteById(id) {
        return apiClient.get(`/sites/${id}`);
    },

    createSite(data) {
        return apiClient.post('/sites/', data);
    },

    updateSite(id, data) {
        return apiClient.put(`/sites/${id}`, data);
    },

    deleteSite(id) {
        return apiClient.delete(`/sites/${id}`);
    }
};
