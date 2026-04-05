import json
import secrets
import string
from datetime import date, datetime, time, timedelta, timezone
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

from fastapi_mail import MessageSchema, FastMail
from sqlalchemy import and_, desc, func, select, text
from sqlalchemy.orm import Session, aliased

from thesis.backend.app.auth import AuthService
from thesis.backend.app.conf import settings, AutomapBase
from thesis.backend.app.exceptions import (
    CityNotFoundException,
    CitiesNotFoundException,
    DuplicatePresetNameException,
    FiltersPresetNotFoundException,
    ScheduleNotFoundException,
    SiteNotFoundException,
    SitesNotFoundException,
    TaskAlreadyExistsException,
    TaskNotFoundException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from thesis.backend.app.schemas import (
    CitySchema,
    FilterPreset,
    FilterPresetCreate,
    FilterPresetUpdate,
    RouteSchema,
    ScheduleCreate,
    ScheduleUpdate,
    SiteCreate,
    SiteUpdate,
    TaskBase,
    TaskResponse,
    TripSchema,
    TripSchemaResponse,
    UserCreate,
    UserResponse,
)
from thesis.core.models import (
    CityModel,
    RouteModel,
    SiteModel,
    TripHistoryModel,
    TripModel,
    User,
)


# Lazy import Celery models (automap, available after DB prepare)
def _celery_models():
    schedule_model = AutomapBase.classes.celery_crontabschedule
    task_model = AutomapBase.classes.celery_periodictask
    return schedule_model, task_model


ModelT = TypeVar("ModelT")


# Base repository
class BaseRepository(Generic[ModelT]):
    """
    A basic repository with typical CRUD operations.
    Subclasses set the 'model' attribute and extend as needed.
    """

    model: Type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, record_id: int) -> ModelT:
        obj = self.db.query(self.model).filter(self.model.id == record_id).first()
        if not obj:
            raise self._not_found_exception(record_id)
        return obj

    def get_all(self) -> List[ModelT]:
        return self.db.query(self.model).all()

    def delete(self, record_id: int) -> None:
        obj = self.get_by_id(record_id)
        self.db.delete(obj)
        self.db.commit()

    def _not_found_exception(self, record_id: int):
        raise NotImplementedError


# Cache service
class CacheService:
    """A common service for working with Redis cache."""

    @staticmethod
    def _serialize(data: Any) -> Any:
        if isinstance(data, list):
            return [CacheService._serialize(item) for item in data]
        if hasattr(data, "__dict__"):
            d = {
                k: CacheService._serialize(v)
                for k, v in data.__dict__.items()
                if k != "_sa_instance_state"
            }
            return d
        if isinstance(data, dict):
            return {k: CacheService._serialize(v) for k, v in data.items()}
        if isinstance(data, datetime):
            return data.isoformat()
        return data

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        async with settings.get_redis() as redis:
            cached = await redis.get(key)
            return json.loads(cached) if cached else None

    @staticmethod
    async def set(key: str, data: Any, expiration: timedelta) -> None:
        serialized = CacheService._serialize(data)
        async with settings.get_redis() as redis:
            await redis.setex(
                key, int(expiration.total_seconds()), json.dumps(serialized)
            )

    @staticmethod
    async def delete(key: str) -> None:
        async with settings.get_redis() as redis:
            await redis.delete(key)


# User service
class UserService(BaseRepository[User]):
    """User management: registration, search, update, deletion."""

    model = User

    def _not_found_exception(self, record_id: int):
        return UserNotFoundException(user_id=record_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self) -> List[User]:
        return self.db.query(User).all()

    async def create(self, data: UserCreate) -> UserResponse:
        if self.get_by_email(data.email):
            raise UserAlreadyExistsException(str(data.email))

        password = self._generate_password()
        new_user = User(
            email=data.email,
            hashed_password=AuthService.hash_password(password),
            role=data.role,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        await self._send_credentials(data.email, password)
        return UserResponse.model_validate(new_user)

    def update(self, user_id: int, updates: dict) -> UserResponse:
        user = self.get_by_id(user_id)
        updates["updated_at"] = datetime.now(timezone.utc)
        for field, value in updates.items():
            if hasattr(user, field):
                setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return UserResponse.model_validate(user)

    def update_last_login(self, user: User) -> None:
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)

    @staticmethod
    def _generate_password(length: int = 12) -> str:
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        return "".join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    async def _send_credentials(email: str, password: str) -> None:
        msg = MessageSchema(
            subject="Account credentials",
            recipients=[email],
            body=f"Your account has been created.\n\nEmail: {email}\nPassword: {password}",
            subtype="plain",
        )
        await FastMail(settings.mail_conf).send_message(msg)


