<script setup>
import { useLayout } from '@/layout/composables/layout';
import { ref } from 'vue';
import router from '@/router';
import AppBreadcrumb from './AppBreadcrumb.vue';
import AppSidebar from './AppSidebar.vue';
import { AuthService } from '@/service/AuthService';
import { useToast } from 'primevue/usetoast';

const { onMenuToggle, toggleDarkMode, layoutConfig } = useLayout();

const darkTheme = ref(layoutConfig.darkTheme);
const toast = useToast();


const onMenuButtonClick = () => {
    onMenuToggle();
};

const handleLogout = async () => {
    try {
        await AuthService.logout();
        localStorage.removeItem('access_token');
        toast.add({
            severity: 'success',
            summary: 'Success',
            detail: 'You have successfully logged out of your account',
            life: 3000
        });
        await router.push('/auth/login');
    } catch (err) {
        toast.add({
            severity: 'error',
            summary: 'Exit error',
            detail: 'Something went wrong when you signed out of your account',
            life: 3000
        });
    }
};
</script>

<template>
    <div class="layout-topbar">
        <div class="topbar-start">
            <Button ref="menubutton" type="button" class="topbar-menubutton p-trigger" @click="onMenuButtonClick">
                <i class="pi pi-bars"></i>
            </Button>

            <div class="topbar-breadcrumb">
                <AppBreadcrumb />
            </div>
        </div>

        <div class="layout-topbar-menu-section">
            <AppSidebar />
        </div>

        <div class="topbar-end mr-20 items-center flex gap-4">
            <div class="flex items-center gap-2 mr-10">
                <i class="pi pi-sun" />
                <InputSwitch v-model="darkTheme" @change="toggleDarkMode" />
                <i class="pi pi-moon" />
            </div>

            <a href="#" class="flex items-center hover:border-gray-700 duration-200" @click.prevent="handleLogout">
                <i class="pi pi-fw pi-sign-out mr-2"></i>
                <span>Logout</span>
            </a>
        </div>
    </div>
</template>
