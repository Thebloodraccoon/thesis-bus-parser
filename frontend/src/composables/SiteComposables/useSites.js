import { ref } from 'vue';
import { useToast } from 'primevue/usetoast';
import { SiteService } from '@/service/SiteService';

export function useSites() {
    const sites = ref([]);
    const site = ref(null);
    const loading = ref(false);
    const toast = useToast();

    async function fetchSites() {
        loading.value = true;
        try {
            const response = await SiteService.getAllSites();
            sites.value = response.data;
        } catch (error) {
            console.error('Error loading sites:', error);
            toast.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Failed to load site list',
                life: 3000
            });
        } finally {
            loading.value = false;
        }
    }

    async function fetchSite(id) {
        loading.value = true;
        try {
            const response = await SiteService.getSiteById(id);
            site.value = response.data;
        } catch (error) {
            console.error('Error loading site data:', error);
            toast.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Failed to load site data',
                life: 3000
            });
        } finally {
            loading.value = false;
        }
    }

    async function createSite(siteData) {
        loading.value = true;
        try {
            await SiteService.createSite(siteData);
            toast.add({
                severity: 'success',
                summary: 'Successfully',
                detail: 'Site added',
                life: 3000
            });
            await fetchSites();
        } catch (error) {
            console.error('Mistake when creating a website:', error);
            toast.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Unable to add site',
                life: 3000
            });
        } finally {
            loading.value = false;
        }
    }

    async function updateSite(id, siteData) {
        loading.value = true;
        try {
            await SiteService.updateSite(id, siteData);
            toast.add({
                severity: 'success',
                summary: 'Successfully',
                detail: 'The site data has been updated',
                life: 3000
            });
        } catch (error) {
            console.error('Error when updating the site:', error);
            toast.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Unable to update site data',
                life: 3000
            });
        } finally {
            loading.value = false;
        }
    }

    async function deleteSite(id) {
        loading.value = true;
        try {
            await SiteService.deleteSite(id);
            toast.add({
                severity: 'success',
                summary: 'Successfully',
                detail: 'Site deleted',
                life: 3000
            });
            await fetchSites(); // Обновляем список сайтов после удаления
        } catch (error) {
            console.error('Error when deleting a site:', error);
            toast.add({
                severity: 'error',
                summary: 'Error',
                detail: 'Failed to delete site',
                life: 3000
            });
        } finally {
            loading.value = false;
        }
    }

    return {
        sites,
        site,
        loading,
        fetchSites,
        fetchSite,
        createSite,
        updateSite,
        deleteSite
    };
}
