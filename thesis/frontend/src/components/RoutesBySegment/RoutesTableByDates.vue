<script setup>
import { computed } from 'vue';
import { formatPrice } from '@/service/currencyUtils';

const props = defineProps({
  routesData: Array,   // [{ date, "1": {...}, "2": null, ... }]
  aggregators: Object, // { "1": "AgentName", "2": "OtherAgent" }
  loading: Boolean,
  size: Number,
  openDialog: Function
});

// Список agentId з aggregators
const agentIds = computed(() => Object.keys(props.aggregators || {}));
</script>

<template>
  <div class="overflow-x-auto w-full">

    <!-- Загрузка -->
    <div v-if="loading" class="card border border-surface rounded p-6 w-full">
      <div class="font-semibold text-xl mb-4">Uploading data...</div>
      <div v-for="n in size" :key="n" class="mb-4">
        <div class="flex space-x-4">
          <Skeleton width="10rem" class="mb-2" />
          <Skeleton height=".5rem" class="flex-1" v-for="i in 6" :key="i" />
        </div>
      </div>
    </div>

    <!-- Нет данных -->
    <div v-else-if="!routesData || routesData.length === 0" class="w-full text-center py-8 text-gray-500">
      <i class="pi pi-info-circle mr-2" />
There is no data to display. Check the filters.
    </div>

    <!-- Таблица -->
    <DataTable
      v-else
      :value="routesData"
      class="min-w-max"
      scrollable
      scrollDirection="horizontal"
    >
      <!-- Колонка дати -->
      <Column field="date" header="Дата" frozen alignFrozen="left" style="min-width: 140px">
        <template #body="slotProps">
          <div class="rounded p-2 font-semibold text-sm">
            {{ slotProps.data.date }}
          </div>
        </template>
      </Column>

      <!-- Колонки агентів -->
      <Column
        v-for="agentId in agentIds"
        :key="agentId"
        :field="agentId"
        :header="aggregators[agentId] || `Agent ${agentId}`"
        style="min-width: 160px"
      >
        <template #body="slotProps">
          <div
            @click="() => {
              const cell = slotProps.data[agentId];
              if (cell && openDialog) {
                openDialog({
                  routeId: cell.id,
                  date: slotProps.data.date,
                  agentId
                });
              }
            }"
            :class="[
              'rounded p-2 transition-colors duration-300',
              slotProps.data[agentId]
                ? 'cursor-pointer hover:bg-primary-100 dark:hover:bg-primary-900'
                : 'cursor-default'
            ]"
          >
            <template v-if="slotProps.data[agentId]">
              <!-- Кількість сегментів -->
              <div class="text-xs text-surface-500 mb-1">
                🚌 {{ slotProps.data[agentId].count }} segments
              </div>

              <!-- Мін / Медіана / Макс -->
              <div class="flex flex-col gap-0.5 text-sm">
                <div class="flex items-center gap-1">
                  <span class="text-surface-400 text-xs w-8">min</span>
                  <span class="text-blue-600 dark:text-blue-300 font-bold">
                    {{ formatPrice(slotProps.data[agentId].min, slotProps.data[agentId].currency) }}
                  </span>
                </div>
                <div class="flex items-center gap-1">
                  <span class="text-surface-400 text-xs w-8">med</span>
                  <span class="text-orange-500 dark:text-yellow-400 font-bold">
                    {{ formatPrice(slotProps.data[agentId].median, slotProps.data[agentId].currency) }}
                  </span>
                </div>
                <div class="flex items-center gap-1">
                  <span class="text-surface-400 text-xs w-8">max</span>
                  <span class="text-red-600 dark:text-red-400 font-bold">
                    {{ formatPrice(slotProps.data[agentId].max, slotProps.data[agentId].currency) }}
                  </span>
                </div>
              </div>
            </template>

            <template v-else>
              <div class="text-sm text-gray-400 italic">No data</div>
            </template>
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
</template>