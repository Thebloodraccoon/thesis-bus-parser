<script setup>
import { onMounted, ref } from 'vue';
import { useToast } from 'primevue/usetoast';
import UserTable from '@/components/UsersComponents/UserTable.vue';
import DeleteUserDialog from '@/components/UsersComponents/DeleteUserDialog.vue';
import InviteUserDialog from '@/components/UsersComponents/InviteUserDialog.vue';
import { useInviteUser } from '@/composables/UserComposables/useInviteUser';
import { useDeleteUser } from '@/composables/UserComposables/useDeleteUser';
import { useUpdateRole } from '@/composables/UserComposables/useUpdateRole';
import { UserService } from '@/service/UserService';

const toast = useToast();

// Table Data
const users = ref([]);
const roleOptions = [
    { label: 'Администратор', value: 'admin' },
    { label: 'Менеджер', value: 'dps_manager' }
];

onMounted(async () => {
    try {
        users.value = await UserService.getUsers();
    } catch (error) {
        toast.add({
            severity: 'error',
            summary: 'Ошибка',
            detail: error.message,
            life: 5000
        });
    }
});

// Use composables
const deleteUserDialog = ref(null);
const { openDeleteDialog, handleDeleteUser } = useDeleteUser(deleteUserDialog);

const { inviteUserDialog, openInviteDialog, handleInviteUser, isLoading } = useInviteUser();
const { updateRole } = useUpdateRole();

function addUser(newUser) {
    users.value.push(newUser);
}

function removeUser(userId) {
    users.value = users.value.filter((user) => user.id !== userId);
}

function updateUserRole(user, newRole) {
    const userIndex = users.value.findIndex((u) => u.id === user.id);
    if (userIndex !== -1) {
        users.value[userIndex].role = newRole;
    }
}

function handleUserDeletion(userId) {
    handleDeleteUser(userId, () => removeUser(userId));
}
</script>

<template>
    <div>
        <UserTable
            :users="users"
            :role-options="roleOptions"
            :disabled-roles="['admin@admin.com']"
            @open-invite-dialog="openInviteDialog"
            @update-role="
                (user, role) => {
                    updateRole(user, role).then(() => updateUserRole(user, role));
                }
            "
            @open-delete-dialog="openDeleteDialog"
        />
        <InviteUserDialog :roles="roleOptions" @invite-user="handleInviteUser($event).then(addUser)" :is-loading="isLoading" ref="inviteUserDialog" />
        <DeleteUserDialog @delete-user="handleUserDeletion" ref="deleteUserDialog" />
    </div>
</template>
