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
        label: 'Статистика',
        items: [
            {
                label: 'Сегменты на одну дату',
                icon: 'pi pi-calendar',
                to: '/'
            },
            {
                label: 'Cегмент в диапазоне дат',
                icon: 'pi pi-arrows-v',
                to: '/route'
            }
        ]
    },
    {
        visible: isAdmin.value,
        items: [
            {
                label: 'Все Пользователи',
                icon: 'pi pi-users',
                to: '/users'
            }
        ]
    },
    {
        label: 'Управление агентами',
        items: [
            {
                label: 'Список агентов',
                icon: 'pi pi-sitemap',
                to: '/site/list'
            },
            {
                label: 'Создать Агента',
                visible: isAdmin.value,
                icon: 'pi pi-plus-circle',
                to: '/site/create'
            }
        ]
    },
    {
        items: [
            {
                label: 'Список Городов',
                icon: 'pi pi-building',
                to: '/city/list'
            }
        ]
    },
    {
        label: 'Celery Задачи',
        visible: isAdmin.value,
        items: [
            {
                label: 'Список Задач',
                icon: 'pi pi-clock',
                to: '/task'
            },
            {
                label: 'Статус Задач',
                icon: 'pi pi-chart-bar',
                to: '/task/progress'
            },
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
