
from dataclasses import dataclass
from datetime import date
from enum import Enum

import pydantic

import pglet

from form import Form


@dataclass
class DataclassDataModel:
    name: str = 'Dataclass Person'
    address: str = 'Some Street 1, Some Town, Some Country'
    age: int = 33
    happy_today: bool = True
    email: str = 'some@email.com'


class ContactOptions(str, Enum):
    EMAIL = 'email'
    PHONE = 'phone'


class PydanticDataModel(pydantic.BaseModel):
    name: str = 'Demo Person'
    birthdate: date = '2000-01-01'
    address: str = 'Some Street 1, Some Town, Some Country'
    temperature: float = 37.0
    happy_today: bool = pydantic.Field(default=True, title='Am I happy today?')
    contact_preference: ContactOptions = ContactOptions.EMAIL
    email: str = pydantic.Field(default='', description='Give a valid email address')
    phone: str = ''


class FormTestApp():
    def __init__(self):
        self.view = pglet.Tabs(tabs=[
            pglet.Tab(text='Pydantic form', controls=[
                Form(data=PydanticDataModel()),
            ]),
            pglet.Tab(text='Dataclass form', controls=[
                Form(data=DataclassDataModel()),
            ]),
        ])


def main(page):
    page.title = "Form test"
    page.horizontal_align = 'center'
    page.theme = 'light'
    app = FormTestApp()
    page.add(app.view)


pglet.app("index", target=main, local=True)
