<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Checkbox from 'primevue/checkbox';
import Button from 'primevue/button';

import { useUserStore } from '@/stores/useUserStore';
import { useSiteValidation } from '@/composables/SiteComposables/useSiteValidation';
import { useSites } from '@/composables/SiteComposables/useSites';

const router = useRouter();
const toast = useToast();

const siteData = ref({
    name: '',
    url: '',
    is_active: true,
    api_key: '',
    is_aggregator: true,
    depth: 1,
    threads: 1
});

const { createSite, fetchSites } = useSites();
const { errors, validateForm } = useSiteValidation(siteData);
const { isAdmin, fetchCurrentUser } = useUserStore();

async function handleSubmit() {
    if (!validateForm()) {
        toast.add({
            severity: 'warn',
            summary: 'Внимание',
            detail: 'Заполните обязательные поля',
            life: 3000
        });
        return;
    }

    try {
        await createSite(siteData.value);
        await router.push('/site/list');
    } catch (error) {
        console.error('Ошибка создания сайта:', error);
    }
}

onMounted(() => {
    fetchCurrentUser();
    fetchSites();
    if (!isAdmin.value) {
        toast.add({
            severity: 'error',
            summary: 'Ошибка',
            detail: 'У вас нет прав для создания сайта',
            life: 5000
        });
        router.push('/site/list');
    }
});
</script>

<template>
    <div class="card site-create">
        <h1>Создать новый сайт</h1>
        <div class="form-container">
            <div class="field mb-4">
                <label for="name">Название:</label>
                <InputText v-model="siteData.name" placeholder="Введите название" :class="{ 'p-invalid': errors.name }" />
                <small v-if="errors.name" class="p-error">{{ errors.name }}</small>
            </div>

            <div class="field mb-4">
                <label for="url">URL:</label>
                <InputText v-model="siteData.url" placeholder="Введите URL" :class="{ 'p-invalid': errors.url }" />
                <small v-if="errors.url" class="p-error">{{ errors.url }}</small>
            </div>

            <div class="field mb-4">
                <label for="api_key">API ключ:</label>
                <InputText v-model="siteData.api_key" placeholder="Введите API ключ" :class="{ 'p-invalid': errors.api_key }" />
                <small v-if="errors.api_key" class="p-error">{{ errors.api_key }}</small>
            </div>

            <div class="field-checkbox mb-4">
                <Checkbox v-model="siteData.is_active" inputId="is_active" binary />
                <label for="is_active" class="ml-2">Активен</label>
            </div>

            <div class="field-checkbox mb-4">
                <Checkbox v-model="siteData.is_aggregator" inputId="is_aggregator" binary />
                <label for="is_aggregator" class="ml-2">Агрегатор</label>
            </div>

            <div class="field mb-4">
                <label for="depth">Depth:</label>
                <InputNumber v-model="siteData.depth" placeholder="Введите глубину" :min="1" :class="{ 'p-invalid': errors.depth }" />
                <small v-if="errors.depth" class="p-error">{{ errors.depth }}</small>
            </div>

            <div class="field mb-4">
                <label for="threads">Threads:</label>
                <InputNumber v-model="siteData.threads" placeholder="Введите количество потоков" :min="1" :class="{ 'p-invalid': errors.threads }" />
                <small v-if="errors.threads" class="p-error">{{ errors.threads }}</small>
            </div>

            <div class="button-group">
                <Button type="button" label="Создать" class="p-button-success mr-2" @click="handleSubmit" />
                <Button type="button" label="Отмена" class="p-button-secondary" @click="$router.push('/site/list')" />
            </div>
        </div>
    </div>
</template>

<style scoped>
.site-create {
    padding: 30px;
    max-width: 700px;
}

.field {
    display: flex;
    flex-direction: column;
}

.p-invalid {
    border-color: #f44336;
}

.p-error {
    color: #f44336;
    font-size: 0.875em;
}

.button-group {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}
</style>
