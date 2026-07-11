"""Template renderer stub"""


class TemplateRenderer:
    def render(self, template_name: str, context: dict) -> str:
        return f"Template: {template_name}, Context: {context}"


template_renderer = TemplateRenderer()
