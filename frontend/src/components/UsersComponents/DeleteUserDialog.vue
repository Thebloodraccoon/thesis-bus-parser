<script setup>
import { ref } from 'vue';

const showDialog = ref(false);
let userIdToDelete = null;

function openDialog(userId) {
    userIdToDelete = userId;
    showDialog.value = true;
}

function closeDialog() {
    showDialog.value = false;
    userIdToDelete = null;
}

defineExpose({ openDialog, closeDialog });
defineEmits(['delete-user']);
</script>

<template>
    <Dialog v-model:visible="showDialog" header="Confirmation of deletion" :modal="true" :closable="false">
        <p>Are you sure you want to remove this user?</p>
        <template #footer>
            <Button label="Отмена" class="p-button-secondary" @click="closeDialog" />
            <Button label="Удалить" class="p-button-danger" @click="$emit('delete-user', userIdToDelete)" />
        </template>
    </Dialog>
</template>
