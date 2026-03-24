<script setup>
import { useLayout } from '@/layout/composables/layout';
import { useRouter } from 'vue-router';

const router = useRouter();
const { isDarkTheme } = useLayout();

function logo() {
    return isDarkTheme.value ? 'light' : 'dark';
}

function navigateToDashboard() {
    router.push('/');
}
</script>

<template>
    <div :class="'exception-body min-h-screen ' + (isDarkTheme ? 'layout-dark' : 'layout-light')" style="background: var(--surface-ground)">
        <div
            class="exception-container min-h-screen flex items-center justify-center flex-col bg-auto md:bg-contain bg-no-repeat"
            style="box-sizing: border-box; background: var(--exception-pages-image); background-repeat: no-repeat; background-size: contain"
        >
            <div class="exception-panel text-center flex items-center justify-center flex-col" style="margin-top: -200px; box-sizing: border-box">
                <h1 class="text-blue-500 mb-0" style="font-size: 140px; font-weight: 900; text-shadow: 0px 0px 50px rgba(#0f8bfd, 0.2)">404</h1>
                <h3 class="text-blue-700" style="font-size: 80px; font-weight: 900; margin-top: -90px; margin-bottom: 50px">not found</h3>
                <p class="text-3xl" style="max-width: 320px">The page that you are looking for does not exist</p>
                <Button type="button" label="Go back to home" style="margin-top: 50px" @click="navigateToDashboard"></Button>
            </div>
            <div class="exception-footer absolute items-center flex" style="bottom: 60px">
                <img :src="`/layout/images/logo/logo-${logo()}.png`" class="exception-logo" style="width: 34px" />
                <img :src="`/layout/images/logo/appname-${logo()}.png`" class="exception-appname ml-4" style="width: 72px" />
            </div>
        </div>
    </div>
</template>
