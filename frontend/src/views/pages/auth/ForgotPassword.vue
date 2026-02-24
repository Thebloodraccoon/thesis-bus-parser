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
    <div :class="'login-body flex min-h-screen  ' + (isDarkTheme ? 'layout-dark' : 'layout-light')">
        <div class="login-image w-6/12 h-screen hidden md:block" style="max-width: 490px">
            <img :src="'/demo/images/pages/forgot-password-' + (isDarkTheme ? 'ondark' : 'onlight') + '.png'" alt="atlantis" class="h-screen w-full" />
        </div>
        <div class="w-full" style="background: var(--surface-ground)">
            <Fluid class="min-h-screen text-center w-full flex items-center md:items-start justify-center flex-col bg-auto md:bg-contain bg-no-repeat" style="padding: 20% 10% 20% 10%; background: var(--exception-pages-image)">
                <div class="flex flex-col">
                    <div class="flex items-center mb-12 logo-container">
                        <img :src="`/layout/images/logo/logo-${logo()}.png`" class="login-logo" style="width: 45px" />
                        <img :src="`/layout/images/logo/appname-${logo()}.png`" class="login-appname ml-4" style="width: 100px" />
                    </div>
                    <div class="form-container text-left" style="max-width: 320px; min-width: 270px">
                        <span class="text-2xl font-semibold m-0">Forgot Password</span>
                        <span class="block text-surface-600 dark:text-surface-200 font-medium mb-6 mt-4">Enter your email to reset your password</span>
                        <IconField>
                            <InputIcon class="pi pi-envelope" />
                            <InputText type="mail" autocomplete="off" placeholder="Email" class="block mb-4" style="max-width: 320px; min-width: 270px" />
                        </IconField>
                    </div>
                    <div class="button-container mt-6 text-left" style="max-width: 320px; min-width: 270px">
                        <div class="buttons flex items-center gap-4">
                            <Button type="button" @click="goHome" class="block" style="max-width: 320px; margin-bottom: 32px">Submit</Button>
                        </div>
                    </div>
                </div>
                <div class="login-footer flex items-center absolute" style="bottom: 75px">
                    <div class="flex items-center login-footer-logo-container pr-6 mr-6 border-r border-surface-200 dark:border-surface-700">
                        <img src="/layout/images/logo/logo-gray.png" class="login-footer-logo" style="width: 22px" />
                        <img src="/layout/images/logo/appname-gray.png" class="login-footer-appname ml-2" style="width: 45px" />
                    </div>
                    <span class="text-sm text-surface-500 dark:text-surface-400 mr-4">Copyright 2024</span>
                </div>
            </Fluid>
        </div>
    </div>
</template>
