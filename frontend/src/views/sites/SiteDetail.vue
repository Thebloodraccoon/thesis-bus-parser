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

const siteId = route.params.id;
const { isAdmin, fetchCurrentUser } = useUserStore();

onMounted(async () => {
    await fetchCurrentUser();
    await fetchSite(siteId);

    siteData.value = { ...site.value };
    console.log(siteData.value);
});

async function handleUpdate() {
    try {
        await updateSite(siteId, siteData.value);
        await router.push('/site/list');
    } catch (error) {
        console.error('Site update error:', error);
    }
}
</script>

<template>
    <div class="card site-detail" v-if="!loading && siteData">
        <h1 class="mb-4">Edit site</h1>
        <div class="form-container">
            <div class="field mb-4">
                <label for="name">Name:</label>
                <InputText v-model="siteData.name" :disabled="!isAdmin" />
            </div>

            <div class="field mb-4">
                <label for="url">URL:</label>
                <InputText v-model="siteData.url" :disabled="!isAdmin" />
            </div>

            <div class="field-checkbox mb-4">
                <Checkbox v-model="siteData.is_active" :disabled="!isAdmin" binary />
                <label for="is_active" class="ml-2">Active</label>
            </div>

            <div class="button-group">
                <Button v-if="isAdmin" label="Save" class="p-button-success mr-2" @click="handleUpdate" :loading="loading" />
                <Button label="Cansel" class="p-button-secondary" @click="$router.push('/site/list')" />
            </div>
        </div>
    </div>

    <div v-else class="loading-container">
        <p>Loading data...</p>
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
