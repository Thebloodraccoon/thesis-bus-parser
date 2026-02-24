from backend.app.settings import settings

SiteModel = settings.ScraperBase.classes.sites
CityModel = settings.ScraperBase.classes.cities
RouteModel = settings.ScraperBase.classes.routes
TripHistoryModel = settings.ScraperBase.classes.trip_history
TripModel = settings.ScraperBase.classes.trips
CeleryScheduleModel = settings.ScraperBase.classes.celery_crontabschedule
CeleryTasksModel = settings.ScraperBase.classes.celery_periodictask
