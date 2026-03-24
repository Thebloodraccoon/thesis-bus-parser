<script setup>
import { useLayout } from '@/layout/composables/layout';
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const { isDarkTheme } = useLayout();
const router = useRouter();

const confirmed = ref(false);
const submit = ref(false);

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
            <img :src="'/demo/images/pages/register-' + (isDarkTheme ? 'ondark' : 'onlight') + '.png'" alt="atlantis" class="h-screen w-full" />
        </div>
        <div class="w-full" style="background: var(--surface-ground)">
            <Fluid class="min-h-screen text-center w-full flex items-center md:items-start justify-center flex-col bg-auto md:bg-contain bg-no-repeat" style="padding: 20% 10% 20% 10%; background: var(--exception-pages-image)">
                <div class="flex flex-col">
                    <div class="flex items-center mb-12 logo-container">
                        <img :src="`/layout/images/logo/logo-${logo()}.png`" class="login-logo" style="width: 45px" />
                        <img :src="`/layout/images/logo/appname-${logo()}.png`" class="login-appname ml-4" style="width: 100px" />
                    </div>
                    <div class="form-container text-left" style="max-width: 320px; min-width: 270px">
                        <span class="text-2xl font-semibold m-0 mb-2">Register</span>
                        <span class="block text-surface-600 dark:text-surface-200 font-medium mb-6">Let's get started</span>
                        <IconField>
                            <InputIcon class="pi pi-user" />
                            <InputText type="text" autocomplete="off" placeholder="username" class="block mb-4" style="max-width: 320px; min-width: 270px" />
                        </IconField>
                        <IconField>
                            <InputIcon class="pi pi-envelope" />
                            <InputText type="mail" autocomplete="off" placeholder="email" class="block mb-4" style="max-width: 320px; min-width: 270px" />
                        </IconField>
                        <IconField>
                            <InputIcon class="pi pi-key" />
                            <InputText type="password" autocomplete="off" placeholder="Password" class="block mb-4" style="max-width: 320px; min-width: 270px" />
                        </IconField>
                        <div class="mt-2 flex flex-wrap">
                            <Checkbox type="checkbox" id="confirmed" v-model="confirmed" :binary="true" class="mr-2" />
                            <label for="confirmed" class="text-surface-900 dark:text-surface-0 font-medium mr-2">I have read the</label>
                            <a class="text-surface-600 dark:text-surface-200 hover:text-primary cursor-pointer">Terms and Conditions</a>
                        </div>
                    </div>
                    <div class="button-container mt-6 text-left" style="max-width: 320px; min-width: 270px">
                        <div class="buttons flex items-center gap-4">
                            <Button type="button" @click="goHome" class="block" severity="danger" outlined style="max-width: 320px; margin-bottom: 32px">Cancel</Button>
                            <Button type="button" @click="submit" class="block" style="max-width: 320px; margin-bottom: 32px">Submit</Button>
                        </div>
                        <span class="font-medium text-surface-600 dark:text-surface-200"
                            >Already have an account? <a class="font-semibold cursor-pointer text-surface-900 dark:text-surface-0 hover:text-primary transition-colors duration-300">Login</a></span
                        >
                    </div>
                </div>

                <div class="login-footer flex items-center mt-6">
                    <div class="flex items-center login-footer-logo-container pr-6 mr-6 border-r border-surface-200 dark:border-surface-700">
                        <img src="/layout/images/logo/logo-gray.png" class="login-footer-logo" style="width: 22px" />
                        <img src="/layout/images/logo/appname-gray.png" class="login-footer-appname ml-2" style="width: 45px" />
                    </div>
                    <span class="text-sm text-surface-500 dark:text-surface-400 mr-4">Copyright 2026</span>
                </div>
            </Fluid>
        </div>
    </div>
</template>
