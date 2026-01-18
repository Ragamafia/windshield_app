from PIL import Image

from models import User
from db.ctrl import db
from logger import logger


# async def check_image(image_path, brand, model, id):
#     if image_path.exists():
#         try:
#             with Image.open(image_path) as f:
#                 f.verify()
#                 logger.success(f'Image already exists: {brand} {model} {id}')
#         except:
#             await self._download_image(brand, model, id)


async def aprooved(user: User):
    if company := await db.get_partner_by_id(user.company_id):
        return company
    else:
        logger.warning(f"User {user.first_name} not tied to the company")
        return False
