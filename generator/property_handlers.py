# generator/property_handlers.py
# FIXED VERSION - Better enum handling and validation

from abc import ABC, abstractmethod
import json
import re
from typing import Any, Optional, Dict

def decode_html_entities(value):
    """Recursively decode HTML entities in strings, dicts, and lists"""
    import html
    if isinstance(value, str):
        # Decode multiple times to handle multiple levels of encoding
        decoded = value
        for _ in range(3):  # Decode up to 3 levels deep
            prev = decoded
            decoded = html.unescape(decoded)
            if decoded == prev:
                break
        return decoded
    elif isinstance(value, dict):
        return {decode_html_entities(k): decode_html_entities(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [decode_html_entities(item) for item in value]
    else:
        return value

class PropertyHandler(ABC):
    """Base class for property value handlers"""

    @abstractmethod
    def transform(self, value: Any, context: Optional[Dict] = None) -> str:
        """Transform a Python value to Dart code"""
        pass

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate if the value is acceptable"""
        pass

    def get_default(self) -> str:
        """Get default Dart value"""
        return "null"


class StringPropertyHandler(PropertyHandler):
    def transform(self, value, context=None):
        if value is None:
            return "{}"

        if isinstance(value, dict):
            import html
            items = []
            for k, v in value.items():
                # Decode HTML entities in keys
                clean_key = html.unescape(str(k)) if isinstance(k, str) else k
                key = f"'{clean_key}'"

    def validate(self, value):
        return isinstance(value, (str, type(None)))


class NumberPropertyHandler(PropertyHandler):
    def __init__(self, is_double=False):
        self.is_double = is_double

    def transform(self, value, context=None):
        if value is None:
            return "null"
        if self.is_double and '.' not in str(value):
            return f"{value}.0"
        return str(value)

    def validate(self, value):
        return isinstance(value, (int, float, type(None)))


class BoolPropertyHandler(PropertyHandler):
    def transform(self, value, context=None):
        if value is None:
            return "null"
        return "true" if value else "false"

    def validate(self, value):
        return isinstance(value, (bool, type(None)))


class ColorPropertyHandler(PropertyHandler):
    COLOR_MAP = {
        'red': 'Colors.red',
        'pink': 'Colors.pink',
        'purple': 'Colors.purple',
        'deeppurple': 'Colors.deepPurple',
        'indigo': 'Colors.indigo',
        'blue': 'Colors.blue',
        'lightblue': 'Colors.lightBlue',
        'cyan': 'Colors.cyan',
        'teal': 'Colors.teal',
        'green': 'Colors.green',
        'lightgreen': 'Colors.lightGreen',
        'lime': 'Colors.lime',
        'yellow': 'Colors.yellow',
        'amber': 'Colors.amber',
        'orange': 'Colors.orange',
        'deeporange': 'Colors.deepOrange',
        'brown': 'Colors.brown',
        'grey': 'Colors.grey',
        'gray': 'Colors.grey',  # Alternative spelling
        'bluegrey': 'Colors.blueGrey',
        'black': 'Colors.black',
        'white': 'Colors.white',
        'transparent': 'Colors.transparent',
    }

    def transform(self, value, context=None):
        if value is None:
            return "null"

        # Handle color names
        if isinstance(value, str):
            # Direct Flutter color reference
            if value.startswith('Colors.'):
                return value

            # Check color map
            color_lower = value.lower().replace('_', '').replace('-', '').replace(' ', '')
            if color_lower in self.COLOR_MAP:
                return self.COLOR_MAP[color_lower]

            # Handle hex colors
            if value.startswith('#'):
                hex_value = value.replace('#', '0xFF')
                return f"Color({hex_value})"

            # Handle 0x format
            if value.startswith('0x'):
                return f"Color({value})"

        # Handle RGB/RGBA dict
        if isinstance(value, dict):
            if 'r' in value and 'g' in value and 'b' in value:
                r, g, b = value['r'], value['g'], value['b']
                a = value.get('a', 255)
                return f"Color.fromARGB({a}, {r}, {g}, {b})"
            elif 'red' in value:
                r = value.get('red', 0)
                g = value.get('green', 0)
                b = value.get('blue', 0)
                a = value.get('alpha', 255)
                return f"Color.fromARGB({a}, {r}, {g}, {b})"

        return "Colors.grey"  # fallback

    def validate(self, value):
        if value is None:
            return True
        if isinstance(value, str):
            return True
        if isinstance(value, dict):
            return 'r' in value or 'red' in value
        return False


class EnumPropertyHandler(PropertyHandler):
    def __init__(self, enum_class: str, allowed_values: list = None):
        self.enum_class = enum_class
        self.allowed_values = allowed_values or []

        # Common Flutter enum mappings
        self.common_enums = {
            'MainAxisAlignment': ['start', 'end', 'center', 'spaceBetween', 'spaceAround', 'spaceEvenly'],
            'CrossAxisAlignment': ['start', 'end', 'center', 'stretch', 'baseline'],
            'TextAlign': ['left', 'right', 'center', 'justify', 'start', 'end'],
            'BoxFit': ['fill', 'contain', 'cover', 'fitWidth', 'fitHeight', 'none', 'scaleDown'],
            'Alignment': ['topLeft', 'topCenter', 'topRight', 'centerLeft', 'center', 'centerRight', 'bottomLeft',
                          'bottomCenter', 'bottomRight'],
        }

        # If no allowed values provided, try to get from common enums
        if not self.allowed_values and self.enum_class in self.common_enums:
            self.allowed_values = self.common_enums[self.enum_class]

    def transform(self, value, context=None):
        if value is None:
            return "null"

        # If value is already a proper enum format
        if isinstance(value, str) and '.' in value:
            return value

        # Convert string to enum
        value_str = str(value)

        # Check if it's in allowed values
        if self.allowed_values:
            if value_str in self.allowed_values:
                return f"{self.enum_class}.{value_str}"

            # Try case-insensitive match
            value_lower = value_str.lower()
            for allowed in self.allowed_values:
                if allowed.lower() == value_lower:
                    return f"{self.enum_class}.{allowed}"

        # For any unrecognized value, try to use it as-is
        # This handles camelCase values like 'spaceEvenly'
        return f"{self.enum_class}.{value_str}"

    def validate(self, value):
        if value is None:
            return True

        # Always return True for now to be flexible
        # The transform method will handle conversion
        return True


class WidgetPropertyHandler(PropertyHandler):
    def __init__(self, widget_generator=None):
        self.widget_generator = widget_generator

    def transform(self, value, context=None):
        if value is None:
            return "null"

        # Handle widget definition dict
        if isinstance(value, dict):
            if self.widget_generator:
                return self.widget_generator.generate_widget(value)
            else:
                # Fallback simple generation
                widget_type = value.get('type', 'Container')
                return f"{widget_type}()"

        # Handle string widget reference
        if isinstance(value, str):
            return value

        return "Container()"  # fallback

    def validate(self, value):
        return isinstance(value, (dict, str, type(None)))


class ListPropertyHandler(PropertyHandler):
    def __init__(self, item_handler: PropertyHandler):
        self.item_handler = item_handler

    def transform(self, value, context=None):
        if value is None:
            return "[]"

        if not isinstance(value, list):
            value = [value]

        items = []
        for item in value:
            transformed = self.item_handler.transform(item, context)
            items.append(transformed)

        return f"[{', '.join(items)}]"

    def validate(self, value):
        if value is None:
            return True
        if not isinstance(value, list):
            return self.item_handler.validate(value)
        return all(self.item_handler.validate(item) for item in value)


class EdgeInsetsPropertyHandler(PropertyHandler):
    def transform(self, value, context=None):
        if value is None:
            return "null"

        # Decode deeply first
        import html
        if isinstance(value, str):
            # Multiple decode passes
            for _ in range(5):
                prev = value
                value = html.unescape(value)
                if value == prev:
                    break

        # Handle different input formats
        if isinstance(value, dict):
            # Deep decode all keys and values
            clean_dict = {}
            for k, v in value.items():
                # Decode key
                clean_key = k
                if isinstance(k, str):
                    for _ in range(5):
                        prev = clean_key
                        clean_key = html.unescape(clean_key)
                        if clean_key == prev:
                            break
                clean_dict[clean_key] = v

            if 'all' in clean_dict:
                return f"EdgeInsets.all({clean_dict['all']}.0)"
            elif 'symmetric' in value:
                sym = value['symmetric']
                if isinstance(sym, dict):
                    h = sym.get('horizontal', 0)
                    v = sym.get('vertical', 0)
                    return f"EdgeInsets.symmetric(horizontal: {h}.0, vertical: {v}.0)"
            elif 'horizontal' in value or 'vertical' in value:
                h = value.get('horizontal', 0)
                v = value.get('vertical', 0)
                return f"EdgeInsets.symmetric(horizontal: {h}.0, vertical: {v}.0)"
            else:
                l = value.get('left', 0)
                t = value.get('top', 0)
                r = value.get('right', 0)
                b = value.get('bottom', 0)
                return f"EdgeInsets.fromLTRB({l}.0, {t}.0, {r}.0, {b}.0)"

        # Handle single number (all sides)
        if isinstance(value, (int, float)):
            return f"EdgeInsets.all({value}.0)"

        # Handle string shorthand
        if isinstance(value, str):
            if ',' in value:
                parts = value.split(',')
                if len(parts) == 4:
                    return f"EdgeInsets.fromLTRB({parts[0]}.0, {parts[1]}.0, {parts[2]}.0, {parts[3]}.0)"
            else:
                try:
                    num = float(value)
                    return f"EdgeInsets.all({num}.0)"
                except:
                    pass

        # If we still have a raw dict at this point, handle it
        if isinstance(value, dict) and not isinstance(value, str):
            # This is still a Python dict, transform it
            if 'all' in value:
                return f"EdgeInsets.all({value['all']}.0)"
            else:
                return "EdgeInsets.zero"

        return "EdgeInsets.zero"

    def validate(self, value):
        return True  # Very flexible validation


class AlignmentPropertyHandler(PropertyHandler):
    ALIGNMENT_MAP = {
        'topleft': 'Alignment.topLeft',
        'topcenter': 'Alignment.topCenter',
        'topright': 'Alignment.topRight',
        'centerleft': 'Alignment.centerLeft',
        'center': 'Alignment.center',
        'centerright': 'Alignment.centerRight',
        'bottomleft': 'Alignment.bottomLeft',
        'bottomcenter': 'Alignment.bottomCenter',
        'bottomright': 'Alignment.bottomRight',
    }

    def transform(self, value, context=None):
        if value is None:
            return "null"

        if isinstance(value, str):
            # Direct Flutter reference
            if value.startswith('Alignment.'):
                return value

            # Check map
            value_lower = value.lower().replace('_', '').replace('-', '').replace(' ', '')
            if value_lower in self.ALIGNMENT_MAP:
                return self.ALIGNMENT_MAP[value_lower]

        # Handle x,y coordinates
        if isinstance(value, dict):
            x = value.get('x', 0)
            y = value.get('y', 0)
            return f"Alignment({x}, {y})"

        return "Alignment.center"

    def validate(self, value):
        return True


class TextStylePropertyHandler(PropertyHandler):
    def transform(self, value, context=None):
        if value is None:
            return "null"

        if isinstance(value, dict):
            props = []

            if 'fontSize' in value:
                props.append(f"fontSize: {value['fontSize']}.0")
            if 'fontWeight' in value:
                weight = value['fontWeight']
                if not weight.startswith('FontWeight.'):
                    weight = f"FontWeight.{weight}"
                props.append(f"fontWeight: {weight}")
            if 'fontStyle' in value:
                style = value['fontStyle']
                if not style.startswith('FontStyle.'):
                    style = f"FontStyle.{style}"
                props.append(f"fontStyle: {style}")
            if 'color' in value:
                color_handler = ColorPropertyHandler()
                color = color_handler.transform(value['color'])
                props.append(f"color: {color}")
            if 'letterSpacing' in value:
                props.append(f"letterSpacing: {value['letterSpacing']}.0")
            if 'wordSpacing' in value:
                props.append(f"wordSpacing: {value['wordSpacing']}.0")
            if 'height' in value:
                props.append(f"height: {value['height']}.0")

            if props:
                return f"TextStyle({', '.join(props)})"

        return "TextStyle()"

    def validate(self, value):
        return value is None or isinstance(value, dict)


class DurationPropertyHandler(PropertyHandler):
    def transform(self, value, context=None):
        if value is None:
            return "null"

        if isinstance(value, dict):
            if 'milliseconds' in value:
                return f"Duration(milliseconds: {value['milliseconds']})"
            elif 'seconds' in value:
                return f"Duration(seconds: {value['seconds']})"
            elif 'minutes' in value:
                return f"Duration(minutes: {value['minutes']})"

        if isinstance(value, (int, float)):
            # Assume milliseconds by default
            return f"Duration(milliseconds: {int(value)})"

        return "Duration(seconds: 1)"

    def validate(self, value):
        return True


class MapPropertyHandler(PropertyHandler):
    def transform(self, value, context=None):
        if value is None:
            return "{}"

        if isinstance(value, dict):
            items = []
            for k, v in value.items():
                # Simple string transformation for now
                key = f"'{k}'"
                if isinstance(v, str):
                    val = f"'{v}'"
                elif isinstance(v, bool):
                    val = "true" if v else "false"
                elif isinstance(v, (int, float)):
                    val = str(v)
                else:
                    val = "null"
                items.append(f"{key}: {val}")

            return "{" + ", ".join(items) + "}"

        return "{}"

    def validate(self, value):
        return value is None or isinstance(value, dict)


class PropertyHandlerFactory:
    """Factory to get the right handler for a property type"""

    _handlers = {}

    @classmethod
    def register_handler(cls, property_type: str, handler: PropertyHandler):
        """Register a custom handler"""
        cls._handlers[property_type] = handler

    @classmethod
    def get_handler(cls, property_type: str, **kwargs) -> PropertyHandler:
        """Get appropriate handler for property type"""

        # Check registered handlers first
        if property_type in cls._handlers:
            return cls._handlers[property_type]

        # Default handlers
        default_handlers = {
            'string': StringPropertyHandler(),
            'int': NumberPropertyHandler(is_double=False),
            'double': NumberPropertyHandler(is_double=True),
            'bool': BoolPropertyHandler(),
            'color': ColorPropertyHandler(),
            'edge_insets': EdgeInsetsPropertyHandler(),
            'alignment': AlignmentPropertyHandler(),
            'text_style': TextStylePropertyHandler(),
            'duration': DurationPropertyHandler(),
            'map': MapPropertyHandler(),
        }

        if property_type in default_handlers:
            return default_handlers[property_type]

        # Create specialized handlers
        if property_type == 'enum':
            return EnumPropertyHandler(**kwargs)
        elif property_type == 'widget':
            return WidgetPropertyHandler(**kwargs)
        elif property_type == 'widget_list':
            widget_handler = WidgetPropertyHandler(**kwargs)
            return ListPropertyHandler(widget_handler)
        elif property_type.endswith('_list'):
            # Handle lists of other types
            base_type = property_type[:-5]  # Remove '_list'
            base_handler = cls.get_handler(base_type, **kwargs)
            return ListPropertyHandler(base_handler)

        # Handle custom types (functions, callbacks, etc.)
        if property_type == 'custom':
            return CustomPropertyHandler()

        # Default to string handler
        return StringPropertyHandler()

    @classmethod
    def clear_handlers(cls):
        """Clear all registered handlers"""
        cls._handlers.clear()


class CustomPropertyHandler(PropertyHandler):
    """Handler for custom properties like functions, callbacks, etc."""

    def transform(self, value, context=None):
        if value is None:
            return "null"

        # If it's a string that looks like a function
        if isinstance(value, str):
            # Decode HTML entities multiple times
            decoded = decode_html_entities(value)

            # Check if it's a function literal
            if decoded.strip().startswith('()') or decoded.strip().startswith('(') and '=>' in decoded:
                return decoded
            # Check if it's just a function reference
            elif decoded == '() {}' or decoded.strip() == '(){}':
                return '() {}'
            else:
                # Return as-is if it looks like valid Dart code
                return decoded

        # For other types, convert to string
        return str(value)

    def validate(self, value):
        return True