import apiClient from '@/api/axios';

export const SiteService = {
    getAllSites() {
        return apiClient.get('/scraper/sites/');
    },

    getSiteById(id) {
        return apiClient.get(`/scraper/sites/${id}`);
    },

    createSite(data) {
        return apiClient.post('/scraper/sites/', data);
    },

    updateSite(id, data) {
        return apiClient.put(`/scraper/sites/${id}`, data);
    },

    deleteSite(id) {
        return apiClient.delete(`/scraper/sites/${id}`);
    }
};
