<script setup>
import {formatPrice} from "@/service/currencyUtils";

const props = defineProps({
  routesData: Array,
  dates: Array,
  aggregators: Object,
  loading: Boolean,
  size: Number,
  openDialog: Function
});


</script>

<template>
  <div class="overflow-x-auto w-full">
    <!-- 🌀 Загрузка -->
    <div v-if="loading" class="card border border-surface rounded p-6 w-full">
      <div class="font-semibold text-xl mb-4">Загрузка данных...</div>
      <div v-for="n in size" :key="n" class="mb-4">
        <div class="flex space-x-4">
          <Skeleton width="10rem" class="mb-2" />
          <Skeleton height=".5rem" class="flex-1" v-for="i in 6" :key="i" />
        </div>
      </div>
    </div>

    <div v-else-if="routesData.length === 0" class="w-full text-center py-8 text-gray-500">
      <i class="pi pi-info-circle mr-2" />
          No data to display. Check the filters.
    </div>

    <DataTable
      v-else
      :value="routesData"
      class="min-w-max"
      scrollable
      scrollDirection="horizontal"
    >
      <Column field="date" header="Дата" frozen alignFrozen="left" style="min-width: 140px">
        <template #body="slotProps">
            <div
                @click="openTripsDialog(slotProps.data[aggregator], aggregator, slotProps.data.route)"
                :class="[
                'rounded p-2 transition-colors duration-300',
                slotProps.data[aggregator] && slotProps.data[aggregator].count > 0
                  ? 'cursor-pointer hover:bg-primary-100 dark:hover:bg-primary-900'
                  : 'cursor-default'
              ]"
            >
              <template v-if="slotProps.data[aggregator]">
                <div class="text-sm mb-1 font-semibold">
                  📊 {{ slotProps.data[aggregator].count }} сегм.
                </div>

                <div class="text-xs mb-1 text-surface-600 dark:text-surface-400">
                  <template v-if="slotProps.data[aggregator].min === slotProps.data[aggregator].max">
                    {{ formatPrice(slotProps.data[aggregator].min, slotProps.data[aggregator].currency) }}
                  </template>
                  <template v-else>
                    {{ formatPrice(slotProps.data[aggregator].min, slotProps.data[aggregator].currency) }}
                    —
                    {{ formatPrice(slotProps.data[aggregator].max, slotProps.data[aggregator].currency) }}
                  </template>
                </div>

                <div class="text-sm">
                  Медиана:
                  <span class="text-primary-600 dark:text-primary-400 font-bold">
                    {{ formatPrice(slotProps.data[aggregator].median, slotProps.data[aggregator].currency) }}
                  </span>
                </div>
              </template>

              <template v-else>
                <div class="text-sm text-gray-400 italic">Нет данных</div>
              </template>
            </div>
          </template>
      </Column>

      <Column
        v-for="(name, aggregatorId) in aggregators"
        :key="aggregatorId"
        :field="aggregatorId"
        :header="name"
      >
        <template #body="slotProps">
          <div
            @click="() => {
              const cell = slotProps.data[aggregatorId];
              if (cell && (cell.ourCount > 0 || cell.competitorCount > 0)) {
                props.openDialog({
                  routeId: cell.id,
                  date: slotProps.data.date,
                  aggregator: aggregatorId
                });
              }
            }"
            :class="[
              'rounded p-2 transition-colors duration-300',
              slotProps.data[aggregatorId] &&
              !(slotProps.data[aggregatorId].ourCount === 0 &&
                slotProps.data[aggregatorId].competitorCount === 0)
                ? 'cursor-pointer hover:bg-primary-100 dark:hover:bg-primary-900'
                : 'cursor-default'
            ]"
          >
            <template v-if="slotProps.data[aggregatorId]">
              <div
                v-if="slotProps.data[aggregatorId].ourCount === 0"
                class="text-sm text-gray-400 font-bold"
              >
                ⛔️ LikeBus не найден
              </div>
              <div v-else class="text-sm mb-1">
                🟢 {{ slotProps.data[aggregatorId].ourCount }} сегментов
                <span class="text-primary-600 dark:text-primary font-bold">
                  <template v-if="slotProps.data[aggregatorId].ourMin === slotProps.data[aggregatorId].ourMax">
                    ({{ formatPrice(slotProps.data[aggregatorId].ourMin, slotProps.data[aggregatorId].currency) }})
                  </template>
                  <template v-else>
                    ({{ formatPrice(slotProps.data[aggregatorId].ourMin, slotProps.data[aggregatorId].currency) }} -
                     {{ formatPrice(slotProps.data[aggregatorId].ourMax, slotProps.data[aggregatorId].currency) }})
                  </template>
                </span>
              </div>

              <div
                v-if="slotProps.data[aggregatorId].competitorCount === 0"
                class="text-sm text-gray-400"
              >
                ⚠️ Конкуренты не найдены
              </div>
              <div v-else class="text-sm mb-1">
                🔴 {{ slotProps.data[aggregatorId].competitorCount }} конкурентов
              </div>
              <div class="text-sm">
                📊 мин:
                <span class="text-blue-700 dark:text-blue-300 font-bold">
                  {{ formatPrice(slotProps.data[aggregatorId].competitorMin, slotProps.data[aggregatorId].currency) }}
                </span> |
                мед:
                <span class="text-orange-500 dark:text-yellow-400 font-bold">
                  {{ formatPrice(slotProps.data[aggregatorId].median, slotProps.data[aggregatorId].currency) }}
                </span> |
                макс:
                <span class="text-red-700 dark:text-red-400 font-bold">
                  {{ formatPrice(slotProps.data[aggregatorId].competitorMax, slotProps.data[aggregatorId].currency) }}
                </span>
              </div>
            </template>

            <template v-else>
              <div class="text-sm text-gray-400 italic">Нет данных</div>
            </template>
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
</template>
