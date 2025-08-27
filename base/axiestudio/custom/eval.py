from typing import TYPE_CHECKING

from axiestudio.utils import validate

if TYPE_CHECKING:
    from axiestudio.custom.custom_component.custom_component import CustomComponent


def eval_custom_component_code(code: str) -> type["CustomComponent"]:
    """Evaluate custom component code."""
    class_name = validate.extract_class_name(code)
    return validate.create_class(code, class_name)
