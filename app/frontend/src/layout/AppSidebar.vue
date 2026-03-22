<script setup>
import { useLayout } from '@/layout/composables/layout';
import { useRouter } from 'vue-router';
import AppMenu from './AppMenu.vue';

const { layoutState, onSidebarToggle, onAnchorToggle, isDarkTheme } = useLayout();
const router = useRouter();

let timeout = null;

function logo() {
    return isDarkTheme.value ? 'light' : 'dark';
}

function onMouseEnter() {
    if (!layoutState.anchored) {
        if (timeout) {
            clearTimeout(timeout);
            timeout = null;
        }

        onSidebarToggle(true);
    }
}

function onMouseLeave() {
    if (!layoutState.anchored) {
        if (!timeout) {
            timeout = setTimeout(() => onSidebarToggle(false), 300);
        }
    }
}

function navigateToHome() {
    router.push('/');
}
</script>

<template>
    <div class="layout-sidebar" @mouseenter="onMouseEnter()" @mouseleave="onMouseLeave()">
        <div class="sidebar-header">
            <a @click="navigateToHome" class="app-logo" style="cursor: pointer">
                <div class="app-logo-small h-8">
                    <img class="!inline-block" :src="`/layout/images/logo/logo-${logo()}.png`" />
                </div>
                <div class="app-logo-normal">
                    <img class="h-8 !inline-block" :src="`/layout/images/logo/logo-${logo()}.png`" />
                    <img class="h-8 ml-4 !inline-block" :src="`/layout/images/logo/appname-${logo()}.png`" />
                </div>
            </a>
            <Button class="layout-sidebar-anchor z-20" type="button" @click="onAnchorToggle"></Button>
        </div>

        <div class="layout-menu-container">
            <AppMenu />
        </div>
    </div>
</template>

<style lang="scss" scoped></style>
