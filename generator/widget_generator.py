# generator/widget_generator.py

from django.template import Template, Context
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DynamicWidgetGenerator:
    """Generate Flutter widget code from database definitions"""

    def __init__(self):
        from .property_handlers import PropertyHandlerFactory
        self.handler_factory = PropertyHandlerFactory
        self.widget_cache = {}

    def generate_widget(self, component_data: Dict[str, Any]) -> str:
        """Generate widget code from component data"""
        try:
            from .models import WidgetType

            # Get widget type from database
            widget_type_name = component_data.get('type')
            if not widget_type_name:
                return self._generate_fallback_widget(component_data)

            # Check cache first
            if widget_type_name in self.widget_cache:
                widget_type = self.widget_cache[widget_type_name]
            else:
                try:
                    widget_type = WidgetType.objects.get(name=widget_type_name, is_active=True)
                    self.widget_cache[widget_type_name] = widget_type
                except WidgetType.DoesNotExist:
                    logger.warning(f"Widget type '{widget_type_name}' not found in database")
                    return self._generate_fallback_widget(component_data)

            # Get the template
            template_string = self._get_template(widget_type, component_data)

            # Process properties
            processed_props = self._process_properties(
                widget_type,
                component_data.get('properties', {})
            )

            # Handle children if it's a container
            children = None
            if widget_type.is_container:
                children = self._process_children(component_data.get('children', []))

            # Generate code using template
            code = self._render_template(
                template_string,
                widget_type,
                processed_props,
                children
            )

            return code

        except Exception as e:
            logger.error(f"Error generating widget: {str(e)}")
            return self._generate_fallback_widget(component_data)

    def _get_template(self, widget_type, component_data: Dict) -> str:
        """Get the best matching template for this widget"""

        # Try to find a template with matching conditions
        templates = widget_type.templates.filter(is_active=True).order_by('-priority')

        for template in templates:
            if self._matches_conditions(template.conditions, component_data):
                return template.template_code

        # Fallback to default template
        return self._get_default_template(widget_type)

    def _get_default_template(self, widget_type) -> str:
        """Generate a default template based on widget structure"""

        if widget_type.is_container and widget_type.can_have_multiple_children:
            return """{{ widget_name }}(
{% for prop in properties %}{% if prop.value != "null" %}  {{ prop.name }}: {{ prop.value }},
{% endif %}{% endfor %}{% if children %}  children: [
{% for child in children %}    {{ child }},
{% endfor %}  ],
{% endif %})"""
        elif widget_type.is_container:
            return """{{ widget_name }}(
{% for prop in properties %}{% if prop.value != "null" %}  {{ prop.name }}: {{ prop.value }},
{% endif %}{% endfor %}{% if children %}  child: {{ children.0 }},
{% endif %})"""
        else:
            return """{{ widget_name }}(
{% for prop in properties %}{% if prop.value != "null" %}  {{ prop.name }}: {{ prop.value }},
{% endif %}{% endfor %})"""

    def _process_properties(self, widget_type, raw_properties: Dict) -> List[Dict]:
        """Process properties using appropriate handlers"""

        processed = []

        # Get all property definitions for this widget
        property_defs = widget_type.properties.all()

        for prop_def in property_defs:
            prop_name = prop_def.name

            # Get value from raw properties or use default
            if prop_name in raw_properties:
                prop_value = raw_properties[prop_name]
            elif prop_def.default_value:
                try:
                    prop_value = json.loads(prop_def.default_value)
                except:
                    prop_value = prop_def.default_value
            else:
                prop_value = None

            # Skip non-required null properties
            if prop_value is None and not prop_def.is_required:
                continue

            # Get appropriate handler
            handler_kwargs = {}
            if prop_def.property_type == 'enum' and prop_def.allowed_values:
                handler_kwargs = {
                    'enum_class': prop_def.dart_type.split('.')[0] if '.' in prop_def.dart_type else prop_def.dart_type,
                    'allowed_values': prop_def.allowed_values.get('values', [])
                }
            elif prop_def.property_type in ['widget', 'widget_list']:
                handler_kwargs = {'widget_generator': self}

            handler = self.handler_factory.get_handler(
                prop_def.property_type,
                **handler_kwargs
            )

            # Validate value
            if not handler.validate(prop_value):
                logger.warning(f"Invalid value for {prop_name}: {prop_value}")
                if prop_def.is_required:
                    prop_value = None  # Will use default transform

            # Transform value to Dart code
            dart_value = handler.transform(prop_value)

            processed.append({
                'name': prop_name,
                'value': dart_value,
                'type': prop_def.property_type,
                'is_required': prop_def.is_required
            })

        # Handle any extra properties not defined in the schema
        defined_props = {p.name for p in property_defs}
        for prop_name, prop_value in raw_properties.items():
            if prop_name not in defined_props:
                # Try to guess the type and handle it
                dart_value = self._handle_unknown_property(prop_name, prop_value)
                if dart_value:
                    processed.append({
                        'name': prop_name,
                        'value': dart_value,
                        'type': 'unknown',
                        'is_required': False
                    })

        return processed

    def _handle_unknown_property(self, name: str, value: Any) -> Optional[str]:
        """Handle properties not defined in the widget schema"""

        if value is None:
            return None

        # Try to guess the type based on the value
        if isinstance(value, bool):
            handler = self.handler_factory.get_handler('bool')
        elif isinstance(value, int):
            handler = self.handler_factory.get_handler('int')
        elif isinstance(value, float):
            handler = self.handler_factory.get_handler('double')
        elif isinstance(value, str):
            # Check if it looks like a color
            if value.startswith('#') or value.startswith('0x') or value in ['red', 'blue', 'green']:
                handler = self.handler_factory.get_handler('color')
            else:
                handler = self.handler_factory.get_handler('string')
        elif isinstance(value, dict):
            # Could be a widget or complex property
            if 'type' in value:
                return self.generate_widget(value)
            else:
                handler = self.handler_factory.get_handler('map')
        elif isinstance(value, list):
            # Try to handle as a list
            if value and isinstance(value[0], dict) and 'type' in value[0]:
                # List of widgets
                handler = self.handler_factory.get_handler('widget_list', widget_generator=self)
            else:
                # Generic list - transform each item
                items = []
                for item in value:
                    item_dart = self._handle_unknown_property(f"{name}_item", item)
                    if item_dart:
                        items.append(item_dart)
                return f"[{', '.join(items)}]" if items else "[]"
        else:
            return None

        return handler.transform(value)

    def _process_children(self, children_data: List) -> List[str]:
        """Process child widgets"""

        if not children_data:
            return []

        children = []
        for child_data in children_data:
            if isinstance(child_data, dict):
                child_code = self.generate_widget(child_data)
                children.append(child_code)
            elif isinstance(child_data, str):
                # Direct widget reference
                children.append(child_data)

        return children

    def _render_template(self, template_string: str, widget_type, properties: List[Dict],
                         children: Optional[List] = None) -> str:
        """Render the template with context"""

        try:
            template = Template(template_string)
            context = Context({
                'widget_name': widget_type.dart_class_name,
                'properties': properties,
                'children': children or [],
                'widget_type': widget_type,
            })

            rendered = template.render(context).strip()

            # Clean up extra commas and whitespace
            import re
            rendered = re.sub(r',(\s*[}\)])', r'\1', rendered)
            rendered = re.sub(r'\n\s*\n', '\n', rendered)

            return rendered

        except Exception as e:
            logger.error(f"Template rendering error: {str(e)}")
            return self._generate_fallback_widget({'type': widget_type.name})

    def _matches_conditions(self, conditions: Dict, component_data: Dict) -> bool:
        """Check if component matches template conditions"""

        if not conditions:
            return True

        for key, expected_value in conditions.items():
            actual_value = component_data.get(key)

            # Handle nested keys (e.g., "properties.color")
            if '.' in key:
                keys = key.split('.')
                actual_value = component_data
                for k in keys:
                    if isinstance(actual_value, dict):
                        actual_value = actual_value.get(k)
                    else:
                        actual_value = None
                        break

            # Check if values match
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            elif actual_value != expected_value:
                return False

        return True

    def _generate_fallback_widget(self, component_data: Dict) -> str:
        """Generate a fallback widget when type is not found"""

        widget_type = component_data.get('type', 'Container')
        props = component_data.get('properties', {})

        # Generate simple property list
        prop_strings = []
        for key, value in props.items():
            if isinstance(value, str):
                prop_strings.append(f"{key}: '{value}'")
            elif isinstance(value, bool):
                prop_strings.append(f"{key}: {'true' if value else 'false'}")
            elif isinstance(value, (int, float)):
                prop_strings.append(f"{key}: {value}")

        if prop_strings:
            return f"{widget_type}({', '.join(prop_strings)})"
        else:
            return f"{widget_type}()"

    def generate_imports(self, components: List[Dict]) -> List[str]:
        """Generate required import statements"""

        imports = set()
        imports.add("import 'package:flutter/material.dart';")

        # Collect all widget types used
        widget_types = set()
        for component in components:
            widget_type_name = component.get('type')
            if widget_type_name:
                widget_types.add(widget_type_name)

        # Get imports for each widget type
        from .models import WidgetType
        for widget_type_name in widget_types:
            try:
                widget_type = WidgetType.objects.get(name=widget_type_name)

                # Add package import if needed
                if widget_type.package:
                    if widget_type.import_path:
                        imports.add(f"import '{widget_type.import_path}';")
                    else:
                        package_name = widget_type.package.name
                        imports.add(f"import 'package:{package_name}/{package_name}.dart';")

            except WidgetType.DoesNotExist:
                pass

        return sorted(list(imports))

    def validate_component(self, component_data: Dict) -> Dict[str, Any]:
        """Validate a component definition"""

        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Check if type exists
        widget_type_name = component_data.get('type')
        if not widget_type_name:
            result['valid'] = False
            result['errors'].append("Widget type is required")
            return result

        from .models import WidgetType
        try:
            widget_type = WidgetType.objects.get(name=widget_type_name)
        except WidgetType.DoesNotExist:
            result['warnings'].append(f"Widget type '{widget_type_name}' not found in database")
            return result

        # Validate properties
        props = component_data.get('properties', {})
        required_props = widget_type.properties.filter(is_required=True)

        for prop_def in required_props:
            if prop_def.name not in props:
                result['warnings'].append(f"Required property '{prop_def.name}' is missing")

        # Validate property values
        for prop_def in widget_type.properties.all():
            if prop_def.name in props:
                value = props[prop_def.name]
                handler = self.handler_factory.get_handler(prop_def.property_type)

                if not handler.validate(value):
                    result['errors'].append(
                        f"Invalid value for property '{prop_def.name}': {value}"
                    )
                    result['valid'] = False

        return result