from app.backend.settings import Base

CeleryScheduleModel = Base.classes.celery_crontabschedule
CeleryTasksModel = Base.classes.celery_periodictask
