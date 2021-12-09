###import time
#from threading import Thread 
from dataclasses import dataclass

import pglet

from form import Form


@dataclass
class DataModel:
    name: str = 'Demo Person'
    address: str = 'Some Street 1, Some Town, Some Country'
    age: int = 33
    email_me: bool = False
    email: str = 'some@email.com'


class FormTestApp():
    def __init__(self):
        self.form = Form(data=DataModel)

def main(page):
    page.title = "Form test"
    page.horizontal_align = 'center'
    page.theme = 'light'
    app = FormTestApp()
    page.add(app.form)


# def run():
pglet.app("index", target=main, local=True)

def run_server():
    t = Thread(target=run)
    t.start()

# run_server()
