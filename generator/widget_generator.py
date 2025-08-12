# generator/widget_generator.py
# FIXED VERSION - Handles Text widgets, enums, and CarouselSlider properly

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

    def _decode_html_deeply(self, value):
        """Decode HTML entities multiple times to handle nested encoding"""
        import html
        if isinstance(value, str):
            decoded = value
            # Decode up to 5 times to handle deep nesting
            for _ in range(5):
                prev = decoded
                decoded = html.unescape(decoded)
                if decoded == prev:
                    break
            return decoded
        elif isinstance(value, dict):
            return {self._decode_html_deeply(k): self._decode_html_deeply(v)
                    for k, v in value.items()}
        elif isinstance(value, list):
            return [self._decode_html_deeply(item) for item in value]
        else:
            return value

    def generate_widget(self, component_data: Dict[str, Any]) -> str:
        """Generate widget code from component data"""
        try:
            from .models import WidgetType

            # Decode all HTML entities in component data first
            component_data = self._decode_html_deeply(component_data)

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

            # Special handling for specific widgets
            if widget_type_name == 'CarouselSlider':
                return self._generate_carousel_slider(component_data)
            elif widget_type_name == 'Text':
                return self._generate_text_widget(component_data)
            elif widget_type_name == 'Icon':
                return self._generate_icon_widget(component_data)
            elif widget_type_name in ['IconButton', 'FloatingActionButton']:
                return self._generate_button_widget(component_data)
            elif widget_type_name == 'Badge':
                return self._generate_badge_widget(component_data)

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
            # Validate and clean before returning
            code = self._validate_and_clean_output(code)
            return code

        except Exception as e:
            logger.error(f"Error generating widget: {str(e)}")
            return self._generate_fallback_widget(component_data)

    def _generate_text_widget(self, component_data: Dict[str, Any]) -> str:
        """Special handling for Text widget to ensure data is always present"""
        props = component_data.get('properties', {})

        # Decode properties deeply first
        props = self._decode_html_deeply(props)

        # Get text data - REQUIRED for Text widget
        text_data = props.get('data', props.get('text', 'Text'))

        # Additional safety - decode again if needed
        text_data = self._decode_html_deeply(str(text_data))

        # Escape single quotes in text
        text_data = text_data.replace("'", "\\'")

        # Handle text style
        style_props = []
        if 'style' in props:
            style = props['style']
            if isinstance(style, dict):
                if 'fontSize' in style:
                    style_props.append(f"fontSize: {style['fontSize']}.0")
                if 'fontWeight' in style:
                    weight = style['fontWeight']
                    if not weight.startswith('FontWeight.'):
                        weight = f"FontWeight.{weight}"
                    style_props.append(f"fontWeight: {weight}")
                if 'color' in style:
                    from .property_handlers import ColorPropertyHandler
                    color_handler = ColorPropertyHandler()
                    color = color_handler.transform(style['color'])
                    style_props.append(f"color: {color}")
        elif 'fontSize' in props:
            style_props.append(f"fontSize: {props['fontSize']}.0")

        # Build Text widget
        if style_props:
            style = f"TextStyle({', '.join(style_props)})"
            return f"Text('{text_data}', style: {style})"
        else:
            return f"Text('{text_data}')"

    def _generate_carousel_slider(self, component_data: Dict[str, Any]) -> str:
        """Special handling for CarouselSlider with proper structure"""
        props = component_data.get('properties', {})

        # Process items
        items = props.get('items', [])
        items_code = []

        for item in items:
            if isinstance(item, dict):
                item_code = self.generate_widget(item)
                items_code.append(item_code)
            else:
                items_code.append("Container()")

        if not items_code:
            items_code = ["Container(color: Colors.grey, child: Center(child: Text('Slide 1')))"]

        # Process options
        options = props.get('options', {})
        option_props = []

        if isinstance(options, dict):
            if 'height' in options:
                option_props.append(f"height: {options['height']}.0")
            if 'autoPlay' in options:
                option_props.append(f"autoPlay: {str(options['autoPlay']).lower()}")
            if 'autoPlayInterval' in options:
                interval = options['autoPlayInterval']
                if isinstance(interval, (int, float)):
                    option_props.append(f"autoPlayInterval: Duration(milliseconds: {int(interval)})")
            if 'viewportFraction' in options:
                option_props.append(f"viewportFraction: {options['viewportFraction']}")
            if 'enlargeCenterPage' in options:
                option_props.append(f"enlargeCenterPage: {str(options['enlargeCenterPage']).lower()}")

        # Default height if not specified
        if not any('height' in prop for prop in option_props):
            option_props.append("height: 200.0")

        # Build CarouselSlider
        options_str = f"CarouselOptions({', '.join(option_props)})" if option_props else "CarouselOptions(height: 200.0)"

        items_str = "[\n    " + ",\n    ".join(items_code) + "\n  ]"

        return f"CarouselSlider(\n  options: {options_str},\n  items: {items_str},\n)"

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

        # Clean raw properties first
        if isinstance(raw_properties, dict):
            cleaned_props = {}
            for key, value in raw_properties.items():
                # Skip None values and "None" strings
                if value is None or value == "None" or value == ["None"]:
                    continue
                cleaned_props[key] = value
            raw_properties = cleaned_props

        # Special handling for Text widget
        if widget_type.name == 'Text':
            return []

        # Get all property definitions for this widget
        property_defs = widget_type.properties.all()

        for prop_def in property_defs:
            prop_name = prop_def.name

            # Get value from raw properties
            if prop_name in raw_properties:
                prop_value = raw_properties[prop_name]

                # Skip None values
                if prop_value is None or prop_value == "None":
                    continue

                # Decode HTML entities if string
                prop_value = self._decode_html_deeply(prop_value)
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

            # Special handling for enum properties
            if prop_def.property_type == 'enum':
                # Common Flutter enums
                if prop_name == 'mainAxisAlignment':
                    handler_kwargs = {
                        'enum_class': 'MainAxisAlignment',
                        'allowed_values': ['start', 'end', 'center', 'spaceBetween', 'spaceAround', 'spaceEvenly']
                    }
                elif prop_name == 'crossAxisAlignment':
                    handler_kwargs = {
                        'enum_class': 'CrossAxisAlignment',
                        'allowed_values': ['start', 'end', 'center', 'stretch', 'baseline']
                    }
                elif prop_name == 'textAlign':
                    handler_kwargs = {
                        'enum_class': 'TextAlign',
                        'allowed_values': ['left', 'right', 'center', 'justify', 'start', 'end']
                    }
                elif prop_name == 'fit':
                    handler_kwargs = {
                        'enum_class': 'BoxFit',
                        'allowed_values': ['fill', 'contain', 'cover', 'fitWidth', 'fitHeight', 'none', 'scaleDown']
                    }
                elif prop_def.allowed_values:
                    handler_kwargs = {
                        'enum_class': prop_def.dart_type.split('.')[
                            0] if '.' in prop_def.dart_type else prop_def.dart_type,
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

            # Check if the value is still a raw dict/map (wasn't properly transformed)
            if isinstance(dart_value, dict):
                # This shouldn't be a raw dict in Flutter code
                if prop_name == 'padding':
                    # Force EdgeInsets transformation
                    edge_handler = self.handler_factory.get_handler('edge_insets')
                    dart_value = edge_handler.transform(prop_value)
                elif prop_name == 'decoration':
                    # Handle decoration - if it's empty or has null gradient, just use null
                    if not prop_value or prop_value.get('gradient') is None:
                        dart_value = "null"
                    else:
                        # Process decoration properly
                        dart_value = "BoxDecoration()"  # Placeholder for now
                else:
                    # For other properties, skip if it's an empty dict
                    dart_value = "null"

            # Don't output raw Python dict syntax
            if str(dart_value).startswith('{') and str(dart_value).endswith('}') and ':' in str(dart_value):
                dart_value = "null"  # Fallback to null instead of invalid syntax

            processed.append({
                'name': prop_name,
                'value': dart_value,
                'type': prop_def.property_type,
                'is_required': prop_def.is_required
            })

        # Handle any extra properties not defined in the schema
        defined_props = {p.name for p in property_defs}
        for prop_name, prop_value in raw_properties.items():
            if prop_name not in defined_props and prop_name not in ['items', 'options']:
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
            # Check if it's an enum value (contains no spaces and is lowercase or camelCase)
            elif not ' ' in value and (value.islower() or value[0].islower()):
                # Try to detect common enum patterns
                if name == 'mainAxisAlignment':
                    return f"MainAxisAlignment.{value}"
                elif name == 'crossAxisAlignment':
                    return f"CrossAxisAlignment.{value}"
                else:
                    handler = self.handler_factory.get_handler('string')
            else:
                handler = self.handler_factory.get_handler('string')
        elif isinstance(value, dict):
            # Could be a widget or complex property
            if 'type' in value:
                return self.generate_widget(value)
            elif name == 'padding':
                # Special case for padding
                handler = self.handler_factory.get_handler('edge_insets')
                return handler.transform(value)
            elif name == 'margin':
                # Special case for margin
                handler = self.handler_factory.get_handler('edge_insets')
                return handler.transform(value)
            elif name == 'decoration':
                # Special case for decoration
                if not value or all(v is None for v in value.values()):
                    return "null"
                return "BoxDecoration()"  # Basic decoration
            else:
                # For other dicts, return null instead of raw dict
                return "null"
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

        # Handle various input formats
        if not children_data:
            return []

        # If it's the string "None", return empty list
        if children_data == "None" or children_data == ["None"]:
            return []

        # Handle if it's not a list
        if not isinstance(children_data, list):
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
        import html

        try:
            template = Template(template_string)
            context = Context({
                'widget_name': widget_type.dart_class_name,
                'properties': properties,
                'children': children or [],
                'widget_type': widget_type,
            })

            rendered = template.render(context).strip()
            # Check for raw Python dict syntax and replace with null
            import re
            # Pattern to match Python dict syntax like {'key': value}
            dict_pattern = r"\{['\"][\w]+['\"]\s*:\s*[^}]+\}"
            rendered = re.sub(dict_pattern, 'null', rendered)

            # Also check for simple {'word': null} patterns
            rendered = re.sub(r"\{['\"]?\w+['\"]?\s*:\s*null\}", 'null', rendered)

            # Final safety check - decode any remaining HTML entities
            for _ in range(5):
                prev = rendered
                rendered = html.unescape(rendered)
                if rendered == prev:
                    break

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
        """Generate required import statements with CarouselSlider fix"""
        imports = set()
        imports.add("import 'package:flutter/material.dart';")

        # Check if carousel_slider is used
        uses_carousel = False

        # Collect all widget types used
        widget_types = set()
        for component in components:
            widget_type_name = component.get('type')
            if widget_type_name:
                widget_types.add(widget_type_name)
                if widget_type_name == 'CarouselSlider':
                    uses_carousel = True

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
                        # Special handling for carousel_slider to avoid conflicts
                        if package_name == 'carousel_slider':
                            # Import with hide to avoid CarouselController conflict
                            imports.add(f"import 'package:{package_name}/{package_name}.dart';")
                        else:
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

        # Special validation for Text widget
        if widget_type_name == 'Text':
            props = component_data.get('properties', {})
            if not props.get('data') and not props.get('text'):
                result['warnings'].append("Text widget should have 'data' or 'text' property")

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

    def _decode_html_entities(self, value):
        """Recursively decode HTML entities"""
        import html
        if isinstance(value, str):
            decoded = value
            for _ in range(3):
                prev = decoded
                decoded = html.unescape(decoded)
                if decoded == prev:
                    break
            return decoded
        elif isinstance(value, dict):
            return {self._decode_html_entities(k): self._decode_html_entities(v)
                    for k, v in value.items()}
        elif isinstance(value, list):
            return [self._decode_html_entities(item) for item in value]
        else:
            return value

    def _generate_icon_widget(self, component_data: Dict[str, Any]) -> str:
        """Special handling for Icon widget"""
        props = self._decode_html_deeply(component_data.get('properties', {}))

        # Icon requires an icon data parameter
        icon_name = props.get('icon', 'Icons.info')

        # Clean up icon name
        if not icon_name.startswith('Icons.'):
            icon_name = f'Icons.{icon_name}'

        # Build icon widget
        parts = [icon_name]

        if 'size' in props:
            parts.append(f"size: {props['size']}.0")
        if 'color' in props:
            from .property_handlers import ColorPropertyHandler
            color_handler = ColorPropertyHandler()
            color = color_handler.transform(props['color'])
            parts.append(f"color: {color}")

        if len(parts) > 1:
            return f"Icon({parts[0]}, {', '.join(parts[1:])})"
        else:
            return f"Icon({icon_name})"

    def _generate_button_widget(self, component_data: Dict[str, Any]) -> str:
        """Special handling for button widgets that require onPressed"""
        widget_type_name = component_data.get('type')
        props = self._decode_html_deeply(component_data.get('properties', {}))

        # Ensure onPressed is present
        if 'onPressed' not in props:
            props['onPressed'] = '() {}'

        # Handle IconButton specifically
        if widget_type_name == 'IconButton':
            icon_props = props.get('icon', {})
            if isinstance(icon_props, dict):
                icon_code = self.generate_widget(icon_props)
            else:
                icon_code = "Icon(Icons.info)"

            return f"IconButton(icon: {icon_code}, onPressed: {props['onPressed']})"

        # Handle FloatingActionButton
        elif widget_type_name == 'FloatingActionButton':
            child_props = props.get('child', {})
            if isinstance(child_props, dict):
                child_code = self.generate_widget(child_props)
            else:
                child_code = "Icon(Icons.add)"

            parts = [f"onPressed: {props['onPressed']}", f"child: {child_code}"]

            if 'backgroundColor' in props:
                from .property_handlers import ColorPropertyHandler
                color_handler = ColorPropertyHandler()
                color = color_handler.transform(props['backgroundColor'])
                parts.append(f"backgroundColor: {color}")

            return f"FloatingActionButton({', '.join(parts)})"

        # Default button handling
        return self._generate_fallback_widget(component_data)

    def _generate_badge_widget(self, component_data: Dict[str, Any]) -> str:
        """Handle Badge widget with automatic fallback"""
        props = self._decode_html_deeply(component_data.get('properties', {}))

        # Check if badges package is available (you'd check this from project packages)
        # For now, we'll create a custom badge implementation

        child_props = props.get('child', {})
        if isinstance(child_props, dict):
            child_code = self.generate_widget(child_props)
        else:
            child_code = "Container()"

        badge_content = props.get('badgeContent', {})
        if isinstance(badge_content, dict):
            badge_code = self.generate_widget(badge_content)
        else:
            badge_code = "Text('0')"

        badge_color = props.get('badgeColor', 'red')
        from .property_handlers import ColorPropertyHandler
        color_handler = ColorPropertyHandler()
        color = color_handler.transform(badge_color)

        # Create inline Badge widget that always works
        return f"""Stack(
          clipBehavior: Clip.none,
          children: [
            {child_code},
            Positioned(
              right: -8,
              top: -8,
              child: Container(
                padding: EdgeInsets.all(2),
                decoration: BoxDecoration(
                  color: {color},
                  borderRadius: BorderRadius.circular(10),
                ),
                constraints: BoxConstraints(
                  minWidth: 20,
                  minHeight: 20,
                ),
                child: Center(
                  child: {badge_code},
                ),
              ),
            ),
          ],
        )"""

    def _validate_and_clean_output(self, code: str) -> str:
        """Validate and clean generated widget code"""
        import re

        # Remove any "None" values
        code = re.sub(r'\bNone\b', 'null', code)

        # Remove any undefined prefixes (like badges. if package not available)
        code = re.sub(r'\bbadges\.', '', code)

        # Fix any remaining HTML entities
        import html
        for _ in range(3):
            prev = code
            code = html.unescape(code)
            if code == prev:
                break

        # Remove invalid property assignments
        code = re.sub(r',\s*,', ',', code)  # Remove double commas
        code = re.sub(r',\s*\)', ')', code)  # Remove trailing commas before )
        code = re.sub(r',\s*\]', ']', code)  # Remove trailing commas before ]

        return code