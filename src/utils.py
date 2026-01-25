import qrcode

from models import User
from db.ctrl import db
from logger import logger


async def aprooved(user: User):
    if company := await db.get_partner_by_id(user.company_id):
        return company
    else:
        logger.warning(f"User {user.first_name} not tied to the company")
        return False


def generate_qr_code():
    qr_codes = {
        "QR1": "https://t.me/@ragamafiatest1bot?start=manager",
        "FirstDetailer": "https://t.me/@FirstDetailerBot?start=manager",
    }
    for name, url in qr_codes.items():
        qr = qrcode.make(url)
        qr.save(f"{name}.png")

#generate_qr_code()
