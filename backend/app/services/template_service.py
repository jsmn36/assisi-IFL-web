from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
    TemplateNotFound,
    meta,
)
from pathlib import Path
from typing import Dict, List
from premailer import transform
import logging

logger = logging.getLogger(__name__)  # ✅ FIXED


class TemplateService:
    """
    Service for email template rendering

    Features:
    - Jinja2 template engine
    - CSS inlining for email compatibility
    - Variable substitution
    - Template inheritance
    - Custom filters
    """

    def __init__(self, template_dir: str = "app/templates/emails"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters
        self.env.filters["currency"] = self.format_currency
        self.env.filters["date"] = self.format_date
        self.env.filters["datetime"] = self.format_datetime

    def render_template(
        self,
        template_name: str,
        context: Dict,
        inline_css: bool = True,
    ) -> str:
        """Render HTML email template"""
        try:
            template = self.env.get_template(template_name)
            html = template.render(**context)

            if inline_css:
                html = transform(html)

            return html

        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            logger.exception(f"Error rendering template {template_name}")
            raise

    def render_text_template(
        self,
        template_name: str,
        context: Dict,
    ) -> str:
        """Render plain text email template"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception:
            logger.exception(f"Error rendering text template {template_name}")
            raise

    def get_template_variables(self, template_name: str) -> List[str]:
        """Get list of variables used in template"""
        try:
            source, _, _ = self.env.loader.get_source(
                self.env, template_name
            )  # ✅ FIXED
            parsed = self.env.parse(source)
            variables = list(meta.find_undeclared_variables(parsed))
            return variables
        except Exception:
            logger.exception("Error getting template variables")
            return []

    def list_templates(self) -> List[str]:
        """List all available templates"""
        return [
            str(template_file.relative_to(self.template_dir))
            for template_file in self.template_dir.rglob("*.html")
        ]

    # -------------------------
    # Custom Filters
    # -------------------------

    @staticmethod
    def format_currency(value: float) -> str:
        """Format as currency"""
        try:
            return f"${value:,.2f}"
        except Exception:
            return str(value)

    @staticmethod
    def format_date(value) -> str:
        """Format date"""
        from datetime import date, datetime

        try:
            if isinstance(value, str):
                value = datetime.fromisoformat(value).date()
            elif isinstance(value, datetime):
                value = value.date()

            if isinstance(value, date):
                return value.strftime("%B %d, %Y")

        except (TypeError, ValueError):
            logger.debug("format_date fallback for value=%r", value)

        return str(value)

    @staticmethod
    def format_datetime(value) -> str:
        """Format datetime"""
        from datetime import datetime

        try:
            if isinstance(value, str):
                value = datetime.fromisoformat(value)

            if isinstance(value, datetime):
                return value.strftime("%B %d, %Y at %I:%M %p")

        except (TypeError, ValueError):
            logger.debug("format_datetime fallback for value=%r", value)

        return str(value)


# Global template service instance
template_service = TemplateService()
