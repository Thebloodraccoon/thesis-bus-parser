import { ref } from 'vue';

export function usePagination() {
    const page = ref(1);
    const size = ref(20);
    const rowsPerPageOptions = ref([
        { label: '20', value: 20 },
        { label: '40', value: 40 },
        { label: '50', value: 50 },
        { label: '90', value: 90 }
    ]);

    const resetPagination = () => {
        page.value = 1;
        size.value = 20;
    };

    return {
        page,
        size,
        rowsPerPageOptions,
        resetPagination
    };
}

