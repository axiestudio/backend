from axiestudio.base.prompts.api_utils import process_prompt_template
from axiestudio.custom.custom_component.component import Component
from axiestudio.inputs.inputs import DefaultPromptField
from axiestudio.io import MessageTextInput, Output, PromptInput
from axiestudio.schema.message import Message
from axiestudio.template.utils import update_template_values


class PromptComponent(Component):
    display_name: str = "Promptmall"
    description: str = "Skapa en promptmall med dynamiska variabler."
    documentation: str = "https://docs.axiestudio.org/components-prompts"
    icon = "braces"
    trace_type = "prompt"
    name = "Prompt Template"
    priority = 0  # Set priority to 0 to make it appear first

    inputs = [
        PromptInput(name="template", display_name="Mall"),
        MessageTextInput(
            name="tool_placeholder",
            display_name="Verktygsplatshållare",
            tool_mode=True,
            advanced=True,
            info="En platshållarinmatning för verktygsläge.",
        ),
    ]

    outputs = [
        Output(display_name="Prompt", name="prompt", method="build_prompt"),
    ]

    async def build_prompt(self) -> Message:
        prompt = Message.from_template(**self._attributes)
        self.status = prompt.text
        return prompt

    def _update_template(self, frontend_node: dict):
        prompt_template = frontend_node["template"]["template"]["value"]
        custom_fields = frontend_node["custom_fields"]
        frontend_node_template = frontend_node["template"]
        _ = process_prompt_template(
            template=prompt_template,
            name="template",
            custom_fields=custom_fields,
            frontend_node_template=frontend_node_template,
        )
        return frontend_node

    async def update_frontend_node(self, new_frontend_node: dict, current_frontend_node: dict):
        """This function is called after the code validation is done."""
        frontend_node = await super().update_frontend_node(new_frontend_node, current_frontend_node)
        template = frontend_node["template"]["template"]["value"]
        # Kept it duplicated for backwards compatibility
        _ = process_prompt_template(
            template=template,
            name="template",
            custom_fields=frontend_node["custom_fields"],
            frontend_node_template=frontend_node["template"],
        )
        # Now that template is updated, we need to grab any values that were set in the current_frontend_node
        # and update the frontend_node with those values
        update_template_values(new_template=frontend_node, previous_template=current_frontend_node["template"])
        return frontend_node

    def _get_fallback_input(self, **kwargs):
        return DefaultPromptField(**kwargs)
