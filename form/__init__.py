from functools import partial

from pglet import DatePicker, SpinButton, Stack, TextBox, Toggle

class Form(Stack):

    step_for_floats = .01

    float_button = partial(SpinButton, step=step_for_floats)

    from_data_type_to_form_control = {

        # Standard library types
        'int': SpinButton,
        'float': float_button,
        'Decimal': float_button,
        'bool': Toggle,
        'datetime': TextBox,
        'date': DatePicker,
        'time': TextBox,

        # pydantic types
        # 'SecretStr': , not supported by pglet
        'ConstrainedInt': SpinButton,
        'NegativeInt': SpinButton,
        'PositiveInt': SpinButton,
        'StrictInt': SpinButton,
        'ConstrainedFloat': float_button,
        'NegativeFloat': float_button,
        'PositiveFloat': float_button,
        'StrictFloat': float_button,
        'ConstrainedDecimal': float_button,
        'StrictBool': Toggle,
        'EmailStr': TextBox,
        'PastDate': DatePicker,
        'FutureDate': DatePicker,
    }

    def __init__(self, width='90%', **kwargs):
        super().__init__(**kwargs)
        self.width = width
        self.horizontal = False

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

        self.controls = _create_controls()

    def _create_controls(self):
        return [
            self._create_control(attribute, attribute_type)
            for attribute, attribute_type in self.model.__annotations__.items()
        ]

    def _create_control(self, attribute: str, attribute_type: Any):
        label_text = attribute.replace('_', ' ').capitalize()
        content_hint = ''

        # pydantic support
        pydantic_field = hasattr(self.model, '__fields__') and self.data.__fields__.get(attribute) or None

        if pydantic_field:
            label_text = pydantic_field.field_info.title or label_text
            content_hint = pydantic_field.field_info.description or ''

        control_type = from_data_type_to_form_control.get(attribute_type, TextBox)
        control = control_type(label=label_text)
        if control_type is TextBox:
            control.placeholder = content_hint

        self.fields[attribute] = control
