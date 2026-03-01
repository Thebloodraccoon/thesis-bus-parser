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
});

const { createSite, fetchSites } = useSites();
const { errors, validateForm } = useSiteValidation(siteData);
const { isAdmin, fetchCurrentUser } = useUserStore();

async function handleSubmit() {
    if (!validateForm()) {
        toast.add({
            severity: 'warn',
            summary: 'Warning',
            detail: 'Fill in the required fields',
            life: 3000
        });
        return;
    }

    try {
        await createSite(siteData.value);
        await router.push('/site/list');
    } catch (error) {
        console.error('Website creation error:', error);
    }
}

onMounted(() => {
    fetchCurrentUser();
    fetchSites();
    if (!isAdmin.value) {
        toast.add({
            severity: 'error',
            summary: 'An error occurred',
            detail: 'You do not have the rights to create a website',
            life: 5000
        });
        router.push('/site/list');
    }
});
</script>

<template>
    <div class="card site-create">
        <h1 class="mb-4">Add a new website</h1>
        <div class="form-container">
            <div class="field mb-4">
                <label for="name">Name:</label>
                <InputText v-model="siteData.name" placeholder="Enter a name" :class="{ 'p-invalid': errors.name }" />
                <small v-if="errors.name" class="p-error">{{ errors.name }}</small>
            </div>

            <div class="field mb-4">
                <label for="url">URL:</label>
                <InputText v-model="siteData.url" placeholder="Enter URL" :class="{ 'p-invalid': errors.url }" />
                <small v-if="errors.url" class="p-error">{{ errors.url }}</small>
            </div>

            <div class="field-checkbox mb-4">
                <Checkbox v-model="siteData.is_active" inputId="is_active" binary />
                <label for="is_active" class="ml-2">Active</label>
            </div>

            <div class="button-group">
                <Button type="button" label="Create" class="p-button-success mr-2" @click="handleSubmit" />
                <Button type="button" label="Cancel" class="p-button-secondary" @click="$router.push('/site/list')" />
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
