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
