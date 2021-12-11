import datetime
import time

from functools import partial
from typing import Any, Union

from pglet import Button, ChoiceGroup, DatePicker, Message, SpinButton, Stack, Textbox, Toggle
from pglet import choicegroup


class Form(Stack):

    step_for_floats = .01

    float_button = partial(SpinButton, step=step_for_floats)

    from_data_type_to_form_control = {

        # Standard library types
        'int': SpinButton,
        'float': float_button,
        'Decimal': float_button,
        'bool': Toggle,
        'datetime': Textbox,
        'date': DatePicker,
        'time': Textbox,

        # pydantic types
        # 'SecretStr': , not supported by pglet
        'ConstrainedIntValue': SpinButton,
        'NegativeIntValue': SpinButton,
        'PositiveIntValue': SpinButton,
        'StrictIntValue': SpinButton,
        'ConstrainedFloatValue': float_button,
        'NegativeFloatValue': float_button,
        'PositiveFloatValue': float_button,
        'StrictFloatValue': float_button,
        'ConstrainedDecimalValue': float_button,
        'StrictBoolValue': Toggle,
        'EmailStrValue': Textbox,
        'PastDateValue': DatePicker,
        'FutureDateValue': DatePicker,
    }

    def __init__(self, value, page, on_submit=None, submit_button=None, **kwargs):
        super().__init__(**kwargs)
        self.page = page

        if type(value) is type:
            self.model = value
            if hasattr(self.model, '__fields__'):
                self.value = self.model.construct()
            else:
                self.value = self.model()
        else:
            self.model = type(value)
            self.value = value
        
        self.fields = {}
        self.messages = {}
        self.pydantic_fields = {}

        self.on_submit = getattr(submit_button, 'on_click', on_submit)

        self._submit_button = submit_button or Button(text="OK", primary=True, icon="CheckMark")
        self._submit_button.on_click = self._submit

        self._form_not_valid_message = Message(value="Not all fields are valid", type="error", visible=False)

        self._create_controls()

    def _create_controls(self):
        self.controls = [
            self._create_control(attribute, attribute_type)
            for attribute, attribute_type in self.model.__annotations__.items()
        ] + [self._submit_button, self._form_not_valid_message]

    def _create_control(self, attribute: str, attribute_type: Any, label=True):
        if (origin := getattr(attribute_type, '__origin__', None)) and origin == Union:
            attribute_type = attribute_type.__args__[0]

        value=getattr(self.value, attribute)
        label_text = attribute.replace('_', ' ').capitalize()
        placeholder = ''
        error_message = 'Check this value'

        # pydantic support
        pydantic_field = hasattr(self.model, '__fields__') and self.value.__fields__.get(attribute) or None

        if pydantic_field:
            self.pydantic_fields[attribute] = pydantic_field
            label_text = pydantic_field.field_info.title or label_text
            placeholder = pydantic_field.field_info.description or ''
            if placeholder:
                error_message = placeholder

        validate_func = partial(self._handle_field_submit_event, attribute)

        if type(attribute_type).__name__ == 'EnumMeta':
            control = ChoiceGroup(
                label=label_text,
                options=[
                    choicegroup.Option(key=option.value, text=option.value.title())
                    for option in attribute_type
                ],
                value=attribute_type(value).value,
                on_change=validate_func,
            )
        else:
            control_type = self.from_data_type_to_form_control.get(attribute_type.__name__, Textbox)
            control = control_type(label=label_text, value=value)
            if control_type is Textbox:
                control.placeholder = placeholder

        self.fields[attribute] = control

        message = Message(value=error_message, type='error', visible=False)
        self.messages[attribute] = message

        return Stack(
            controls=[
                control,
                message,
            ],
            on_submit=validate_func,
        )

    def _handle_field_submit_event(self, attribute, event):
        self._validate_value(attribute)

    def _validate_value(self, attribute):
        is_valid = True
        control = self.fields[attribute]

        try:
            setattr(self.value, attribute, control.value)
        except ValueError:
            self.messages[attribute].visible = True
            is_valid = False
        else:
            self.messages[attribute].visible = False
            if pydantic_field := self.pydantic_fields.get(attribute):
                value, error = pydantic_field.validate(
                    control.value,
                    self.value.dict(),
                    loc=attribute,
                    cls=self.model,
                )
                if error:
                    self.messages[attribute].visible = True
                    is_valid = False
                else:
                    print(attribute, value)
                    if type(value) is datetime.date:
                        value = value.isoformat()
                    control.value = value

        self.page.update()
        return is_valid

    def _submit(self, e):
        if not all(self._validate_value(attribute) for attribute in self.fields):
            self._form_not_valid_message.visible = True
            self.page.update()
            time.sleep(5)
            self._form_not_valid_message.visible = False
            self.page.update()
        elif self.on_submit:
            self.on_submit(self)
