<script setup>
import { useLayout } from '@/layout/composables/layout';
import { computed, onBeforeUnmount, onMounted } from 'vue';
import AppBreadCrumb from './AppBreadcrumb.vue';
import AppConfig from './AppConfig.vue';
import AppProfileMenu from './AppProfileMenu.vue';
import AppTopbar from './AppTopbar.vue';

const { layoutConfig, layoutState, watchSidebarActive, unbindOutsideClickListener } = useLayout();

onMounted(() => {
    watchSidebarActive();
});

onBeforeUnmount(() => {
    unbindOutsideClickListener();
});

const containerClass = computed(() => {
    return [
        {
            'layout-light': !layoutConfig.darkTheme,
            'layout-dark': layoutConfig.darkTheme,
            'layout-overlay': layoutConfig.menuMode === 'overlay',
            'layout-static': layoutConfig.menuMode === 'static',
            'layout-slim': layoutConfig.menuMode === 'slim',
            'layout-slim-plus': layoutConfig.menuMode === 'slim-plus',
            'layout-horizontal': layoutConfig.menuMode === 'horizontal',
            'layout-reveal': layoutConfig.menuMode === 'reveal',
            'layout-drawer': layoutConfig.menuMode === 'drawer',
            'layout-static-inactive': layoutState.staticMenuDesktopInactive && layoutConfig.menuMode === 'static',
            'layout-overlay-active': layoutState.overlayMenuActive,
            'layout-mobile-active': layoutState.staticMenuMobileActive,
            'layout-sidebar-active': layoutState.sidebarActive,
            'layout-sidebar-anchored': layoutState.anchored
        }
    ];
});
</script>

<template>
    <div class="layout-container" :class="containerClass">
        <div class="layout-content-wrapper">
            <AppTopbar />

            <div class="content-breadcrumb">
                <AppBreadCrumb />
            </div>

            <div class="layout-content">
                <router-view></router-view>
            </div>

            <div class="layout-mask"></div>
        </div>
        <AppProfileMenu />
        <AppConfig />

        <Toast></Toast>
    </div>
</template>

<style lang="scss"></style>
