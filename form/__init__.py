import copy
import datetime
import time
from functools import partial
from types import SimpleNamespace
from typing import Any
from typing import Union

from pglet import Button
from pglet import ChoiceGroup
from pglet import DatePicker
from pglet import Dropdown
from pglet import Grid
from pglet import Message
from pglet import Panel
from pglet import SpinButton
from pglet import Stack
from pglet import Text
from pglet import Textbox
from pglet import Toggle
from pglet import choicegroup
from pglet.control_event import ControlEvent

__all__ = ["Form"]

class ListControl(Stack):

    def __init__(self, value, panel_width=None, gap=0, **kwargs):
        super().__init__(**kwargs)
        self.gap = gap
        self.value = value
        self.panel_width = panel_width
        self.panel = None
        self.panel_holder = Stack()
        self.update()

    def update(self):
        self.controls = [
            Stack(
                horizontal=True,
                border_top="1px solid lightgray",
                controls=[
                    Button(width="100%", text=str(item), action=True, on_click=partial(self.list_selection, item)),
                    Button(height="100%", icon="ChevronRight", on_click=partial(self.list_selection, item)),
                ],
            )
            for item in self.value
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

    def _handle_subform_submit_event(self, event):
        self.update()
        self.page.update()
        self._handle_subform_dismiss_event(event)

    def _handle_subform_dismiss_event(self, event):
        self.panel_holder.controls.pop()
        self.panel_holder.update()


class Form(Stack):

    _step_for_floats = 0.01

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

    _label_alignment_by_control_type = {
        ChoiceGroup: "top",
        DatePicker: "center",
        Grid: "top",
        ListControl: "top",
        SpinButton: "center",
        Stack: "top",
        Textbox: "center",
        Toggle: "top",
    }

    def __init__(
        self,
        value: Any,
        on_submit: callable = None,
        submit_button: Button = None,
        field_validation_default_error_message: str = "Check this value",
        form_validation_error_message: str = "Not all fields have valid values",
        autosave: bool = False,
        label_alignment: str = "left",
        label_width: str = "30%",
        control_style: str = "normal",
        padding: int = 20,
        gap: int = 10,
        width="min(600px, 90%)",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.field_validation_default_error_message = field_validation_default_error_message
        self.form_validation_error_message = form_validation_error_message
        self.autosave = autosave
        self.label_alignment = label_alignment
        self.label_width = label_width
        self.control_style = control_style
        self.padding = padding
        self.gap = gap
        self.width = width

        if type(value) is type:
            self._model = value
            if hasattr(self._model, '__fields__'):
                self.value = self._model.construct()
            else:
                try:
                    self.value = self._model()
                except Exception as error:
                    raise ValueError('Unable to instantiate form data with default values', error)
        else:
            self._model = type(value)
            self.value = value

        self.working_copy = self.autosave and self.value or copy.deepcopy(self.value)
        
        self._fields = {}
        self._messages = {}
        self._pydantic_fields = {}

        self.on_submit = getattr(submit_button, 'on_click', on_submit)

        self._submit_button = submit_button or Button(text="OK", primary=True, icon="CheckMark")
        self._submit_button.on_click = self._submit

        self._form_not_valid_message = Message(value=self.form_validation_error_message, type="error", visible=False)

        self._create_controls()

    def _create_controls(self):
        controls = [
            self._create_control(attribute, attribute_type)
            for attribute, attribute_type in self._model.__annotations__.items()
        ]
        self.controls = controls + [
            Stack(horizontal=True, horizontal_align="end", controls=[self._form_not_valid_message, self._submit_button])
        ]

    def _create_control(self, attribute: str, attribute_type: Any):
        # For unions, we consider only the first type annotation
        if (origin := getattr(attribute_type, '__origin__', None)) and origin == Union:
            attribute_type = attribute_type.__args__[0]

        control_data = SimpleNamespace(
            attribute=attribute,
            attribute_type=attribute_type,
            value=getattr(self.working_copy, attribute),
            label_text=attribute.replace("_", " ").capitalize(),
            placeholder="",
            error_message=self.field_validation_default_error_message,
        )

        control_data = self._check_pydantic_overrides(control_data)

        handle_change_func = partial(self._handle_field_submit_event, attribute)

        control = None

        if origin == list and len(attribute_type.__args__) == 1:
            control = self._create_list_control(control_data)
        elif type(attribute_type).__name__ == "EnumMeta":
            control = self._create_multiple_choice_control(control_data)
        else:
            control = self._create_basic_control(control_data)

        if not control:
            raise ValueError("Could not create control", control_data)

        control.on_change = handle_change_func

        if self.control_style == 'line':
            try:
                control.underlined = True
                control.borderless = True
            except AttributeError:
                pass

        self._fields[attribute] = control

        message = Message(value=control_data.error_message, type="error", visible=False)
        self._messages[attribute] = message

        control_stack = Stack(
            controls=[
                control,
                message,
            ],
            on_submit=handle_change_func,
            width="100%",
        )

        if hasattr(control, "label"):
            control.label = None

        return Stack(
            horizontal=True,
            controls=[
                Text(
                    value=control_data.label_text,
                    width="30%",
                    bold=True,
                    align=self.label_alignment,
                    vertical_align=self._label_alignment_by_control_type[type(control)],
                ),
                control_stack,
            ],
        )

    def _check_pydantic_overrides(self, control_data):
        pydantic_field = (
            hasattr(self._model, "__fields__") and self.value.__fields__.get(control_data.attribute) or None
        )

        if pydantic_field:
            self._pydantic_fields[control_data.attribute] = pydantic_field
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

    def _create_multiple_choice_control(self, control_data):
        enum_type = control_data.attribute_type
        return ChoiceGroup(
            options=[choicegroup.Option(key=option.value, text=option.value.title()) for option in enum_type],
            value=enum_type(control_data.value).value,
        )

    def _create_list_control(self, control_data):
        return ListControl(value=control_data.value, panel_width=self.width)

    def _handle_field_submit_event(self, attribute, event):
        self._validate_value(attribute)

    def _validate_value(self, attribute):
        is_valid = True
        control = self._fields[attribute]

        if pydantic_field := self._pydantic_fields.get(attribute):
            value, error = pydantic_field.validate(
                control.value,
                self.working_copy.dict(),
                loc=attribute,
                cls=self._model,
            )
            if error:
                is_valid = False
            else:
                # Validation can change the value, update control
                if type(value) is datetime.date:
                    value = value.isoformat()
                control.value = value

        if is_valid:
            try:
                setattr(self.working_copy, attribute, control.value)
            except ValueError:
                is_valid = False

        self._messages[attribute].visible = not is_valid
        self.page.update()
        return is_valid

    def _submit(self, e):
        if not all(self._validate_value(attribute) for attribute in self._fields):
            # self._form_not_valid_message.value = self.form_validation_error_message
            # self._form_not_valid_message.visible = True
            self._submit_button.primary = False
            original_icon = self._submit_button.icon
            self._submit_button.icon = "Cancel"
            self.page.update()
            time.sleep(5)
            # self._form_not_valid_message.visible = False
            self._submit_button.primary = True
            self._submit_button.icon = "CheckMark"
            self.page.update()
        else:
            if not self.autosave:
                self.value.__dict__.update(self.working_copy.__dict__)
            if self.on_submit:
                self.on_submit(ControlEvent(self._submit_button, 'submit', None, self, self.page))
