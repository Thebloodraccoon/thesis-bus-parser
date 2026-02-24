<script setup>
import { useLayout } from '@/layout/composables/layout';
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const { isDarkTheme } = useLayout();
const router = useRouter();

const value1 = ref(null);
const value2 = ref(null);
const value3 = ref(null);
const value4 = ref(null);
const verify = ref(false);

function logo() {
    return isDarkTheme.value ? 'light' : 'dark';
}

function goHome() {
    router.push('/');
}

const focus = (event) => {
    const regexNum = /^\d+$/;
    const isValid = regexNum.test(event.key);
    const nextElementInputRef = event.currentTarget.nextElementSibling.children[0];

    isValid && nextElementInputRef.focus();
};
</script>

<template>
    <div :class="'login-body flex min-h-screen  ' + (isDarkTheme ? 'layout-dark' : 'layout-light')">
        <div class="login-image w-6/12 h-screen hidden md:block" style="max-width: 490px">
            <img :src="'/demo/images/pages/verification-' + (isDarkTheme ? 'ondark' : 'onlight') + '.png'" alt="atlantis" class="h-screen w-full" />
        </div>
        <div class="w-full" style="background: var(--surface-ground)">
            <Fluid class="min-h-screen text-center w-full flex items-center md:items-start justify-center flex-col bg-auto md:bg-contain bg-no-repeat" style="padding: 20% 10% 20% 10%; background: var(--exception-pages-image)">
                <div class="flex flex-col">
                    <div class="flex items-center mb-12 logo-container">
                        <img :src="`/layout/images/logo/logo-${logo()}.png`" class="login-logo" style="width: 45px" />
                        <img :src="`/layout/images/logo/appname-${logo()}.png`" class="login-appname ml-4" style="width: 100px" />
                    </div>
                    <div class="form-container text-left" style="max-width: 320px; min-width: 270px">
                        <span class="text-surface-900 dark:text-surface-0 font-bold mb-2 text-2xl m-0">Verification</span>
                        <span class="text-surface-600 dark:text-surface-200 font-medium">We have sent code to you email:</span>
                        <div class="flex items-center mt-1 mb-6">
                            <i class="pi pi-envelope text-surface-600 dark:text-surface-200"></i>
                            <span class="text-surface-900 dark:text-surface-0 font-bold ml-2">dm**@gmail.com</span>
                        </div>
                        <div class="flex justify-between w-full items-center gap-4">
                            <InputNumber inputId="val1" v-model="value1" inputClass="w-12 text-center" :max="9" @keyup="focus($event)"></InputNumber>
                            <InputNumber inputId="val2" v-model="value2" inputClass="w-12 text-center" :max="9" @keyup="focus($event)"></InputNumber>
                            <InputNumber inputId="val3" v-model="value3" inputClass="w-12 text-center" :max="9" @keyup="focus($event)"></InputNumber>
                            <InputNumber inputId="val4" v-model="value4" inputClass="w-12 text-center" :max="9"></InputNumber>
                        </div>
                    </div>
                    <div class="button-container mt-6 text-left" style="max-width: 320px; min-width: 270px">
                        <div class="buttons flex items-center gap-4">
                            <Button @click="goHome" class="block" severity="danger" outlined style="max-width: 320px; margin-bottom: 32px">Cancel</Button>
                            <Button @click="verify" class="block" style="max-width: 320px; margin-bottom: 32px">Verify</Button>
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
