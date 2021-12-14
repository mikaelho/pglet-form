import traceback
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List

import pydantic

from typing import Union, Literal

import pglet
from pglet import Text
from pglet.control_event import ControlEvent

from form import Form


@dataclass
class DataclassDataModel:
    name: str = 'Dataclass Person'
    birthdate: date = "2000-01-01"
    address: str = 'Some Street 1, Some Town, Some Country'
    age: int = 33
    happy_today: bool = True
    email: str = 'some@email.com'


non_empty_str = pydantic.constr(strip_whitespace=True, min_length=1)


class ContactOptions(str, Enum):
    EMAIL = 'email'
    PHONE = 'phone'


class Movie(pydantic.BaseModel):
    title: non_empty_str = ""
    director: str = ""
    year: int = 2000

    def __str__(self):
        return f"{self.title} ({self.year})"


class PydanticDataModel(pydantic.BaseModel):
    title: str = ""
    name: non_empty_str = "Demo Person"
    birthdate: date = "2000-01-01"
    address: non_empty_str = "Some Street 1, Some Town, Some Country"
    temperature: float = 37.0
    happy_today: bool = pydantic.Field(default=True, title='Am I happy today?')
    contact_preference: ContactOptions = ContactOptions.EMAIL
    email: Union[pydantic.EmailStr, Literal[""]] = pydantic.Field(
        default="",
        description='Give a valid email address',
    )
    phone: str = pydantic.Field(default="", regex="^[\d ()+-]*?$", description="Only numbers and ()+- allowed")
    movies: List[Movie] = [
        Movie(title="My Little Pony: The Movie", director="Jayson Thiessen", year=2017),
        Movie(title="The Name of the Rose", director="Jean-Jacques Annaud", year=1986),
    ]

    @pydantic.validator('email', pre=True)
    def email_is_filled_if_selected(cls, value, values):
        if values.get('contact_preference') == ContactOptions.EMAIL and not value:
            raise ValueError('Please fill in an email address')
        return value

    @pydantic.validator('phone', pre=True)
    def phone_is_filled_if_selected(cls, value, values):
        if values.get('contact_preference') == ContactOptions.PHONE and not value:
            raise ValueError('Please fill in a phone number')
        return value

class FormTestApp():
    def __init__(self, page):
        self.page = page
        self.view = pglet.Tabs(
            width="min(600px, 90%)",
            padding=20,
            tabs=[
                pglet.Tab(
                    text="Pydantic form",
                    controls=[
                        Form(
                            value=PydanticDataModel(),
                            on_submit=self.on_submit,
                        ),
                    ],
                ),
                pglet.Tab(
                    text="Dataclass form",
                    controls=[
                        Form(value=DataclassDataModel(), on_submit=self.on_submit),
                    ],
                ),
            ],
        )

    def on_submit(self, event: ControlEvent):
        self.page.add(pglet.Dialog(open=True, title="Submitted data", blocking=True, controls=[
            Text(value=str(event.control.value))
        ]))


def main(page):
    page.title = "Form test"
    page.horizontal_align = 'center'
    page.theme = 'light'
    app = FormTestApp(page)
    page.add(app.view)


pglet.app("index", target=main, local=True)
