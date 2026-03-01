import { ref } from 'vue';

export function useSiteValidation(siteData) {
    const errors = ref({
        name: '',
        url: '',
    });

    const validateForm = () => {
        errors.value.name = siteData.value.name ? '' : 'The name is required';
        errors.value.url = siteData.value.url ? '' : 'URL required';
        return !errors.value.name && !errors.value.url;
    };

    return {
        errors,
        validateForm
    };
}
