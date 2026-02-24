import { ref } from 'vue';

export function useSiteValidation(siteData) {
    const errors = ref({
        name: '',
        url: '',
        api_key: '',
        depth: 0,
        threads: 0
    });

    const validateForm = () => {
        errors.value.name = siteData.value.name ? '' : 'Название обязательно';
        errors.value.url = siteData.value.url ? '' : 'URL обязателен';
        errors.value.api_key = siteData.value.api_key ? '' : 'API ключ обязателен';

        if (siteData.value.depth === null || siteData.value.depth <= 0) {
            errors.value.depth = 'Значение глубины должно быть больше 0';
        } else {
            errors.value.depth = '';
        }

        if (siteData.value.threads === null || siteData.value.threads <= 0) {
            errors.value.threads = 'Значение потоков должно быть больше 0';
        } else {
            errors.value.threads = '';
        }

        return !errors.value.name && !errors.value.url && !errors.value.api_key &&
               !errors.value.depth && !errors.value.threads;
    };

    return {
        errors,
        validateForm
    };
}
