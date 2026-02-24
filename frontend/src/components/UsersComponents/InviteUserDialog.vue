<script setup>
import { ref, computed } from 'vue';
import Button from 'primevue/button';

const props = defineProps({
    roles: {
        type: Array,
        required: true
    },
    isLoading: {
        type: Boolean,
        default: false
    }
});

computed(() => props.isLoading);

const form = ref({
    email: '',
    role: ''
});
const showDialog = ref(false);

function openDialog() {
    showDialog.value = true;

    if (props.roles.length > 0) {
        form.value.role = props.roles[0].value;
    }
}

function closeDialog() {
    showDialog.value = false;
    form.value = {
        email: '',
        role: ''
    };
}

const emit = defineEmits(['invite-user']);

async function onSubmit() {
    emit('invite-user', form.value);
}

defineExpose({ openDialog, closeDialog });
</script>
<template>
    <Dialog v-model:visible="showDialog" header="Invite a user" :modal="true" :closable="false" :dismissableMask="true" class="min-w-[450px] min-h-[350px] flex items-center justify-center">
        <form @submit.prevent="onSubmit" class="flex flex-col gap-4 w-80">
            <div class="flex flex-col gap-2">
                <label for="email" class="block text-sm font-medium text-gray-700">Email</label>
                <InputText v-model="form.email" id="email" placeholder="Enter email" class="w-full" required />
            </div>
            <div class="flex flex-col gap-2">
                <label for="role" class="block text-sm font-medium text-gray-700">Role</label>
                <Select v-model="form.role" :options="roles" option-label="label" option-value="value" id="role" class="w-full" required />
            </div>
            <div class="flex justify-end gap-4">
                <Button type="button" label="Cancel" class="p-button-secondary" @click="closeDialog" />
                <Button type="submit" label="Invite" class="p-button-primary p-button" :loading="isLoading" :disabled="isLoading" />
            </div>
        </form>
    </Dialog>
</template>
