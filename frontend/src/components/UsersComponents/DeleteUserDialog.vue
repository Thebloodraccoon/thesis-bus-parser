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
    <Dialog v-model:visible="showDialog" header="Подтверждение удаления" :modal="true" :closable="false">
        <p>Вы уверены, что хотите удалить этого пользователя?</p>
        <template #footer>
            <Button label="Отмена" class="p-button-secondary" @click="closeDialog" />
            <Button label="Удалить" class="p-button-danger" @click="$emit('delete-user', userIdToDelete)" />
        </template>
    </Dialog>
</template>
