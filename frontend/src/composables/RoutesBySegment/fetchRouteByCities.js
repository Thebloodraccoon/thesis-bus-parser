import apiClient from '@/api/axios'

export async function fetchRouteByCities({
  fromCityId,
  toCityId,
  departureDates,
  departureTimeFrom = '00:00',
  departureTimeTo = '23:59',
  arrivalTimeFrom = '00:00',
  arrivalTimeTo = '23:59',
  isTransfer = null,
  siteIds = []
}) {
  if (!fromCityId || !toCityId) {
    throw new Error('fromCityId и toCityId являются обязательными')
  }

  const params = new URLSearchParams()

params.append('from_city_id', fromCityId)
params.append('to_city_id', toCityId)

departureDates.forEach(date => {
  params.append('departure_dates', date)
})

params.append('departure_time_from', departureTimeFrom)
params.append('departure_time_to', departureTimeTo)
params.append('arrival_time_from', arrivalTimeFrom)
params.append('arrival_time_to', arrivalTimeTo)

if (isTransfer !== null) {
  params.append('is_transfer', isTransfer)
}

siteIds.forEach(id => {
  params.append('sites', id)
})

const { data } = await apiClient.get('/scraper/routes/route-by-cities', {
  params
})
  return data
}
