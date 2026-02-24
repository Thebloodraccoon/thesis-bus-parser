<script setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import InputText from 'primevue/inputtext';
import InputNumber from 'primevue/inputnumber';
import Checkbox from 'primevue/checkbox';
import Button from 'primevue/button';

import { useSites } from '@/composables/SiteComposables/useSites';
import { useUserStore } from '@/stores/useUserStore';

const route = useRoute();
const router = useRouter();
const toast = useToast();

const { site, fetchSite, updateSite, loading } = useSites();
const siteData = ref({});

// Получение ID из URL
const siteId = route.params.id;

// Получение роли пользователя
const { isAdmin, fetchCurrentUser } = useUserStore();

onMounted(async () => {
    await fetchCurrentUser(); // Получение текущего пользователя и его роли
    await fetchSite(siteId);

    // Копируем данные в siteData для редактирования
    siteData.value = { ...site.value };
    console.log(siteData.value);
});

// Обновление данных сайта
async function handleUpdate() {
    try {
        await updateSite(siteId, siteData.value);
        await router.push('/site/list');
    } catch (error) {
        console.error('Ошибка обновления сайта:', error);
    }
}
</script>

<template>
    <div class="card site-detail" v-if="!loading && siteData">
        <h1>Редактировать сайт</h1>
        <div class="form-container">
            <div class="field mb-4">
                <label for="name">Название:</label>
                <InputText v-model="siteData.name" :disabled="!isAdmin" />
            </div>

            <div class="field mb-4">
                <label for="url">URL:</label>
                <InputText v-model="siteData.url" :disabled="!isAdmin" />
            </div>

            <div class="field mb-4">
                <label for="api_key">API ключ:</label>
                <InputText v-model="siteData.api_key" :disabled="!isAdmin" />
            </div>

            <div class="field-checkbox mb-4">
                <Checkbox v-model="siteData.is_active" :disabled="!isAdmin" binary />
                <label for="is_active" class="ml-2">Активен</label>
            </div>

            <div class="field-checkbox mb-4">
                <Checkbox v-model="siteData.is_aggregator" :disabled="!isAdmin" binary />
                <label for="is_aggregator" class="ml-2">Агрегатор</label>
            </div>

            <div class="field mb-4">
                <label for="depth">Depth:</label>
                <InputNumber v-model="siteData.depth" :disabled="!isAdmin" :min="1" />
            </div>

            <div class="field mb-4">
                <label for="threads">Threads:</label>
                <InputNumber v-model="siteData.threads" :disabled="!isAdmin" :min="1" />
            </div>

            <!-- Кнопки -->
            <div class="button-group">
                <!-- Кнопка "Сохранить" видна только для админов -->
                <Button v-if="isAdmin" label="Сохранить" class="p-button-success mr-2" @click="handleUpdate" :loading="loading" />
                <Button label="Отмена" class="p-button-secondary" @click="$router.push('/site/list')" />
            </div>
        </div>
    </div>

    <!-- Лоудер пока идет загрузка данных -->
    <div v-else class="loading-container">
        <p>Загрузка данных...</p>
    </div>
</template>

<style scoped>
.site-detail {
    padding: 30px;
    max-width: 700px;
}

.field {
    display: flex;
    flex-direction: column;
}

.button-group {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}

.loading-container {
    text-align: center;
    padding: 50px;
}
</style>
