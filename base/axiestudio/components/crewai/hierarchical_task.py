from axiestudio.base.agents.crewai.tasks import HierarchicalTask
from axiestudio.custom.custom_component.component import Component
from axiestudio.io import HandleInput, MultilineInput, Output


class HierarchicalTaskComponent(Component):
    display_name: str = "Hierarkisk uppgift"
    description: str = "Varje uppgift måste ha en beskrivning, en förväntad utdata och en agent ansvarig för utförandet."
    icon = "CrewAI"
    legacy = True
    inputs = [
        MultilineInput(
            name="task_description",
            display_name="Beskrivning",
            info="Beskrivande text som detaljerar uppgiftens syfte och utförande.",
        ),
        MultilineInput(
            name="expected_output",
            display_name="Förväntad utdata",
            info="Tydlig definition av förväntat uppgiftsresultat.",
        ),
        HandleInput(
            name="tools",
            display_name="Verktyg",
            input_types=["Tool"],
            is_list=True,
            info="Lista över verktyg/resurser begränsade för uppgiftsutförande. Använder agentverktygen som standard.",
            required=False,
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Task", name="task_output", method="build_task"),
    ]

    def build_task(self) -> HierarchicalTask:
        task = HierarchicalTask(
            description=self.task_description,
            expected_output=self.expected_output,
            tools=self.tools or [],
        )
        self.status = task
        return task
