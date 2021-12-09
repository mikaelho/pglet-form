from functools import partial
from typing import Any

from pglet import ChoiceGroup, DatePicker, SpinButton, Stack, Textbox, Toggle
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

    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)

        if type(data) is type:
            self.model = data
            if hasattr(self.model, '__fields__'):
                self.data = self.model.construct()
            else:
                self.data = self.model()
        else:
            self.model = type(data)
            self.data = data
        self.fields = {}

        self.controls = self._create_controls()

    def _create_controls(self):
        return [
            self._create_control(attribute, attribute_type)
            for attribute, attribute_type in self.model.__annotations__.items()
        ]

    def _create_control(self, attribute: str, attribute_type: Any):
        value=getattr(self.data, attribute)
        label_text = attribute.replace('_', ' ').capitalize()
        content_hint = ''

        # pydantic support
        pydantic_field = hasattr(self.model, '__fields__') and self.data.__fields__.get(attribute) or None

        if pydantic_field:
            label_text = pydantic_field.field_info.title or label_text
            content_hint = pydantic_field.field_info.description or ''

        if type(attribute_type).__name__ == 'EnumMeta':
            control = ChoiceGroup(
                label=label_text,
                options=[
                    choicegroup.Option(key=option.name, text=option.value.title())
                    for option in attribute_type
                ],
                value=attribute_type(value).name,
            )
        else:
            control_type = self.from_data_type_to_form_control.get(attribute_type.__name__, Textbox)
            control = control_type(label=label_text, value=value)
            if control_type is Textbox:
                control.placeholder = content_hint

        self.fields[attribute] = control

        return control
