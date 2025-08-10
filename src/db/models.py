from pydantic import BaseModel
from datetime import datetime as dt

class User(BaseModel):
    user_id: int
    first_name: str | None = None
    username: str | None = None

    admin: bool = False
    banned: bool = False

    record: str | None = None
    type: str | None = None
    ts: dt