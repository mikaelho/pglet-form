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

        self.on_submit = getattr(submit_button, 'on_click', on_submit)

        submit_button = submit_button or Button(text='OK', primary=True, icon='OK')

        submit_button.on_click = self._submit

        self.controls = self._create_controls() + [submit_button]

    def _create_controls(self):
        return [
            self._create_control(attribute, attribute_type)
            for attribute, attribute_type in self.model.__annotations__.items()
        ]

    def _create_control(self, attribute: str, attribute_type: Any):
        if (origin := getattr(attribute_type, '__origin__', None)) and origin == Union:
            attribute_type = attribute_type.__args__[0]

        value=getattr(self.value, attribute)
        label_text = attribute.replace('_', ' ').capitalize()
        placeholder = ''
        error_message = 'Check this value'

        # pydantic support
        pydantic_field = hasattr(self.model, '__fields__') and self.value.__fields__.get(attribute) or None

        if pydantic_field:
            label_text = pydantic_field.field_info.title or label_text
            placeholder = pydantic_field.field_info.description or ''
            if placeholder:
                error_message = placeholder

        validate_func = partial(
            self._validate_value, attribute, attribute_type, pydantic_field
        )

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

        submit_wrapper = Stack(
            controls=[
                control,
                message,
            ],
            on_submit=validate_func,
        )

        return submit_wrapper

    def _validate_value(self, attribute, attribute_type, pydantic_field, e):
        control = self.fields[attribute]
        setattr(self.value, attribute, control.value)
        print('set', attribute, control.value)
        if pydantic_field:
            value, error = pydantic_field.validate(
                control.value,
                self.value.dict(),
                loc=attribute,
                cls=self.model,
            )
            if error:
                self.messages[attribute].visible = True
            else:
                self.messages[attribute].visible = False
                control.value = value
            self.page.update()
            time.sleep(10)
            self.messages[attribute].visible = False
            self.page.update()

    def _submit(self, e):
        try:
            self.model(**self.value.asdict())
        except Exception as error:
            print('Ah no!', error)
        else:
            if self.on_submit:
                self.on_submit(self)
