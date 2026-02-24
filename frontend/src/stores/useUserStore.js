import { ref, computed } from 'vue';
import apiClient from '@/api/axios';

const user = ref(null);
const isFetching = ref(false);

async function fetchCurrentUser() {
    if (isFetching.value || user.value) {
        return;
    }

    isFetching.value = true;
    try {
        const response = await apiClient.get('/user/current');
        user.value = response.data;
    } catch (error) {
        console.error('Error getting the current user: ', error);
        user.value = null;
    } finally {
        isFetching.value = false;
    }
}

const isAdmin = computed(() => {
    return user.value?.role === 'admin';
});

export function useUserStore() {
    return {
        user,
        isAdmin,
        fetchCurrentUser
    };
}
