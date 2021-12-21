import copy
import datetime
import time
import traceback
from dataclasses import is_dataclass
from functools import partial
from types import SimpleNamespace
from typing import Any
from typing import Union

from pglet import Button
from pglet import ChoiceGroup
from pglet import DatePicker
from pglet import Dropdown
from pglet import Message
from pglet import Panel
from pglet import SpinButton
from pglet import Stack
from pglet import Text
from pglet import Textbox
from pglet import Toggle
from pglet import choicegroup
from pglet import dropdown
from pglet.control_event import ControlEvent

__all__ = ["Form"]


class Form(Stack):

    _step_for_floats = 0.1

    _float_button = partial(SpinButton, step=_step_for_floats)
    _date_picker_with_edit = partial(DatePicker, allow_text_input=True)

    _standard_library_types = {
        "str": Textbox,
        "int": SpinButton,
        "float": _float_button,
        "Decimal": _float_button,
        "bool": Toggle,
        "datetime": Textbox,
        "date": _date_picker_with_edit,
        "time": Textbox,
    }

    _pydantic_types = {
        "ConstrainedIntValue": SpinButton,
        "NegativeIntValue": SpinButton,
        "PositiveIntValue": SpinButton,
        "StrictIntValue": SpinButton,
        "ConstrainedFloatValue": _float_button,
        "NegativeFloatValue": _float_button,
        "PositiveFloatValue": _float_button,
        "StrictFloatValue": _float_button,
        "ConstrainedDecimalValue": _float_button,
        "StrictBoolValue": Toggle,
        "EmailStrValue": Textbox,
        "PastDateValue": _date_picker_with_edit,
        "FutureDateValue": _date_picker_with_edit,
        # 'SecretStr': , not supported by pglet
    }

    _from_data_type_to_form_control = _standard_library_types
    _from_data_type_to_form_control.update(_pydantic_types)

    # Alignments when not "top"
    _label_alignment_by_control_type = {
        DatePicker: "center",
        SpinButton: "center",
        Textbox: "center",
    }

    def __init__(
        self,
        value: Any,
        on_submit: callable = None,
        submit_button: Button = None,
        field_validation_default_error_message: str = "Check this value",
        form_validation_error_message: str = "Not all fields have valid values",
        autosave: bool = False,
        label_above: bool = False,
        label_alignment: str = "left",
        label_width: str = "30%",
        control_style: str = "normal",
        padding: int = 20,
        gap: int = 10,
        width="min(600px, 90%)",
        threshold_for_dropdown=3,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.field_validation_default_error_message = field_validation_default_error_message
        self.form_validation_error_message = form_validation_error_message
        self.autosave = autosave
        self.label_above = label_above
        self.label_alignment = label_alignment
        self.label_width = label_width
        self.control_style = control_style
        self.threshold_for_dropdown = threshold_for_dropdown

        self.padding = padding
        self.gap = gap
        self.width = width

        if type(value) is type:
            self._model = value
            if hasattr(self._model, "__fields__"):
                self.value = self._model.construct()
            else:
                try:
                    self.value = self._model()
                except Exception as error:
                    raise ValueError("Unable to instantiate form data with default values", error)
        else:
            self._model = type(value)
            self.value = value

        self.working_copy = self.autosave and self.value or copy.deepcopy(self.value)

        self._fields = {}
        self._messages = {}
        self._pydantic_fields = {}

        self.on_submit = getattr(submit_button, "on_click", on_submit)

        self._submit_button = submit_button or Button(text="OK", primary=True, icon="CheckMark")
        self._submit_button.on_click = self._submit

        self._form_not_valid_message = Message(value=self.form_validation_error_message, type="error", visible=False)

        self._create_controls()

    def _create_controls(self):
        controls = self._create_controls_for_annotations(self.working_copy, self._model, self.label_above)
        self.controls = controls + [
            Stack(horizontal=True, horizontal_align="end", controls=[self._form_not_valid_message, self._submit_button])
        ]

    def _create_controls_for_annotations(self, obj, cls, label_above, path: tuple = tuple()):
        return [
            self._create_control(attribute, attribute_type, getattr(obj, attribute), label_above, path)
            for attribute, attribute_type in cls.__annotations__.items()
        ]

    def _create_control(self, attribute: str, attribute_type: Any, value: Any, label_above: bool, path: tuple):
        # For unions, we consider only the first type annotation
        if (origin := getattr(attribute_type, "__origin__", None)) and origin == Union:
            attribute_type = attribute_type.__args__[0]

        control_data = SimpleNamespace(
            attribute=attribute,
            attribute_type=attribute_type,
            value=value,
            label_text=attribute.replace("_", " ").capitalize(),
            placeholder="",
            error_message=self.field_validation_default_error_message,
        )

        control_data = self._apply_pydantic_overrides(control_data, path)

        handle_change_func = partial(self._handle_field_submit_event, path + (attribute,))

        is_list = False

        if origin == list and len(attribute_type.__args__) == 1:
            actual_type = attribute_type.__args__[0]
            control_data.attribute_type = actual_type
            if type(actual_type).__name__ == "EnumMeta":
                control = self._create_multiple_choice_control(control_data, multiple=True)
            else:
                control = self._create_list_control(control_data)
                is_list = True
        elif type(attribute_type).__name__ == "EnumMeta":
            control = self._create_multiple_choice_control(control_data)
        elif self._is_complex_object(attribute_type):
            control = self._create_complex_control(control_data, path)
        else:
            control = self._create_basic_control(control_data)

        control.on_change = handle_change_func

        if self.control_style == "line":
            try:
                control.underlined = True
                control.borderless = True
            except AttributeError:
                pass

        self._fields[path + (attribute,)] = control

        message = Message(value=control_data.error_message, type="error", visible=False)
        self._messages[path + (attribute,)] = message

        control_stack = Stack(
            controls=[
                control,
                message,
            ],
            on_submit=handle_change_func,
            width="100%",
            vertical_align="center",
        )

        if hasattr(control, "label"):
            control.label = None

        label_text = Text(
            value=control_data.label_text,
            width="100%",
            bold=True,
            align=self.label_alignment,
            vertical_align=self._label_alignment_by_control_type.get(type(control), "top"),
        )

        label_stack = Stack(horizontal=True, controls=[label_text])
        if not label_above:
            label_stack.width = self.label_width

        if is_list:
            label_stack.controls.append(Button(icon="Add", on_click=control.list_add))

        attribute_stack = Stack(
            controls=[
                label_stack,
                control_stack,
            ],
        )
        if label_above:
            attribute_stack.gap = 0

        if not label_above:
            attribute_stack.horizontal = True

        return attribute_stack

    def _is_complex_object(self, object_type: type):
        return is_dataclass(object_type) or hasattr(object_type, "__fields__")

    def _apply_pydantic_overrides(self, control_data, path):
        pydantic_field = (
            hasattr(self._model, "__fields__") and self.value.__fields__.get(control_data.attribute) or None
        )

        if pydantic_field:
            self._pydantic_fields[path + (control_data.attribute,)] = pydantic_field
            if label_text := pydantic_field.field_info.title:
                control_data.label_text = label_text
            if placeholder := pydantic_field.field_info.description:
                control_data.placeholder = placeholder
                control_data.error_message = placeholder

        return control_data

    def _create_basic_control(self, control_data):
        control_type = self._from_data_type_to_form_control.get(control_data.attribute_type.__name__, Textbox)
        control = control_type(value=control_data.value)
        if control_type in (DatePicker, Dropdown, Textbox):
            control.placeholder = control_data.placeholder
        return control

    def _create_multiple_choice_control(self, control_data, multiple=False):
        if multiple:
            raise NotImplementedError("Multiple selection is not supported yet")

        enum_type = control_data.attribute_type

        value = enum_type(control_data.value).value

        if len(enum_type) >= self.threshold_for_dropdown:
            control_type = Dropdown
            option_type = dropdown.Option
        else:
            control_type = ChoiceGroup
            option_type = choicegroup.Option

        return control_type(
            options=[option_type(key=option.value, text=option.value.title()) for option in enum_type],
            value=value,
        )

    def _create_complex_control(self, control_data, path):
        return Stack(
            width="100%",
            controls=self._create_controls_for_annotations(
                control_data.value, control_data.attribute_type, label_above=True, path=path + (control_data.attribute,)
            ),
        )

    def _create_list_control(self, control_data):
        return ListControl(value=control_data.value, attribute_type=control_data.attribute_type, panel_width=self.width)

    def _handle_field_submit_event(self, attribute, event):
        self._validate_value(attribute)

    def _validate_value(self, attribute):
        is_valid = True
        control = self._fields[attribute]

        if type(control) is Stack:
            return True

        if pydantic_field := self._pydantic_fields.get(attribute):
            value, error = pydantic_field.validate(
                control.value,
                self.working_copy.dict(),
                loc=attribute,
                cls=self._model,
            )
            if error:
                print("NOT", attribute)
                is_valid = False
            else:
                # Validation can change the value, update control
                if type(value) is datetime.date:
                    value = value.isoformat()
                control.value = value

        if is_valid:
            obj = self.working_copy
            for attribute_name in attribute[:-1]:
                obj = getattr(obj, attribute_name)
            try:
                setattr(obj, attribute[-1], control.value)
            except ValueError:
                is_valid = False

        self._messages[attribute].visible = not is_valid
        self.page.update()
        return is_valid

    def _submit(self, e):
        if not all(self._validate_value(attribute) for attribute in self._fields):
            self._submit_button.primary = False
            self._submit_button.icon = "Cancel"
            self.page.update()
            time.sleep(5)
            self._submit_button.primary = True
            self._submit_button.icon = "CheckMark"
            self.page.update()
        else:
            if not self.autosave:
                self.value.__dict__.update(self.working_copy.__dict__)
            if self.on_submit:
                custom_event = ControlEvent(self._submit_button, "submit", None, self, self.page)
                self.on_submit(custom_event)


class ListControl(Stack):

    def __init__(self, value, attribute_type, panel_width=None, gap=0, **kwargs):
        super().__init__(**kwargs)
        self.gap = gap
        self.value = value
        self.attribute_type = attribute_type
        self.panel_width = panel_width
        self.panel = None
        self.panel_holder = Stack()
        self.update()

    def update(self):
        self.controls = [
            Stack(
                gap=0,
                horizontal=True,
                border_top="1px solid lightgray",
                controls=[
                    Button(width="100%", text=str(item), action=True, on_click=partial(self.list_selection, item)),
                    Button(height="100%", icon="Delete", on_click=partial(self.list_delete, index)),
                    Button(height="100%", icon="ChevronRight", on_click=partial(self.list_selection, item)),
                ],
            )
            for index, item in enumerate(self.value)
        ] + [self.panel_holder]

    def list_selection(self, item, event):
        subform = Form(value=item, on_submit=self._handle_subform_submit_event)
        self.panel = Panel(
            open=True,
            type='custom',
            auto_dismiss=False,
            light_dismiss=True,
            title=type(item).__name__.capitalize(),
            controls=[subform],
            on_dismiss=self._handle_subform_dismiss_event
        )
        if self.panel_width:
            self.panel.width = self.panel_width
        self.panel_holder.controls.append(self.panel)
        self.panel_holder.update()

    def list_delete(self, index, event):
        del self.value[index]
        self.update()
        self.page.update()

    def list_add(self, event):
        self.value.append(self.attribute_type())
        self.update()
        self.page.update()
        self.list_selection(self.value[-1], event)

    def _handle_subform_submit_event(self, event):
        self.update()
        self.page.update()
        self._handle_subform_dismiss_event(event)

    def _handle_subform_dismiss_event(self, event):
        self.panel_holder.controls.pop()
        self.panel_holder.update()
