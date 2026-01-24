from models import User
from db.ctrl import db
from logger import logger


async def aprooved(user: User):
    if company := await db.get_partner_by_id(user.company_id):
        return company
    else:
        logger.warning(f"User {user.first_name} not tied to the company")
        return False
