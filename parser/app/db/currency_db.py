from typing import Any, Dict, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from parser.app.models import CurrencyModel
from parser.app.schemas.currency_schema import CurrencySchema
from parser.app.settings.logger import get_logger

logger = get_logger(__name__)

def get_currency_by_code(db: Session, code: str) -> Optional[CurrencyModel]:
    if not code:
        return None

    code = code.upper()
    return db.query(CurrencyModel).filter(CurrencyModel.code == code).first()


def create_currency(db: Session, currency_data: CurrencySchema) -> CurrencyModel:
    try:
        new_currency = CurrencyModel(
            code=currency_data.code.upper(),
            rate=currency_data.rate,
            exchange_date=currency_data.exchange_date,
        )

        db.add(new_currency)
        db.commit()
        db.refresh(new_currency)
        return new_currency
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error while creating currency: {e}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error while creating currency: {e}")
        raise


def update_currency(
    db: Session, db_currency: CurrencyModel, update_data: Dict[str, Any]
) -> CurrencyModel:
    if "rate" in update_data and update_data["rate"] is not None:
        db_currency.rate = update_data["rate"]

    if "exchange_date" in update_data and update_data["exchange_date"] is not None:
        db_currency.exchange_date = update_data["exchange_date"]

    try:
        db.commit()
        db.refresh(db_currency)
        return db_currency
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating currency {db_currency.code}: {e}")
        raise


def update_or_create_currency(
    db: Session, currency_data: CurrencySchema
) -> CurrencyModel:
    code = currency_data.code.upper()
    db_currency = get_currency_by_code(db, code)

    if db_currency:
        update_data = {
            "rate": currency_data.rate,
            "exchange_date": currency_data.exchange_date,
        }
        return update_currency(db, db_currency, update_data)

    return create_currency(db, currency_data)
