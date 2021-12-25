import inspect
from functools import partial
from textwrap import dedent

import pglet
from pglet import Button
from pglet import Stack
from pglet import Text
from pglet import Toggle

from manual_content import content


class FormDemoApp:
    def __init__(self):
        self.page = None

        self.table_of_contents = Stack(gap=0, controls=self.get_controls_for_table_of_contents())
        self.previous_button = Button(icon="ChevronUp", on_click=partial(self.change, -1))
        self.next_button = Button(icon="ChevronDown", on_click=partial(self.change, +1))

        self.title = Text(bold=True, size="xLarge", width="100%", color="themePrimary")
        self.body = Text(markdown=True, width="100%", padding=0)
        self.result = Stack(width="max(400px, 60%)", margin="100px 0px 0px 0px")

        self.mode_toggle = Toggle(value=True, label="Dark mode", on_change=self.set_mode)

        self.selected_index = 0

    def main(self, page):
        self.page = page

        table_of_contents_buttons = Stack(
            height="100%",
            vertical_align="center",
            controls=[
                self.previous_button,
                self.next_button,
            ]
        )

        table_of_contents_area = Stack(
            #width="20%",
            min_width=300,
            horizontal_align="left",
            margin=32,
            gap=32,
            controls=[
                Text(bold=True, size="xLarge", value="Table of Contents"),
                Stack(horizontal=True, controls=[
                    self.table_of_contents,
                    table_of_contents_buttons,
                ]),
                self.mode_toggle,
            ],
        )

        heading_area = Stack(horizontal=True, controls=[self.title])

        text_area = Stack(
            width="100%",
            margin=32,
            controls=[
                heading_area,
                self.body,
            ],
        )

        page.add(
            Stack(
                #wrap=True,
                width="95%",
                gap=16,
                horizontal=True,
                vertical_align="top",
                vertical_fill=False,
                controls=[table_of_contents_area, text_area, self.result],
            )
        )

        self.change(-1)

        page.horizontal_align = "center"
        self.set_mode()
        page.update()

    def get_controls_for_table_of_contents(self):
        return [
            Stack(
                border_top="1px solid lightgray",
                gap=0,
                controls=[
                    Button(
                        action=True,
                        text=self.display_name(func),
                        icon="CircleRing",
                        on_click=partial(self.display, func),
                    )
                ],
            )
            for func in content
        ]

    def display(self, document_function, event=None):
        self.selected_index = content.index(document_function)
        self.display_function(document_function)

    def display_function(self, document_function):
        for control in self.table_of_contents.controls:
            control.controls[0].icon = "CircleRing"

        self.table_of_contents.controls[self.selected_index].controls[0].icon = "CircleFill"

        document_function = content[self.selected_index]
        self.title.value = self.display_name(document_function)
        self.body.value = self.get_body_text(document_function)
        self.result.clean()
        if control := document_function(None):
            control.border = "1px solid"
            self.result.controls = [control]
        self.page.update()

    def change(self, delta, event=None):
        self.selected_index = max(0, min(len(content) - 1, self.selected_index + delta))

        self.previous_button.disabled = self.selected_index == 0
        self.next_button.disabled = self.selected_index == len(content) - 1

        self.display_function(content[self.selected_index])

    def get_body_text(self, document_function):
        body = inspect.getdoc(document_function)

        code = "\n".join(inspect.getsource(document_function).split('"""')[2].splitlines()[:-1])
        code = dedent(code).strip()
        code = f"```\n{code}\n```"

        body = body.replace("[code]", code) if "[code]" in body else f"{body}\n{code}"

        return body

    def display_name(self, document_function):
        if value := getattr(document_function, "display_name", None):
            return value
        else:
            return document_function.__name__.replace("_", " ").capitalize()

    def set_mode(self, event=None):
        self.page.theme = "dark" if self.mode_toggle.value else "light"
        self.page.update()


if __name__ == "__main__":
    pglet.app("index", target=FormDemoApp().main, local=True)
