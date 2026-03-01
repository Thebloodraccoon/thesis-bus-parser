<script setup>
import { ref, onMounted, watch } from 'vue';
import AppMenuItem from './AppMenuItem.vue';
import { useUserStore } from '@/stores/useUserStore';

const { user, isAdmin, fetchCurrentUser } = useUserStore();

onMounted(async () => {
    if (!user.value) {
        await fetchCurrentUser();
    }
});

const model = ref([
    {
        label: 'Statistics',
        items: [
            {
                label: 'Single-date segments',
                icon: 'pi pi-calendar',
                to: '/'
            },
            {
                label: 'Date range segment',
                icon: 'pi pi-arrows-v',
                to: '/route'
            }
        ]
    },
    {
        visible: isAdmin.value,
        items: [
            {
                label: 'All Users',
                icon: 'pi pi-users',
                to: '/users'
            }
        ]
    },
    {
        visible: isAdmin.value,
        label: 'Agents Management',
        items: [
            {
                label: 'List of agents',
                icon: 'pi pi-sitemap',
                to: '/site/list'
            },
            {
                label: 'Create an Agent',
                visible: isAdmin.value,
                icon: 'pi pi-plus-circle',
                to: '/site/create'
            }
        ]
    },
    {
        items: [
            {
                label: 'List of cities',
                icon: 'pi pi-building',
                to: '/city/list'
            }
        ]
    },
    {
        label: 'Celery Tasks Management',
        visible: isAdmin.value,
        items: [
            {
                label: 'Tasks List',
                icon: 'pi pi-clock',
                to: '/task'
            }
        ]
    }
]);

watch(isAdmin, (newVal) => {
    const userManagementItem = model.value.find((item) => item.label === 'User Management');
    if (userManagementItem) {
        const usersItem = userManagementItem.items.find((item) => item.label === 'Users');
        if (usersItem) {
            usersItem.visible = newVal;
        }
    }
});
</script>

<template>
    <ul class="layout-menu">
        <template v-for="(item, i) in model" :key="item">
            <AppMenuItem v-if="!item.separator" :item="item" root :index="i" />

            <li v-else class="menu-separator"></li>
        </template>
    </ul>
</template>
