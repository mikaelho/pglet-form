import datetime
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import List

from pglet import Dialog
from pglet import Image
from pglet import Stack
from pglet import Text

from form import Form

content = []


def introduction():
    """
    # Easy web development for Python developers

    Web technologies are available everywhere, and they seem like a good way to create a graphical user interface for
    your Python application, either on the desktop or on the web. Unfortunately, most Python coders like Python,
    and would like to avoid using a lot of other languages (HTML, Javascript and CSS) just to get a UI created.

    Pglet ("pagelet") is a server using React components and providing a protocol for clients to control the UI. One
    of the available languages is Python. The server comes nicely bundled in the install, so all you need is:

    `pip install pglet`

    and you are off to creating a web-enabled UI in pure Python (3.7+).

    As a taste of what pglet-python code looks like, this is the code for the box on the right:

    [code]
    ```
    pglet.page().add(main_view)
    ```

    For more details, supported controls and a tutorial, see the [pglet Python docs](https://pglet.io/docs/).

    # Easy forms

    One of the most-repeated type of UI is some kind of form for entering and updating information. While creating
    forms is easy in pglet, it is nevertheless a repeating task that provides little programming joy. The next pages
    show how to create forms using a Form control that eats annotated Python classes, for example, Python's
    [dataclasses](https://docs.python.org/3/library/dataclasses.html).

    # Easy forms with validation

    Typically you also need to somehow validate user input before you can use it for anything: you need to check that
    necessary values have been provided, check that numbers are numbers, check dates etc.

    You can avoid this repetitive code by giving the Form control a [pydantic](https://pydantic-docs.helpmanual.io/)
    object. Validation defined on the object is performed before the data is returned to you. In some cases,
    you can use the exact same data definition with your APIs (e.g. FastAPI) or when writing to a document or SQL
    data store.
    """

    import pglet
    from pglet import Image, Stack, Text

    main_view = Stack(
        horizontal_align="center",
        padding=20, gap=20,
        controls=[
            Image(width="50%", src="https://www.python.org/static/img/python-logo@2x.png"),
            Image(width="30%", src="https://pglet.io/img/logo_dark.svg"),
            Text(value="pydantic", bold=True, size="xxLarge"),
        ],
    )

    return main_view


content.append(introduction)


def data_first_forms():
    """
    Using the Form control, form definition focuses on the data you need out of it, so we define a class with
    necessary information as attributes, information types as annotations, and default values as assignements.

    Python dataclasses are convenient for this, as we do not need to spend time creating the `__init__` and other
    boilerplate.

    To create the form, all we need to do is give the class definition to the Form control:

    [code]

    Change values, and click "OK" to see the data you would get.

    Form control understands the following data types explicitly, others will be by default be represented with a
    basic text box on the form:
    - str
    - int
    - float
    - bool
    - datetime
    - date
    - time
    - Decimal
    """

    @dataclass
    class DataclassDataModel:
        name: str = "Dataclass Person"
        birthdate: datetime.date = "2000-01-01"
        address: str = "Some Street 1, Some Town, Some Country"
        age: int = 33
        happy_today: bool = True
        email: str = "some@email.com"

    form = Form(value=DataclassDataModel, width="100%", on_submit=show_submitted_data)

    return form


data_first_forms.display_name = "Data-first forms"

content.append(data_first_forms)


def selection_values():
    """
    Python enums are supported for selecting from a specific set of values.

    [code]
    """
    class ContactOption(str, Enum):
        EMAIL = 'email'
        PHONE = 'phone'

    @dataclass
    class DataclassDataModel:
        name: str = "Dataclass Person"
        ok_to_contact: bool = True
        contact_option: ContactOption = ContactOption.EMAIL

    return Form(value=DataclassDataModel, width="100%", on_submit=show_submitted_data)

content.append(selection_values)


def more_values():
    """
    If there are more than 3 values, we switch to a dropdown. The threshold is configurable.

    [code]
    """
    class ContactOption(str, Enum):
        EMAIL = 'email'
        PHONE = 'phone'
        MESSAGE = 'message'
        DOVE = 'dove'

    @dataclass
    class DataclassDataModel:
        name: str = "Dataclass Person"
        ok_to_contact: bool = True
        contact_option: ContactOption = ContactOption.EMAIL

    return Form(value=DataclassDataModel, width="100%", on_submit=show_submitted_data)

content.append(more_values)


def nested_class_definitions():
    """
    Often we need to reuse parts of data structures. Form control supports nested class definitions, like `Movie`
    in the example below.

    [code]
    """
    @dataclass
    class Movie:
        title: str
        year: int

    @dataclass
    class DataclassDataModel:
        name: str = "Dataclass Person"
        email: str = "some@email.com"
        favorite_movie: Movie = Movie(
            title="My Little Pony: The Movie",
            year=2017,
        )

    return Form(value=DataclassDataModel, width="100%", on_submit=show_submitted_data)

content.append(nested_class_definitions)


def several_nested_objects():
    """
    Several nested objects are supported with a List annotation. Lists rely on a sensible `str()` implementation to
    display nicely, open up in a separate panel for editing, and support adding and deleting items.

    [code]

    Note that to support adding more movies, we need to provide default values for Movie attributes.
    """
    @dataclass
    class Movie:
        title: str = ""
        year: int = 2000

        def __str__(self):
            return f"{self.title} ({self.year})"

    movies = [
        Movie(title="My Little Pony: The Movie", year=2017),
        Movie(title="The Name of the Rose", year=1986),
    ]

    @dataclass
    class DataclassDataModel:
        name: str = "Dataclass Person"
        email: str = "some@email.com"
        favorite_movies: List[Movie] = field(
            default_factory = lambda: movies
        )


    return Form(value=DataclassDataModel, width=500, on_submit=show_submitted_data)

content.append(several_nested_objects)


def show_submitted_data(event):
    value = event.control.value
    event.control.page.add(Dialog(open=True, title="Submitted data", blocking=True, controls=[
        Text(value=str(value.__dict__))
    ]))