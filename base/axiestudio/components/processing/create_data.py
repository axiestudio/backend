from typing import Any

from axiestudio.custom.custom_component.component import Component
from axiestudio.field_typing.range_spec import RangeSpec
from axiestudio.inputs.inputs import BoolInput, DictInput, IntInput, MessageTextInput
from axiestudio.io import Output
from axiestudio.schema.data import Data
from axiestudio.schema.dotdict import dotdict


class CreateDataComponent(Component):
    display_name: str = "Skapa data"
    description: str = "Skapa dynamiskt en Data med ett angivet antal fält."
    name: str = "CreateData"
    MAX_FIELDS = 15  # Define a constant for maximum number of fields
    legacy = True
    icon = "ListFilter"

    inputs = [
        IntInput(
            name="number_of_fields",
            display_name="Antal fält",
            info="Antal fält som ska läggas till posten.",
            real_time_refresh=True,
            value=1,
            range_spec=RangeSpec(min=1, max=MAX_FIELDS, step=1, step_type="int"),
        ),
        MessageTextInput(
            name="text_key",
            display_name="Textnyckel",
            info="Nyckel som identifierar fältet som ska användas som textinnehåll.",
            advanced=True,
        ),
        BoolInput(
            name="text_key_validator",
            display_name="Textnyckelvalidator",
            advanced=True,
            info="Om aktiverad, kontrollerar om den angivna 'Textnyckeln' finns i den angivna 'Data'.",
        ),
    ]

    outputs = [
        Output(display_name="Data", name="data", method="build_data"),
    ]

    def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None):
        if field_name == "number_of_fields":
            default_keys = ["code", "_type", "number_of_fields", "text_key", "text_key_validator"]
            try:
                field_value_int = int(field_value)
            except ValueError:
                return build_config
            existing_fields = {}
            if field_value_int > self.MAX_FIELDS:
                build_config["number_of_fields"]["value"] = self.MAX_FIELDS
                msg = (
                    f"Number of fields cannot exceed {self.MAX_FIELDS}. "
                    "Please adjust the number of fields to be within the allowed limit."
                )
                raise ValueError(msg)
            if len(build_config) > len(default_keys):
                # back up the existing template fields
                for key in build_config.copy():
                    if key not in default_keys:
                        existing_fields[key] = build_config.pop(key)

            for i in range(1, field_value_int + 1):
                key = f"field_{i}_key"
                if key in existing_fields:
                    field = existing_fields[key]
                    build_config[key] = field
                else:
                    field = DictInput(
                        display_name=f"Field {i}",
                        name=key,
                        info=f"Key for field {i}.",
                        input_types=["Message", "Data"],
                    )
                    build_config[field.name] = field.to_dict()

            build_config["number_of_fields"]["value"] = field_value_int
        return build_config

    async def build_data(self) -> Data:
        data = self.get_data()
        return_data = Data(data=data, text_key=self.text_key)
        self.status = return_data
        if self.text_key_validator:
            self.validate_text_key()
        return return_data

    def get_data(self):
        """Function to get the Data from the attributes."""
        data = {}
        for value_dict in self._attributes.values():
            if isinstance(value_dict, dict):
                # Check if the value of the value_dict is a Data
                value_dict_ = {
                    key: value.get_text() if isinstance(value, Data) else value for key, value in value_dict.items()
                }
                data.update(value_dict_)
        return data

    def validate_text_key(self) -> None:
        """This function validates that the Text Key is one of the keys in the Data."""
        data_keys = self.get_data().keys()
        if self.text_key not in data_keys and self.text_key != "":
            formatted_data_keys = ", ".join(data_keys)
            msg = f"Text Key: '{self.text_key}' not found in the Data keys: '{formatted_data_keys}'"
            raise ValueError(msg)
