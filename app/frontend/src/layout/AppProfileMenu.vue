<script setup>
import { useLayout } from '@/layout/composables/layout';

const date = new Date();

const { layoutState } = useLayout();
</script>

<template>
    <Drawer v-model:visible="layoutState.rightMenuVisible" header="Profile" position="right" class="layout-profile-sidebar !w-full sm:!w-[28rem]" :class="{ 'layout-rightmenu-active': layoutState.rightMenuActive }">
        <div class="layout-rightmenu h-full overflow-y-auto overflow-x-hidden">
            <div class="user-detail-wrapper text-center" style="padding: 4.5rem 0 2rem 0">
                <div class="user-detail-content mb-6">
                    <img src="/layout/images/avatar/gene.png" alt="atlantis" class="user-image" />
                    <span class="user-name text-2xl text-center block mt-6 mb-1">Gene Russell</span>
                    <span class="user-number">(406) 555-0120</span>
                </div>
                <div class="user-tasks flex justify-between items-center py-6 px-4 border-b border-surface-200 dark:border-surface-700">
                    <div class="user-tasks-item in-progress font-medium">
                        <a class="task-number text-red-500 flex justify-center items-center rounded" style="background: rgba(255, 255, 255, 0.05); padding: 9px; width: 50px; height: 50px; font-size: 30px">23</a>
                        <span class="task-name block mt-4">Progress</span>
                    </div>
                    <div class="user-tasks-item font-medium">
                        <a class="task-number flex justify-center items-center rounded" style="background: rgba(255, 255, 255, 0.05); padding: 9px; width: 50px; height: 50px; font-size: 30px">6</a>
                        <span class="task-name block mt-4">Overdue</span>
                    </div>
                    <div class="user-tasks-item font-medium">
                        <a class="task-number flex justify-center items-center rounded" style="background: rgba(255, 255, 255, 0.05); padding: 9px; width: 50px; height: 50px; font-size: 30px">38</a>
                        <span class="task-name block mt-4">All deals</span>
                    </div>
                </div>
            </div>
            <div>
                <Calendar v-model="date" inline styleClass="w-full p-0"></Calendar>
            </div>
            <div class="daily-plan-wrapper mt-8">
                <span class="today-date">14 Sunday, Jun 2020</span>
                <ul class="list-none overflow-hidden p-0 m-0">
                    <li class="mt-4 rounded py-2 px-4" style="background: rgba(255, 255, 255, 0.05)">
                        <span class="event-time block font-semibold text-surface-500 dark:text-surface-400">1:00 PM - 2:00 PM</span>
                        <span class="event-topic block mt-2">Meeting with Alfredo Rhiel Madsen</span>
                    </li>
                    <li class="mt-4 rounded py-2 px-4" style="background: rgba(255, 255, 255, 0.05)">
                        <span class="event-time block font-semibold text-surface-500 dark:text-surface-400">2:00 PM - 3:00 PM</span>
                        <span class="event-topic block mt-2">Team Sync</span>
                    </li>
                    <li class="mt-4 rounded py-2 px-4" style="background: rgba(255, 255, 255, 0.05)">
                        <span class="event-time block font-semibold text-surface-500 dark:text-surface-400">5:00 PM - 6:00 PM</span>
                        <span class="event-topic block mt-2">Team Sync</span>
                    </li>
                    <li class="mt-4 rounded py-2 px-4" style="background: rgba(255, 255, 255, 0.05)">
                        <span class="event-time block font-semibold text-surface-500 dark:text-surface-400">7:00 PM - 7:30 PM</span>
                        <span class="event-topic block mt-2">Meeting with Engineering managers</span>
                    </li>
                </ul>
            </div>
        </div>
    </Drawer>
</template>
