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
            console.error('Ошибка при загрузке сайтов:', error);
            toast.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: 'Не удалось загрузить список сайтов',
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
            console.error('Ошибка при загрузке данных сайта:', error);
            toast.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: 'Не удалось загрузить данные сайта',
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
                summary: 'Успешно',
                detail: 'Сайт добавлен',
                life: 3000
            });
            await fetchSites(); // Обновляем список сайтов после создания
        } catch (error) {
            console.error('Ошибка при создании сайта:', error);
            toast.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: 'Не удалось добавить сайт',
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
                summary: 'Успешно',
                detail: 'Данные сайта обновлены',
                life: 3000
            });
        } catch (error) {
            console.error('Ошибка при обновлении сайта:', error);
            toast.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: 'Не удалось обновить данные сайта',
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
                summary: 'Успешно',
                detail: 'Сайт удален',
                life: 3000
            });
            await fetchSites(); // Обновляем список сайтов после удаления
        } catch (error) {
            console.error('Ошибка при удалении сайта:', error);
            toast.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: 'Не удалось удалить сайт',
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
