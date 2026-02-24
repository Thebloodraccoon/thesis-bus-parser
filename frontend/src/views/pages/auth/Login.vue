<script setup>
import {useLayout} from '@/layout/composables/layout';
import router from '@/router';
import {onUnmounted, ref, watch} from 'vue';
import {useToast} from 'primevue/usetoast';
import {AuthService} from '@/service/AuthService';

const {isDarkTheme} = useLayout();
const toast = useToast();

function logo() {
  return isDarkTheme.value ? 'light' : 'dark';
}

const email = ref('');
const password = ref('');
const error = ref(null);

const showTwoFAModal = ref(false);
const tempToken = ref(null);
const otpUri = ref(null);
const otpCode = ref('');


const validateEmail = (email) => {
  const emailRegex = /^[\w.-]+@[\w-]+(\.[a-z]{2,4})+$/i; // Correct regex
  return emailRegex.test(email);
};

async function handleLogin() {
  try {
    if (!validateEmail(email.value)) {
      toast.add({
        severity: 'warn',
        summary: 'Внимание',
        detail: 'Введите корректный email',
        life: 3000
      });
      return;
    }

    const data = await AuthService.login(email.value, password.value);

    // === 1. Вариант: обычный вход (админ)
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);

      toast.add({
        severity: 'success',
        summary: 'Успех',
        detail: 'Вы успешно вошли в систему',
        life: 3000
      });

      const redirectPath = localStorage.getItem('redirectPath');
      if (redirectPath) {
        localStorage.removeItem('redirectPath');
        await router.push(redirectPath);
      } else {
        await router.push('/');
      }
      return;
    }

    // === 2. Вариант: 2FA вход
    // temp_token обязателен
    tempToken.value = data.temp_token;
    otpUri.value = data.otp_uri || null;
    showTwoFAModal.value = true;

  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: err.message,
      life: 5000
    });
  }
}


async function handleVerifyOtp() {
  try {
    const result = await AuthService.verifyOtp(otpCode.value, tempToken.value);

    toast.add({
      severity: 'success',
      summary: 'Успех',
      detail: 'Вы вошли по 2FA',
      life: 3000
    });

    showTwoFAModal.value = false;
    await router.push('/');
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: err.message,
      life: 5000
    });
  }
}

const countdown = ref(300); // 5 минут
let countdownInterval = null;

watch(showTwoFAModal, (visible) => {
  if (visible) {
    countdown.value = 300;
    startCountdown();
  } else {
    stopCountdown();
  }
});

function startCountdown() {
  stopCountdown(); // перестраховка
  countdownInterval = setInterval(() => {
    countdown.value--;
    if (countdown.value <= 0) {
      stopCountdown();
      showTwoFAModal.value = false;
      toast.add({
        severity: 'warn',
        summary: 'Время вышло',
        detail: 'Срок действия временного токена истёк. Повторите вход.',
        life: 5000
      });
    }
  }, 1000);
}

function stopCountdown() {
  if (countdownInterval) {
    clearInterval(countdownInterval);
    countdownInterval = null;
  }
}

onUnmounted(() => {
  stopCountdown();
});
</script>

<template>
  <div :class="'login-body flex min-h-screen ' + (!isDarkTheme ? 'layout-light' : 'layout-dark')">
    <div class="login-image w-6/12 h-screen hidden md:block" style="max-width: 490px">
      <img :src="'/demo/images/pages/login-' + (isDarkTheme ? 'ondark' : 'onlight') + '.png'" alt="atlantis"
           class="h-screen w-full"/>
    </div>
    <div class="login-panel w-full" style="background: var(--surface-ground)">
      <Fluid
          class="min-h-screen text-center w-full flex items-center md:items-start justify-center flex-col bg-auto md:bg-contain bg-no-repeat"
          style="padding: 20% 10% 20% 10%; background: var(--exception-pages-image)">
        <div class="flex flex-col">
          <div class="flex items-center mb-12 logo-container">
            <img :src="`/layout/images/logo/appname-${logo()}.png`" class="login-appname ml-4" style="width: 200px"/>
          </div>
          <div class="form-container">
            <IconField>
              <InputIcon class="pi pi-envelope"/>
              <InputText v-model="email" type="text" autocomplete="off" placeholder="Email" class="block mb-4"
                         style="max-width: 320px; min-width: 270px"/>
            </IconField>
            <IconField>
              <InputIcon class="pi pi-key"/>
              <InputText v-model="password" type="password" autocomplete="off" placeholder="Password" class="block mb-4"
                         style="max-width: 320px; min-width: 270px"/>
            </IconField>
            <p v-if="error" class="text-red-500 text-sm mb-4">{{ error }}</p>
          </div>
          <div class="button-container">
            <Button type="button" @click="handleLogin" class="block" style="max-width: 320px; margin-bottom: 32px">
              Login
            </Button>
          </div>
        </div>

        <div class="login-footer flex items-center absolute" style="bottom: 75px">
          <div
              class="flex items-center login-footer-logo-container pr-6 mr-6 border-r border-surface-200 dark:border-surface-700">
            <img src="/layout/images/logo/logo-gray.png" class="login-footer-logo" style="width: 22px"/>
            <img src="/layout/images/logo/appname-gray.png" class="login-footer-appname ml-2" style="width: 45px"/>
          </div>
          <span class="text-sm text-surface-500 dark:text-surface-400 mr-4">Copyright 2024</span>
        </div>
      </Fluid>
    </div>
  </div>

  <Dialog v-model:visible="showTwoFAModal" header="Двухфакторная аутентификация" modal>
    <div class="flex flex-col items-center justify-center text-center p-4">
      <p class="mb-4 text-base font-medium">Введите код из приложения Google Authenticator</p>

      <p class="text-sm text-gray-400 mb-4">
        Время на ввод: <span class="font-semibold text-black dark:text-white">{{ Math.floor(countdown / 60) }}:{{ String(countdown % 60).padStart(2, '0') }}</span>
      </p>

      <div v-if="otpUri" class="qr-container mb-4">
        <img
            :src="`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(otpUri)}`"
            alt="QR Code"
            class="rounded-lg shadow-md border border-gray-300 dark:border-gray-600 m-auto"
        />
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-2 break-words max-w-xs select-all">
          {{ otpUri }}
        </p>
      </div>

      <InputText
          v-model="otpCode"
          placeholder="Введите код из приложения"
          class="mb-2 w-full max-w-xs"
      />
      <Button label="Подтвердить" @click="handleVerifyOtp"/>
    </div>
  </Dialog>


</template>
