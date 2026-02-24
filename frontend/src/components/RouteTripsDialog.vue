<script setup>
import { ref, watch } from 'vue';
import Dialog from 'primevue/dialog';
import apiClient from '@/api/axios';
import { useToast } from 'primevue/usetoast';
import { formatDate } from '@/service/dateUtils';
import {currencySymbol, formatPrice} from "@/service/currencyUtils";

const props = defineProps({
  visible: Boolean,
  routeId: Number,
  departureTimeFrom: String,
  departureTimeTo: String,
  arrivalTimeFrom: String,
  arrivalTimeTo: String,
  isTransfer: Boolean,
  aggregatorName: String,
  CitiesName: String,
  selectedDate: [Date, String]
});


const emit = defineEmits(['update:visible']);

const toast = useToast();
const loading = ref(false);
const tripsData = ref({ our_trips: [], competitor_trips: [] });

const fetchTrips = async () => {
    if (!props.routeId) return;
    loading.value = true;
    try {
        const params = {
            route_id: props.routeId
        };

        if (props.departureTimeFrom) params.departure_time_from = props.departureTimeFrom;
        if (props.departureTimeTo) params.departure_time_to = props.departureTimeTo;
        if (props.arrivalTimeFrom) params.arrival_time_from = props.arrivalTimeFrom;
        if (props.arrivalTimeTo) params.arrival_time_to = props.arrivalTimeTo;
        if (props.isTransfer) params.is_transfer = true;

        const { data } = await apiClient.get('/scraper/routes/trips/', {
            params,
            paramsSerializer: (params) => {
                const searchParams = new URLSearchParams();
                Object.keys(params).forEach((key) => {
                    searchParams.append(key, params[key]);
                });
                return searchParams.toString();
            }
        });

        tripsData.value = data;
    } catch (err) {
        toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось загрузить маршруты', life: 3000 });
    } finally {
        loading.value = false;
    }
};

watch(
    () => props.visible,
    (val) => {
        if (val) fetchTrips();
    }
);

const formatDateTime = (dateStr, timeStr) => {
    if (!dateStr || !timeStr) return '-';
    const [year, month, day] = dateStr.split('-');
    const [hour, minute] = timeStr.split(':');
    return {
        date: `${day}.${month}`,
        time: `${hour}:${minute}`
    };
};
</script>

