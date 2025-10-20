from aiogram.fsm.state import State, StatesGroup


class EditPartner(StatesGroup):
    name = State()
    discount = State()


__all__ = [
    "EditPartner"
]