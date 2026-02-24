<script setup>
import {formatPrice} from "@/service/currencyUtils";
import {useRouter} from 'vue-router';

const router = useRouter();

function goToSegment(row) {
  const query = {
    fromCityId: row.fromCityId,
    toCityId: row.toCityId,
    departureTimeFrom: props.departureTimeFrom,
    departureTimeTo: props.departureTimeTo,
    arrivalTimeFrom: props.arrivalTimeFrom,
    arrivalTimeTo: props.arrivalTimeTo,
    siteIds: props.selectedSites?.join(',')
  };

  if (props.isTransfer !== null) {
    query.isTransfer = props.isTransfer;
  }

  router.push({
    name: 'RouteBySegmentPage',
    query
  });
}


const props = defineProps({
  routesData: Array,
  cities: Object,
  aggregators: Object,
  openTripsDialog: Function,
  loading: Boolean,
  size: Number,
  departureTimeFrom: String,
  departureTimeTo: String,
  arrivalTimeFrom: String,
  arrivalTimeTo: String,
  isTransfer: [Boolean, null],
  selectedSites: Array
});
</script>

<template>
  <div class="overflow-x-auto w-full">
    <div v-if="loading" class="card border border-surface rounded p-6 w-full">
      <div class="font-semibold text-xl mb-4">Загрузка данных...</div>
      <div v-for="n in size" :key="n" class="mb-4">
        <div class="flex space-x-4">
          <Skeleton width="10rem" class="mb-2"/>
          <Skeleton height=".5rem" class="flex-1" v-for="i in 6" :key="i"/>
        </div>
      </div>
    </div>

    <DataTable v-else :value="routesData" class="min-w-max" scrollable scrollDirection="horizontal" >
      <Column field="route" header="Сегмент" frozen alignFrozen="left" style="min-width: 200px">
        <template #body="slotProps">
        <router-link
            :to="{
              name: 'RouteBySegmentPage',
              query: {
                fromCityId: slotProps.data.fromCityId,
                toCityId: slotProps.data.toCityId,
                departureTimeFrom: props.departureTimeFrom,
                departureTimeTo: props.departureTimeTo,
                arrivalTimeFrom: props.arrivalTimeFrom,
                arrivalTimeTo: props.arrivalTimeTo,
                ...(props.isTransfer !== null ? { isTransfer: props.isTransfer } : {}),
                siteIds: props.selectedSites?.join(',')
              }
            }"
            class="text-primary-700 hover:underline cursor-pointer font-semibold"
          >
            {{ slotProps.data.route }}
          </router-link>

        </template>
      </Column>
      <Column
        v-for="aggregator in Object.keys(routesData[0] || {}).filter((key) => !['route', 'fromCityId', 'toCityId'].includes(key))"
        :key="aggregator"
        :field="aggregator"
        :header="aggregator"
      >
        <template #body="slotProps">
          <div
              @click="openTripsDialog(slotProps.data[aggregator], aggregator, slotProps.data.route)"
              :class="[
              'rounded p-2 transition-colors duration-300',
              slotProps.data[aggregator] && !(slotProps.data[aggregator].ourCount === 0 && slotProps.data[aggregator].competitorCount === 0)
                ? 'cursor-pointer hover:bg-primary-100 dark:hover:bg-primary-900'
                : 'cursor-default'
            ]"
          >
            <template v-if="slotProps.data[aggregator]">
              <div v-if="slotProps.data[aggregator].ourCount === 0" class="text-sm text-gray-400 font-bold">
                ⛔️ LikeBus не найден
              </div>
              <div v-else class="text-sm mb-1">
                🟢 {{ slotProps.data[aggregator].ourCount }} сегментов
                <span class="text-primary-600 dark:text-primary font-bold">
                  <template v-if="slotProps.data[aggregator].ourMin === slotProps.data[aggregator].ourMax">
                    ({{ formatPrice(slotProps.data[aggregator].ourMin, slotProps.data[aggregator].currency) }})
                  </template>
                  <template v-else>
                    ({{ formatPrice(slotProps.data[aggregator].ourMin, slotProps.data[aggregator].currency) }} -
                    {{ formatPrice(slotProps.data[aggregator].ourMax, slotProps.data[aggregator].currency) }})
                  </template>
                </span>
              </div>

              <div
                  v-if="slotProps.data[aggregator].competitorCount === 0"
                  class="text-sm text-gray-400"
              >
                ⚠️ Конкуренты не найдены
              </div>
              <div v-else class="text-sm mb-1">
                🔴 {{ slotProps.data[aggregator].competitorCount }} конкурентов
              </div>

              <div class="text-sm">
                📊 мин:
                <span class="text-blue-700 dark:text-blue-300 font-bold">
                  {{ formatPrice(slotProps.data[aggregator].competitorMin, slotProps.data[aggregator].currency) }}
                </span>
                |
                мед:
                <span class="text-orange-500 dark:text-yellow-400 font-bold">
                  {{ formatPrice(slotProps.data[aggregator].median, slotProps.data[aggregator].currency) }}
                </span>
                |
                макс:
                <span class="text-red-700 dark:text-red-400 font-bold">
                  {{ formatPrice(slotProps.data[aggregator].competitorMax, slotProps.data[aggregator].currency) }}
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

