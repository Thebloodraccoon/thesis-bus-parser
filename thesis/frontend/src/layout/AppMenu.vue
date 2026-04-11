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
        label: 'Statistics & Docs',
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
            },
            {
                label: 'List of cities',
                icon: 'pi pi-building',
                to: '/city/list'
            }
        ]
    },
    {
        label: 'Admin panel',
        visible: isAdmin.value,
        items: [
            {
                label: 'Celery Tasks Management',
                icon: 'pi pi-clock',
                to: '/task'
            },
            {
                label: 'Users Management',
                icon: 'pi pi-users',
                to: '/users'
            }
        ]
    }
    // {
    //     visible: isAdmin.value,
    //     label: 'Sites Management',
    //     items: [
    //         {
    //             label: 'List of sites',
    //             icon: 'pi pi-sitemap',
    //             to: '/site/list'
    //         },
    //         {
    //             label: 'Create a Site',
    //             visible: isAdmin.value,
    //             icon: 'pi pi-plus-circle',
    //             to: '/site/create'
    //         }
    //     ]
    // },
    // {
    //     visible: isAdmin.value,
    //     label: '',
    //     items: [
    //
    //     ]
    // }
]);

watch(isAdmin, (newVal) => {
    const userManagementItem = model.value.find((item) => item.label === 'Admin panel');
    if (userManagementItem) {
        const taskItem = userManagementItem.items.find((item) => item.label === 'Celery Tasks Management');
        if (taskItem) {
            taskItem.visible = newVal;
        }

        const usersItem = userManagementItem.items.find((item) => item.label === 'Users Management');
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