<template>
    <Dialog :draggable="false" :visible="props.visible" @update:visible="emit('update:visible', $event)" modal :header="`Детали сегмента: ${props.CitiesName}`" :style="{ width: '98vw', height: '100vh', backgroundColor: '#262626' }">
        <p class="m-1">
          Дата отправления:
          <strong>{{ formatDate(props.selectedDate, { showTime: false, showSeconds: false }) }}</strong>
        </p>
        <p class="m-1">
            Агент:
            <strong>{{ props.aggregatorName }}</strong>
        </p>
        <p class="m-1">
            Время отправления:
            <strong>{{ props.departureTimeFrom }}</strong> —
            <strong>{{ props.departureTimeTo }}</strong>
        </p>
        <p class="m-1">
            Время прибытия:
            <strong>{{ props.arrivalTimeFrom }}</strong> —
            <strong>{{ props.arrivalTimeTo }}</strong>
        </p>
        <p class="m-1" v-if="props.isTransfer !== null">
            Тип маршрута:
            <strong>
                {{ props.isTransfer ? 'Только пересадочные' : 'Только прямые' }}
            </strong>
        </p>
        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 class="text-lg font-semibold mb-2">🟢 Наши сегменты</h3>
              <div class="space-y-3">
                <Skeleton width="100%" height="2rem" v-for="n in 6" :key="n" />
              </div>
            </div>
            <div>
              <h3 class="text-lg font-semibold mb-2">🔴 Сегменты конкурентов</h3>
              <div class="space-y-3">
                <Skeleton width="100%" height="2rem" v-for="n in 6" :key="n" />
              </div>
            </div>
          </div>


        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Наши маршруты -->
            <div>
                <h3 class="text-lg font-semibold mb-2">🟢 Наши сегменты ({{ tripsData.our_trips.length }})</h3>
                <DataTable
                  v-if="tripsData.our_trips.length"
                  :value="tripsData.our_trips"
                  scrollable
                  scrollHeight="65vh"
                >
                    <Column header="Отпр." :sortable="true" sortField="departure_time">
                        <template #body="{ data }">
                            <div>
                                <span>{{ formatDateTime(data.departure_date, data.departure_time).date }}, </span>
                                <strong>{{ formatDateTime(data.departure_date, data.departure_time).time }}</strong>
                            </div>
                        </template>
                    </Column>
                    <Column header="Приб." :sortable="true" sortField="arrival_time">
                        <template #body="{ data }">
                            <span>{{ formatDateTime(data.arrival_date, data.arrival_time).date }}, </span>
                            <strong>{{ formatDateTime(data.arrival_date, data.arrival_time).time }}</strong>
                        </template>
                    </Column>

                    <Column field="from_station" header="Откуда" />
                    <Column field="to_station" header="Куда" />
                    <Column field="price" header="Цена" sortable>
                      <template #body="{ data }">
                        <span class="whitespace-nowrap">
                          {{ formatPrice(data.price, currencySymbol(data.currency)) }}
                        </span>
                      </template>
                    </Column>
                    <Column header="Тип маршрута">
                          <template #body="{ data }">
                              <span v-if="data.is_transfer">Пересадочный</span>
                              <span v-else>Прямой</span>
                          </template>
                      </Column>
                    <Column field="available_seats" header="Дост. мест" style="width: 5px" sortable />
                    <Column header="Акту." class="text-gray-400">
                        <template #body="{ data }">
                            {{ formatDate(data.price_updated_at, {showSeconds: false, showYear: false}) }}
                        </template>
                    </Column>
                </DataTable>
                <div v-else class="text-gray-400 italic">Нет данных</div>
            </div>

            <!-- Маршруты конкурентов -->
            <div>
                <h3 class="text-lg font-semibold mb-2">🔴 Сегменты конкурентов ({{ tripsData.competitor_trips.length }})</h3>
                <DataTable v-if="tripsData.competitor_trips.length" :value="tripsData.competitor_trips" scrollable scrollHeight="65vh">
                    <Column header="Отпр." :sortable="true" sortField="departure_time">
                        <template #body="{ data }">
                            <div>
                                <span>{{ formatDateTime(data.departure_date, data.departure_time).date }}, </span>
                                <strong>{{ formatDateTime(data.departure_date, data.departure_time).time }}</strong>
                            </div>
                        </template>
                    </Column>

                    <Column header="Приб." :sortable="true" sortField="arrival_time">
                        <template #body="{ data }">
                            <span>{{ formatDateTime(data.arrival_date, data.arrival_time).date }}, </span>
                            <strong>{{ formatDateTime(data.arrival_date, data.arrival_time).time }}</strong>
                        </template>
                    </Column>

                    <Column field="from_station" header="Откуда" />
                    <Column field="to_station" header="Куда" />
                    <Column field="price" header="Цена" sortable>
                      <template #body="{ data }">
                        <span class="whitespace-nowrap">
                          {{ formatPrice(data.price, currencySymbol(data.currency)) }}
                        </span>
                      </template>
                    </Column>
                    <Column field="carrier_name" header="Перевозчик" />

                    <Column header="Тип маршрута">
                        <template #body="{ data }">
                            <span v-if="data.is_transfer">Пересадочный</span>
                            <span v-else>Прямой</span>
                        </template>
                    </Column>

                    <Column field="available_seats" header="Дост. мест" style="width: 10px" sortable />

                    <Column header="Акту." class="text-gray-400">
                        <template #body="{ data }">
                            {{ formatDate(data.price_updated_at, {showSeconds: false, showYear: false}) }}
                        </template>
                    </Column>
                </DataTable>
                <div v-else class="text-gray-400 italic">Нет данных</div>
            </div>
        </div>
    </Dialog>
</template>
