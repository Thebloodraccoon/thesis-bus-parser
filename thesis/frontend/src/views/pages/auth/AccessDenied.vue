<script setup>
import { useLayout } from '@/layout/composables/layout';
import { useRouter } from 'vue-router';

const { isDarkTheme } = useLayout();
const router = useRouter();

function logo() {
    return isDarkTheme.value ? 'light' : 'dark';
}

function goHome() {
    router.push('/');
}
</script>

<template>
    <div :class="'exception-body min-h-screen ' + (isDarkTheme ? 'layout-dark' : 'layout-light')" style="background: var(--surface-ground)">
        <div
            class="exception-container min-h-screen flex items-center justify-center flex-col bg-auto md:bg-contain bg-no-repeat"
            :style="{ background: 'var(--exception-pages-image)', backgroundRepeat: 'no-repeat', backgroundSize: 'contain', boxSizing: 'border-box' }"
        >
            <div class="exception-panel text-center flex items-center justify-center flex-col" style="margin-top: -200px; box-sizing: border-box">
                <h1 class="text-blue-500 mb-0" style="font-size: 140px; font-weight: 900; text-shadow: 0px 0px 50px rgba(#0f8bfd, 0.2)">ACCESS</h1>
                <h3 class="text-blue-700" style="font-size: 80px; font-weight: 900; margin-top: -90px; margin-bottom: 50px">denied</h3>
                <p class="text-3xl" style="max-width: 320px">You are not allowed to view this page.</p>
                <Button type="button" @click="goHome" style="margin-top: 50px">Go back to home</Button>
            </div>
            <div class="exception-footer absolute items-center flex" style="bottom: 60px">
                <img :src="`/layout/images/logo/logo-${logo()}.png`" class="exception-logo" style="width: 34px" />
                <img :src="`/layout/images/logo/appname-${logo()}.png`" class="exception-appname ml-4" style="width: 72px" />
            </div>
        </div>
    </div>
</template>