# Site service
_SITE_CACHE_TTL = timedelta(hours=1)


class SiteService(BaseRepository[SiteModel]):
    """Management of agent sites with Redis caching of the list."""

    model = SiteModel

    def _not_found_exception(self, record_id: int):
        return SiteNotFoundException(id=record_id)

    def _cache_key(self, is_active: Optional[bool]) -> str:
        return f"sites:all:{is_active}"

    def get_all_filtered(self, is_active: Optional[bool] = None) -> List[SiteModel]:
        q = self.db.query(SiteModel)
        if is_active is not None:
            q = q.filter(SiteModel.is_active == is_active)
        return q.all()

    def get_by_name(self, name: str) -> SiteModel:
        site = self.db.query(SiteModel).filter(SiteModel.name == name).first()
        if not site:
            raise SiteNotFoundException(name=name)
        return site

    def get_ids_in_list(self, ids: List[int]) -> List[int]:
        if not ids:
            return []
        stmt = select(SiteModel.id).where(SiteModel.id.in_(ids))
        return list(self.db.execute(stmt).scalars().all())

    async def get_cached(self, is_active: Optional[bool] = None) -> List[dict]:
        key = self._cache_key(is_active)
        cached = await CacheService.get(key)
        if cached is not None:
            return cached
        sites = self.get_all_filtered(is_active)
        serialized = CacheService._serialize(sites)
        await CacheService.set(key, serialized, _SITE_CACHE_TTL)
        return serialized

    async def invalidate_cache(self) -> None:
        for state in ("None", "True", "False"):
            await CacheService.delete(f"sites:all:{state}")

    def create(self, data: SiteCreate) -> SiteModel:
        site = SiteModel(name=data.name, url=data.url, is_active=data.is_active)
        self.db.add(site)
        self.db.commit()
        self.db.refresh(site)
        return site

    def update(self, site_id: int, data: SiteUpdate) -> SiteModel:
        site = self.get_by_id(site_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(site, key, value)
        self.db.commit()
        self.db.refresh(site)
        return site


# City service
_CITY_CACHE_KEY = "cities:"
_CITY_CACHE_TTL = timedelta(days=1)


class CityService(BaseRepository[CityModel]):
    """Directory of cities with long-term redis caching."""

    model = CityModel

    def _not_found_exception(self, record_id: int):
        return CityNotFoundException(record_id)

    def get_all(self) -> List[CitySchema]:
        cities = self.db.execute(select(CityModel)).scalars().all()
        return [
            CitySchema(
                id=c.id, name_en=c.name_en, name_ua=c.name_ua, like_bus_id=c.like_bus_id
            )
            for c in cities
        ]

    def get_ids_in_list(self, ids: List[int]) -> List[int]:
        if not ids:
            return []
        stmt = select(CityModel.id).where(CityModel.id.in_(ids))
        return list(self.db.execute(stmt).scalars().all())

    async def get_cached(self) -> List[CitySchema]:
        cached = await CacheService.get(_CITY_CACHE_KEY)
        if cached:
            return cached
        cities = self.get_all()
        await CacheService.set(_CITY_CACHE_KEY, cities, _CITY_CACHE_TTL)
        return cities

    async def refresh_cache(self) -> None:
        await CacheService.delete(_CITY_CACHE_KEY)
        await self.get_cached()


# Schedule service
class ScheduleService:
    """Managing Celery schedules (crontab)."""

    def __init__(self, db: Session):
        self.db = db
        self.ScheduleModel, _ = _celery_models()

    def get_by_id(self, schedule_id: int):
        obj = (
            self.db.query(self.ScheduleModel)
            .filter(self.ScheduleModel.id == schedule_id)
            .first()
        )
        if not obj:
            raise ScheduleNotFoundException(schedule_id)
        return obj

    def create(self, data: ScheduleCreate):
        obj = self.ScheduleModel(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, schedule_id: int, data: ScheduleUpdate):
        obj = self.get_by_id(schedule_id)
        update_data = {
            k: v for k, v in data.model_dump(exclude_unset=True).items() if v != ""
        }
        for k, v in update_data.items():
            setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        self._touch_celery_cache()
        return obj

    def delete(self, schedule_id: int) -> None:
        obj = self.get_by_id(schedule_id)
        self.db.delete(obj)
        self.db.commit()

    def _touch_celery_cache(self) -> None:
        self.db.execute(
            text("UPDATE celery_periodictaskchanged SET last_update = NOW()")
        )
        self.db.commit()


# Task service
class TaskService:
    """Celery Task Management: Parsing on a Schedule."""

    def __init__(self, db: Session):
        self.db = db
        self.schedule_svc = ScheduleService(db)
        self.site_svc = SiteService(db)
        _, self.TaskModel = _celery_models()

    @staticmethod
    def _build_args(data: TaskBase) -> str:
        return json.dumps(
            [
                data.site_name,
                data.start_date,
                data.end_date,
                data.threads,
                data.max_duration_seconds,
            ]
        )

    @staticmethod
    def _parse_args(task) -> tuple:
        try:
            args = json.loads(task.args)
            return args[0], args[1], args[2], args[3], args[4]
        except Exception as e:
            raise e

    @staticmethod
    def _parse_cron_weekdays(day_of_week: str) -> List[int]:
        if not day_of_week or day_of_week == "*":
            return list(range(7))
        result: Set[int] = set()
        for part in day_of_week.split(","):
            part = part.strip()
            if part.startswith("*/"):
                try:
                    result.update(range(0, 7, int(part[2:])))
                except ValueError:
                    continue
            elif "-" in part:
                try:
                    start, end = map(int, part.split("-"))
                    result.update(range(max(0, start), min(6, end) + 1))
                except ValueError:
                    continue
            else:
                try:
                    d = int(part)
                    if 0 <= d <= 6:
                        result.add(d)
                except ValueError:
                    continue
        return sorted(result)

    def _build_schedule_data(
        self, data: TaskBase, is_create: bool = True
    ) -> Union[ScheduleCreate, ScheduleUpdate]:
        day_of_week = ",".join(map(str, data.weekdays)) if data.weekdays else "*"
        kwargs = {
            "minute": data.minute,
            "hour": data.hour,
            "day_of_month": "*",
            "month_of_year": "*",
            "day_of_week": day_of_week,
        }
        return ScheduleCreate(**kwargs) if is_create else ScheduleUpdate(**kwargs)

    def _serialize(self, task) -> Optional[TaskResponse]:
        schedule = self.schedule_svc.get_by_id(task.schedule_id)
        if not schedule:
            return None
        site_name, start_date, end_date, threads, max_dur = self._parse_args(task)
        site_id = None
        if site_name:
            site = self.site_svc.get_by_name(site_name)
            site_id = int(site.id)
        return TaskResponse(
            id=task.id,
            name=task.name,
            enabled=task.enabled,
            last_run_at=task.last_run_at,
            total_run_count=task.total_run_count,
            schedule_id=task.schedule_id,
            site_id=site_id,
            start_date=start_date or 0,
            end_date=end_date or 0,
            threads=threads or 5,
            max_duration_seconds=max_dur or 86400,
            minute=schedule.minute,
            hour=schedule.hour,
            weekdays=self._parse_cron_weekdays(schedule.day_of_week),
        )

    def _get_by_id(self, task_id: int):
        obj = self.db.query(self.TaskModel).filter(self.TaskModel.id == task_id).first()
        if not obj:
            raise TaskNotFoundException(task_id)
        return obj

    def _get_by_name(self, name: str):
        return self.db.query(self.TaskModel).filter(self.TaskModel.name == name).first()

    def _commit_refresh(self, task) -> Optional[TaskResponse]:
        self.db.commit()
        self.db.refresh(task)
        self.schedule_svc._touch_celery_cache()
        return self._serialize(task)

    def get_all(self) -> List[TaskResponse]:
        tasks = (
            self.db.query(self.TaskModel)
            .filter(self.TaskModel.queue == "parsing")
            .all()
        )
        return list(filter(None, map(self._serialize, tasks)))

    def create(self, data: TaskBase) -> Optional[TaskResponse]:
        self.site_svc.get_by_name(data.site_name)
        name = data.task_name.strip().replace(" ", "_")
        if self._get_by_name(name):
            raise TaskAlreadyExistsException(name)

        schedule = self.schedule_svc.create(
            self._build_schedule_data(data, is_create=True)
        )
        task = self.TaskModel(
            name=name,
            task="app.managers.task.run_single_parser",
            enabled=data.enabled,
            args=self._build_args(data),
            kwargs=json.dumps({}),
            headers=json.dumps({}),
            last_run_at=None,
            total_run_count=0,
            one_off=False,
            queue="parsing",
            discriminator="crontabschedule",
            schedule_id=schedule.id,
        )
        self.db.add(task)
        return self._commit_refresh(task)

    def update(self, task_id: int, data: TaskBase) -> Optional[TaskResponse]:
        task = self._get_by_id(task_id)
        self.site_svc.get_by_name(data.site_name)
        name = data.task_name.strip().replace(" ", "_")
        if name != task.name and self._get_by_name(name):
            raise TaskAlreadyExistsException(name)

        self.schedule_svc.update(
            task.schedule_id, self._build_schedule_data(data, is_create=False)
        )
        task.name = name
        task.enabled = data.enabled
        task.args = self._build_args(data)
        return self._commit_refresh(task)

    def delete(self, task_id: int) -> None:
        task = self._get_by_id(task_id)
        self.schedule_svc.delete(task.schedule_id)
        self.db.delete(task)
        self.db.commit()


# Filter preset service (Redis-based, no SQL)
class FilterPresetService:
    """Preset filters are stored in Redis without a table in the database."""

    def __init__(self, db: Session):
        self.city_svc = CityService(db)
        self.site_svc = SiteService(db)

    @staticmethod
    def _preset_key(user_id: int, preset_id: str) -> str:
        return f"user:{user_id}:filter_preset:{preset_id}"

    @staticmethod
    def _presets_set_key(user_id: int) -> str:
        return f"user:{user_id}:filter_presets"

    def _validate_cities(self, ids: Optional[List[int]]) -> None:
        if not ids:
            return
        existing = set(self.city_svc.get_ids_in_list(ids))
        missing = set(ids) - existing
        if missing:
            raise CitiesNotFoundException(missing)

    def _validate_sites(self, ids: Optional[List[int]]) -> None:
        if not ids:
            return
        existing = set(self.site_svc.get_ids_in_list(ids))
        missing = set(ids) - existing
        if missing:
            raise SitesNotFoundException(missing)

    async def _is_name_duplicate(
        self, user_id: int, name: str, exclude_id: Optional[str] = None
    ) -> bool:
        presets = await self.get_all(user_id) or []
        return any(
            p.name == name and (exclude_id is None or p.id != exclude_id)
            for p in presets
        )

    async def get_all(self, user_id: int) -> List[FilterPreset]:
        presets = []
        async with settings.get_redis() as redis:
            preset_ids = await redis.smembers(self._presets_set_key(user_id))
            for pid in preset_ids:
                data = await redis.get(self._preset_key(user_id, pid))
                if data:
                    presets.append(FilterPreset(**json.loads(data)))
        return presets

    async def create(self, user_id: int, data: FilterPresetCreate) -> FilterPreset:
        if await self._is_name_duplicate(user_id, data.name):
            raise DuplicatePresetNameException()
        self._validate_cities(data.from_cities)
        self._validate_cities(data.to_cities)
        self._validate_sites(data.sites)

        preset = FilterPreset(**data.model_dump())
        async with settings.get_redis() as redis:
            await redis.set(
                self._preset_key(user_id, preset.id),
                json.dumps(preset.model_dump(), cls=_TimeEncoder),
            )
            await redis.sadd(self._presets_set_key(user_id), preset.id)
        return preset

    async def update(
        self, user_id: int, preset_id: str, data: FilterPresetUpdate
    ) -> FilterPreset:
        if data.name and await self._is_name_duplicate(
            user_id, data.name, exclude_id=preset_id
        ):
            raise DuplicatePresetNameException()

        async with settings.get_redis() as redis:
            raw = await redis.get(self._preset_key(user_id, preset_id))
            if not raw:
                raise FiltersPresetNotFoundException()

            preset = FilterPreset(**json.loads(raw))
            update_data = data.model_dump(exclude_unset=True)

            if "from_cities" in update_data:
                self._validate_cities(update_data["from_cities"])
            if "to_cities" in update_data:
                self._validate_cities(update_data["to_cities"])
            if "sites" in update_data:
                self._validate_sites(update_data["sites"])

            for field, value in update_data.items():
                setattr(preset, field, value)

            await redis.set(
                self._preset_key(user_id, preset_id),
                json.dumps(preset.model_dump(), cls=_TimeEncoder),
            )
        return preset

    async def delete(self, user_id: int, preset_id: str) -> None:
        async with settings.get_redis() as redis:
            if not await redis.exists(self._preset_key(user_id, preset_id)):
                raise FiltersPresetNotFoundException()
            await redis.srem(self._presets_set_key(user_id), preset_id)
            await redis.delete(self._preset_key(user_id, preset_id))


class _TimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.strftime("%H:%M")
        return super().default(obj)


# Route service
class RouteService:
    """
    Complex SQL queries for routes and flights.
    Encapsulates all the logic of working with RouteModel, TripModel, TripHistoryModel.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_all_routes(
            self,
            departure_date: date,
            page: int = 1,
            size: int = 20,
            from_city_ids: Optional[List[int]] = None,
            to_city_ids: Optional[List[int]] = None,
            departure_time_from: Optional[time] = None,
            departure_time_to: Optional[time] = None,
            arrival_time_from: Optional[time] = None,
            arrival_time_to: Optional[time] = None,
            sites: Optional[List[int]] = None,
            is_transfer: Optional[bool] = None,
    ) -> Dict[str, Any]:
        available_sites = self._normalize_sites(sites)
        existing_sites = self._get_existing_site_ids(available_sites)
        unique_routes, total = self._get_unique_routes(
            departure_date, page, size, from_city_ids, to_city_ids
        )

        items = []
        for row in unique_routes:
            entry = self._make_route_entry(
                row.from_city_id,
                row.to_city_id,
                departure_date,
                available_sites,
                existing_sites,
            )
            routes = self._get_routes_data(
                departure_date,
                row.from_city_id,
                row.to_city_id,
                available_sites,
                departure_time_from,
                departure_time_to,
                arrival_time_from,
                arrival_time_to,
                is_transfer,
            )
            for site_id, route_obj in routes.items():
                entry["agents"][str(site_id)] = route_obj
            items.append(entry)

        return {"total": total, "page": page, "size": size, "items": items}

    def get_route_by_cities(
            self,
            departure_dates: List[date],
            from_city_id: int,
            to_city_id: int,
            departure_time_from: Optional[time] = None,
            departure_time_to: Optional[time] = None,
            arrival_time_from: Optional[time] = None,
            arrival_time_to: Optional[time] = None,
            sites: Optional[List[int]] = None,
            is_transfer: Optional[bool] = None,
    ) -> Dict[str, Any]:
        available_sites = self._normalize_sites(sites)
        existing_sites_str: Set[str] = {
            str(s) for s in self._get_existing_site_ids(available_sites)
        }

        result: Dict[str, Any] = {
            "from_city": from_city_id,
            "to_city": to_city_id,
            "agents": {},
        }
        date_strings = [str(d) for d in departure_dates]
        for sid in available_sites:
            if sid not in existing_sites_str:
                result["agents"][sid] = {"status": f"site with ID {sid} does not exist"}
            else:
                result["agents"][sid] = {ds: {} for ds in date_strings}

        for dep_date in departure_dates:
            routes = self._get_routes_data(
                dep_date,
                from_city_id,
                to_city_id,
                available_sites,
                departure_time_from,
                departure_time_to,
                arrival_time_from,
                arrival_time_to,
                is_transfer,
            )
            for site_id, route_obj in routes.items():
                site_data = result["agents"].get(str(site_id))
                if isinstance(site_data, dict) and "status" not in site_data:
                    site_data[str(dep_date)] = route_obj

        return result

    def get_trips_by_route(
            self,
            route_id: int,
            departure_time_from: Optional[time] = None,
            departure_time_to: Optional[time] = None,
            arrival_time_from: Optional[time] = None,
            arrival_time_to: Optional[time] = None,
            is_transfer: Optional[bool] = None,
    ) -> TripSchemaResponse:
        latest = self._build_history_subquery().alias("latest_history")
        trip_ids_subq = self._apply_time_filters(
            select(TripModel.id).where(TripModel.route_id == route_id),
            departure_time_from,
            departure_time_to,
            arrival_time_from,
            arrival_time_to,
        ).subquery()

        transfer_cond = (
            (TripModel.is_transfer == is_transfer) if is_transfer is not None else True
        )

        q = (
            select(
                TripModel,
                RouteModel.departure_date.label("route_date"),
                latest.c.price,
                latest.c.currency,
                latest.c.available_seats,
                latest.c.created_at.label("price_updated_at"),
            )
            .select_from(TripModel)
            .where(TripModel.route_id == route_id)
            .where(TripModel.id.in_(select(trip_ids_subq)))
            .where(transfer_cond)
            .join(latest)
            .join(RouteModel, TripModel.route_id == RouteModel.id)
        )

        rows = self.db.execute(q).all()
        return self._process_trips(rows)

    @staticmethod
    def _normalize_sites(sites: Optional[List[int]]) -> List[str]:
        return [str(s) for s in sites] if sites else []

    def _get_existing_site_ids(self, available: List[str]) -> List:
        return (
            self.db.execute(select(SiteModel.id).where(SiteModel.id.in_(available)))
            .scalars()
            .all()
        )

    @staticmethod
    def _make_route_entry(
            from_city_id, to_city_id, dep_date, available, existing
    ) -> Dict[str, Any]:
        existing_str = [str(s) for s in existing]
        agents = {}
        for sid in available:
            agents[sid] = (
                {}
                if sid in existing_str
                else {"status": f"site with ID {sid} does not exist"}
            )
        return {
            "from_city": from_city_id,
            "to_city": to_city_id,
            "departure_date": str(dep_date),
            "agents": agents,
        }

    def _get_unique_routes(self, dep_date, page, size, from_ids, to_ids):
        from_city = aliased(CityModel, name="from_city")
        to_city = aliased(CityModel, name="to_city")

        q = (
            select(
                from_city.name_ua.label("from_city_name"),
                to_city.name_ua.label("to_city_name"),
                RouteModel.from_city_id,
                RouteModel.to_city_id,
            )
            .join(from_city, RouteModel.from_city_id == from_city.id)
            .join(to_city, RouteModel.to_city_id == to_city.id)
            .group_by(
                RouteModel.from_city_id,
                RouteModel.to_city_id,
                from_city.name_ua,
                to_city.name_ua,
            )
            .where(RouteModel.departure_date == dep_date)
            .order_by(from_city.name_ua, to_city.name_ua)
        )
        if from_ids:
            q = q.where(RouteModel.from_city_id.in_(from_ids))
        if to_ids:
            q = q.where(RouteModel.to_city_id.in_(to_ids))

        total = (
                self.db.execute(select(func.count()).select_from(q.subquery())).scalar()
                or 0
        )
        rows = self.db.execute(q.offset((page - 1) * size).limit(size)).all()
        return rows, total

    @staticmethod
    def _build_history_subquery():
        cutoff = datetime.now() - timedelta(days=30)
        return (
            select(
                TripHistoryModel.trip_id,
                TripHistoryModel.price,
                TripHistoryModel.currency,
                TripHistoryModel.available_seats,
                TripHistoryModel.created_at,
            )
            .where(TripHistoryModel.trip_id == TripModel.id)
            .where(TripHistoryModel.created_at >= cutoff)
            .order_by(desc(TripHistoryModel.created_at))
            .limit(1)
            .correlate(TripModel)
            .lateral()
        )

    @staticmethod
    def _apply_time_filters(q, dep_from, dep_to, arr_from, arr_to):
        from sqlalchemy import Time

        if dep_from:
            q = q.where(func.cast(TripModel.departure_time, Time) >= dep_from)
        if dep_to:
            q = q.where(func.cast(TripModel.departure_time, Time) <= dep_to)
        if arr_from:
            q = q.where(func.cast(TripModel.arrival_time, Time) >= arr_from)
        if arr_to:
            q = q.where(func.cast(TripModel.arrival_time, Time) <= arr_to)
        return q

    def _get_routes_data(
            self,
            dep_date,
            from_city_id,
            to_city_id,
            available_sites,
            dep_time_from,
            dep_time_to,
            arr_time_from,
            arr_time_to,
            is_transfer,
    ) -> Dict[Any, RouteSchema]:
        latest = self._build_history_subquery().alias("latest_history")
        time_filters = (dep_time_from, dep_time_to, arr_time_from, arr_time_to)
        has_time = any(time_filters)

        trip_ids_q = self._apply_time_filters(
            select(TripModel.id).where(TripModel.route_id == RouteModel.id),
            *time_filters,
        ).subquery()

        transfer_cond = (
            (TripModel.is_transfer == is_transfer) if is_transfer is not None else True
        )

        q = (
            select(
                RouteModel.from_city_id,
                RouteModel.to_city_id,
                RouteModel.site_id,
                RouteModel.departure_date,
                RouteModel.id,
                func.max(latest.c.currency).label("currency"),
                func.percentile_cont(0.5)
                .within_group(latest.c.price)
                .label("median_price"),
                func.min(latest.c.price).label("min_price"),
                func.max(latest.c.price).label("max_price"),
                func.count(func.distinct(TripModel.id)).label("total_segments_count"),
            )
            .outerjoin(
                TripModel,
                and_(
                    RouteModel.id == TripModel.route_id,
                    (TripModel.id.in_(select(trip_ids_q)) if has_time else True),
                    transfer_cond,
                ),
            )
            .join(latest)
            .where(RouteModel.departure_date == dep_date)
            .where(RouteModel.from_city_id == from_city_id)
            .where(RouteModel.to_city_id == to_city_id)
            .where(RouteModel.site_id.in_(available_sites))
            .group_by(RouteModel.id)
        )

        rows = self.db.execute(q).all()
        result = {}
        for row in rows:
            result[row.site_id] = RouteSchema(
                id=row.id,
                currency=row.currency or "",
                min_price=row.min_price or 0.0,
                max_price=row.max_price or 0.0,
                median_price=row.median_price or 0.0,
                total_segments_count=row.total_segments_count or 0,
            )
        return result

    @staticmethod
    def _process_trips(rows) -> TripSchemaResponse:
        trips = []
        for row in rows:
            trip = row[0]
            td = trip.duration
            duration = None
            if td is not None:
                total_sec = int(td.total_seconds())
                duration = time(
                    total_sec // 3600 % 24, (total_sec % 3600) // 60, total_sec % 60
                )
            trips.append(
                TripSchema(
                    from_station=trip.from_station,
                    to_station=trip.to_station,
                    departure_date=row.route_date,
                    departure_time=trip.departure_time,
                    arrival_time=trip.arrival_time,
                    arrival_date=trip.arrival_date,
                    carrier_name=trip.carrier_name,
                    duration=duration,
                    is_transfer=trip.is_transfer,
                    price=row.price,
                    currency=row.currency,
                    available_seats=row.available_seats,
                    price_updated_at=row.price_updated_at,
                )
            )
        return TripSchemaResponse(total_segments_count=len(trips), trips=trips)

    def export_routes_to_csv(
            self,
            departure_date: "date",
            from_city_ids: Optional[List[int]] = None,
            to_city_ids: Optional[List[int]] = None,
            departure_time_from: Optional["time"] = None,
            departure_time_to: Optional["time"] = None,
            arrival_time_from: Optional["time"] = None,
            arrival_time_to: Optional["time"] = None,
            is_transfer: Optional[bool] = None,
            sites: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns a flat list of rows for CSV export of routes on a specified date.
        Each row = one route × one aggregator.
        """

        from_city = aliased(CityModel, name="from_city")
        to_city = aliased(CityModel, name="to_city")
        latest = self._build_history_subquery().alias("latest_history")

        time_filters = (departure_time_from, departure_time_to, arrival_time_from, arrival_time_to)
        has_time = any(time_filters)

        trip_ids_q = self._apply_time_filters(
            select(TripModel.id).where(TripModel.route_id == RouteModel.id),
            *time_filters,
        ).subquery()

        transfer_cond = (
            (TripModel.is_transfer == is_transfer) if is_transfer is not None else True
        )

        site_filter = [str(s) for s in sites] if sites else None

        q = (
            select(
                from_city.name_ua.label("from_city"),
                to_city.name_ua.label("to_city"),
                RouteModel.departure_date,
                SiteModel.name.label("aggregator"),
                RouteModel.id.label("route_id"),
                func.max(latest.c.currency).label("currency"),
                func.min(latest.c.price).label("min_price"),
                func.percentile_cont(0.5)
                .within_group(latest.c.price)
                .label("median_price"),
                func.max(latest.c.price).label("max_price"),
                func.count(func.distinct(TripModel.id)).label("segments_count"),
            )
            .join(from_city, RouteModel.from_city_id == from_city.id)
            .join(to_city, RouteModel.to_city_id == to_city.id)
            .join(SiteModel, RouteModel.site_id == SiteModel.id)
            .outerjoin(
                TripModel,
                and_(
                    RouteModel.id == TripModel.route_id,
                    (TripModel.id.in_(select(trip_ids_q)) if has_time else True),
                    transfer_cond,
                ),
            )
            .join(latest)
            .where(RouteModel.departure_date == departure_date)
            .group_by(
                RouteModel.id,
                from_city.name_ua,
                to_city.name_ua,
                SiteModel.name,
            )
            .order_by(from_city.name_ua, to_city.name_ua, SiteModel.name)
        )

        if from_city_ids:
            q = q.where(RouteModel.from_city_id.in_(from_city_ids))
        if to_city_ids:
            q = q.where(RouteModel.to_city_id.in_(to_city_ids))
        if site_filter:
            q = q.where(RouteModel.site_id.in_(site_filter))

        rows = self.db.execute(q).all()

        return [
            {
                "from_city": row.from_city,
                "to_city": row.to_city,
                "departure_date": str(row.departure_date),
                "aggregator": row.aggregator,
                "route_id": row.route_id,
                "currency": row.currency or "",
                "min_price": round(row.min_price or 0, 2),
                "median_price": round(float(row.median_price or 0), 2),
                "max_price": round(row.max_price or 0, 2),
                "segments_count": row.segments_count or 0,
            }
            for row in rows
        ]

    def export_trips_to_csv(
            self,
            route_id: int,
            departure_time_from: Optional[time] = None,
            departure_time_to: Optional[time] = None,
            arrival_time_from: Optional[time] = None,
            arrival_time_to: Optional[time] = None,
            is_transfer: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns a flat list of rows for CSV export of trips for a given route.
        Applies the same filters as get_trips_by_route.
        """
        response = self.get_trips_by_route(
            route_id=route_id,
            departure_time_from=departure_time_from,
            departure_time_to=departure_time_to,
            arrival_time_from=arrival_time_from,
            arrival_time_to=arrival_time_to,
            is_transfer=is_transfer,
        )

        rows = []
        for trip in response.trips:
            rows.append(
                {
                    "departure_date": str(trip.departure_date) if trip.departure_date else "",
                    "departure_time": str(trip.departure_time)[:5] if trip.departure_time else "",
                    "arrival_date": str(trip.arrival_date) if trip.arrival_date else "",
                    "arrival_time": str(trip.arrival_time)[:5] if trip.arrival_time else "",
                    "duration": str(trip.duration)[:5] if trip.duration else "",
                    "from_station": trip.from_station or "",
                    "to_station": trip.to_station or "",
                    "carrier_name": trip.carrier_name,
                    "is_transfer": trip.is_transfer,
                    "price": trip.price,
                    "currency": trip.currency,
                    "available_seats": trip.available_seats if trip.available_seats is not None else "",
                    "price_updated_at": trip.price_updated_at.strftime(
                        "%Y-%m-%d %H:%M") if trip.price_updated_at else "",
                }
            )
        return rows

    def export_segment_to_csv(
            self,
            from_city_id: int,
            to_city_id: int,
            departure_dates: List[date],
            departure_time_from: Optional[time] = None,
            departure_time_to: Optional[time] = None,
            arrival_time_from: Optional[time] = None,
            arrival_time_to: Optional[time] = None,
            sites: Optional[List[int]] = None,
            is_transfer: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Flat CSV export for a city-pair segment across multiple departure dates.
        Each row = one date × one aggregator with min/median/max price and segment count.
        """
        from_city_alias = aliased(CityModel, name="from_city")
        to_city_alias = aliased(CityModel, name="to_city")
        latest = self._build_history_subquery().alias("latest_history")

        time_filters = (departure_time_from, departure_time_to, arrival_time_from, arrival_time_to)
        has_time = any(time_filters)

        trip_ids_q = self._apply_time_filters(
            select(TripModel.id).where(TripModel.route_id == RouteModel.id),
            *time_filters,
        ).subquery()

        transfer_cond = (
            (TripModel.is_transfer == is_transfer) if is_transfer is not None else True
        )

        available_sites = self._normalize_sites(sites)
        existing_site_ids = [str(s) for s in self._get_existing_site_ids(available_sites)]

        q = (
            select(
                from_city_alias.name_ua.label("from_city"),
                to_city_alias.name_ua.label("to_city"),
                RouteModel.departure_date,
                SiteModel.name.label("aggregator"),
                RouteModel.id.label("route_id"),
                func.max(latest.c.currency).label("currency"),
                func.min(latest.c.price).label("min_price"),
                func.percentile_cont(0.5)
                .within_group(latest.c.price)
                .label("median_price"),
                func.max(latest.c.price).label("max_price"),
                func.count(func.distinct(TripModel.id)).label("segments_count"),
            )
            .join(from_city_alias, RouteModel.from_city_id == from_city_alias.id)
            .join(to_city_alias, RouteModel.to_city_id == to_city_alias.id)
            .join(SiteModel, RouteModel.site_id == SiteModel.id)
            .outerjoin(
                TripModel,
                and_(
                    RouteModel.id == TripModel.route_id,
                    (TripModel.id.in_(select(trip_ids_q)) if has_time else True),
                    transfer_cond,
                ),
            )
            .join(latest)
            .where(RouteModel.from_city_id == from_city_id)
            .where(RouteModel.to_city_id == to_city_id)
            .where(RouteModel.departure_date.in_(departure_dates))
            .group_by(
                RouteModel.id,
                from_city_alias.name_ua,
                to_city_alias.name_ua,
                SiteModel.name,
                RouteModel.departure_date,
            )
            .order_by(RouteModel.departure_date, SiteModel.name)
        )

        if available_sites:
            q = q.where(RouteModel.site_id.in_(existing_site_ids))

        rows = self.db.execute(q).all()

        return [
            {
                "from_city": row.from_city,
                "to_city": row.to_city,
                "departure_date": str(row.departure_date),
                "aggregator": row.aggregator,
                "route_id": row.route_id,
                "currency": row.currency or "",
                "min_price": round(row.min_price or 0, 2),
                "median_price": round(float(row.median_price or 0), 2),
                "max_price": round(row.max_price or 0, 2),
                "segments_count": row.segments_count or 0,
            }
            for row in rows
        ]
