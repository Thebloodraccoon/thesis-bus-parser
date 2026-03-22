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
                <h1 class="text-red-400 mb-0" style="font-size: 140px; font-weight: 900; text-shadow: 0px 0px 50px rgba(#fc6161, 0.2)">ERROR</h1>
                <h3 class="text-red-300" style="font-size: 80px; font-weight: 900; margin-top: -90px; margin-bottom: 50px">something's went wrong</h3>
                <Button @click="goHome" style="margin-top: 50px">Go back to home</Button>
            </div>
            <div class="exception-footer absolute items-center flex" style="bottom: 60px">
                <img :src="`/layout/images/logo/logo-${logo()}.png`" class="exception-logo" style="width: 34px" />
                <img :src="`/layout/images/logo/appname-${logo()}.png`" class="exception-appname ml-4" style="width: 72px" />
            </div>
        </div>
    </div>
</template>
