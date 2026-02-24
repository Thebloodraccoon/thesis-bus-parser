<script setup>
import { useLayout } from '@/layout/composables/layout';
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const { showSidebar } = useLayout();

const breadcrumbRoutes = ref([]);
const searchInput = ref(null);
const searchActive = ref(false);

function setBreadcrumbRoutes() {
    if (route.meta.breadcrumb) {
        breadcrumbRoutes.value = route.meta.breadcrumb;

        return;
    }

    breadcrumbRoutes.value = route.fullPath
        .split('/')
        .filter((item) => item !== '')
        .filter((item) => isNaN(Number(item)))
        .map((item) => item.charAt(0).toUpperCase() + item.slice(1));
}

function activateSearch() {
    searchActive.value = true;
    setTimeout(() => {
        searchInput.value.$el.focus();
    }, 100);
}
function deactivateSearch() {
    searchActive.value = false;
}

function onSidebarButtonClick() {
    showSidebar();
}

watch(
    route,
    () => {
        setBreadcrumbRoutes();
    },
    { immediate: true }
);
</script>

<template>
    <div class="layout-breadcrumb flex items-center relative h-12">
        <nav>
            <ol class="relative z-20">
                <template v-for="(breadcrumbRoute, i) in breadcrumbRoutes" :key="breadcrumbRoute">
                    <li>{{ breadcrumbRoute }}</li>
                    <li v-if="i !== breadcrumbRoutes.length - 1" class="layout-breadcrumb-chevron">/</li>
                </template>
            </ol>
        </nav>
        <ul class="breadcrumb-menu flex items-center justify-end lg:hidden absolute right-0 top-0 z-40 h-12 w-screen">
            <li class="w-full m-0 ml-4">
                <div class="breadcrumb-search flex justify-end" :class="{ 'breadcrumb-search-active': searchActive }">
                    <Button icon="pi pi-search" class="breadcrumb-searchbutton text-surface-500 dark:text-surface-400 flex-shrink-0" type="button" severity="secondary" text rounded @click="activateSearch"></Button>
                    <div class="search-input-wrapper">
                        <IconField>
                            <InputIcon class="pi pi-search" />
                            <InputText ref="searchInput" type="text" placeholder="Search" @blur="deactivateSearch" @keydown.escape="deactivateSearch" />
                        </IconField>
                    </div>
                </div>
            </li>
        </ul>
    </div>
</template>
