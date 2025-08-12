# Dynamic Backend Engine Implementation Guide

## Overview
This dynamic backend engine transforms your Flutter code generator from a hardcoded system to a fully database-driven solution that can handle ANY pub.dev package without modifying code.

## Architecture Components

### 1. Core Models (models.py)
- **WidgetType**: Defines any widget dynamically
- **WidgetProperty**: Properties for each widget type
- **WidgetTemplate**: Code generation templates
- **PropertyTransformer**: Rules for transforming values
- **PackageWidgetRegistry**: Track widgets per package
- **DynamicPageComponent**: Replaces hardcoded PageComponent

### 2. Property Handlers (property_handlers.py)
Smart functions that transform property values to Dart code:
- StringPropertyHandler
- ColorPropertyHandler
- EdgeInsetsPropertyHandler
- WidgetPropertyHandler (for nested widgets)
- And many more...

### 3. Widget Generator (widget_generator.py)
Generates Flutter code from database definitions:
- Template-based generation
- Dynamic property processing
- Nested widget support
- Fallback mechanisms

### 4. Package Analyzer (package_analyzer.py)
Auto-discovers widgets from pub.dev:
- Fetches package information
- Extracts widget definitions
- Parses documentation
- Registers in database

## Implementation Steps

### Step 1: Add New Files
```bash
# Create new files in your generator app
generator/
├── property_handlers.py    # Property transformation logic
├── widget_generator.py     # Dynamic code generation
├── package_analyzer.py     # Package discovery
├── admin_dynamic.py        # Admin interface for dynamic widgets
└── management/
    └── commands/
        └── discover_package.py  # Command to discover packages
```

### Step 2: Update Models
Add the new model definitions to your existing `models.py` or create them separately.

### Step 3: Run Migrations
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Update Admin
Add the dynamic admin classes to your `admin.py`:
```python
# In admin.py
from .admin_dynamic import *  # Import all dynamic admin classes
```

### Step 5: Discover Your First Package
```bash
# Discover carousel_slider package
python manage.py discover_package carousel_slider

# Discover multiple packages
python manage.py discover_package http provider cached_network_image

# With options
python manage.py discover_package video_player --verbose --force
```

### Step 6: Update Your Utils
Modify `FlutterCodeGenerator` in `utils.py` to use the dynamic system:

```python
from .widget_generator import DynamicWidgetGenerator

class FlutterCodeGenerator:
    def __init__(self, project):
        self.project = project
        self.widget_generator = DynamicWidgetGenerator()
    
    def generate_widget_code(self, component):
        # Use dynamic generator instead of hardcoded
        return self.widget_generator.generate_widget({
            'type': component.widget_type.name,
            'properties': component.properties
        })
```

## Usage Examples

### Adding a New Package

#### Method 1: Command Line
```bash
python manage.py discover_package carousel_slider
```

#### Method 2: Admin Interface
1. Go to Django Admin
2. Navigate to "Package Widget Registry"
3. Click "Discover Package"
4. Enter package name
5. System auto-discovers widgets

#### Method 3: Python Code
```python
from generator.package_analyzer import PackageAnalyzer

analyzer = PackageAnalyzer()
analyzer.auto_register_widgets('carousel_slider')
```

### Creating Components with Dynamic Widgets

```python
from generator.models import DynamicPageComponent, WidgetType

# Get widget type from database
carousel_widget = WidgetType.objects.get(name='CarouselSlider')

# Create component
component = DynamicPageComponent.objects.create(
    project=project,
    page_name='HomePage',
    widget_type=carousel_widget,
    properties={
        'height': 200,
        'autoPlay': True,
        'items': [
            {'type': 'Image', 'properties': {'url': 'image1.jpg'}},
            {'type': 'Image', 'properties': {'url': 'image2.jpg'}}
        ]
    }
)
```

### Custom Widget Templates

```python
from generator.models import WidgetType, WidgetTemplate

widget = WidgetType.objects.get(name='CustomButton')

# Create a custom template
WidgetTemplate.objects.create(
    widget_type=widget,
    template_name='material_style',
    template_code='''MaterialButton(
{% for prop in properties %}  {{ prop.name }}: {{ prop.value }},
{% endfor %}  onPressed: () {},
)''',
    priority=10,
    conditions={'style': 'material'}
)
```

## Benefits

### 1. Zero Code Changes for New Packages
```bash
# Before: Had to modify code for each new widget type
# Now: Just run one command
python manage.py discover_package new_package_name
```

### 2. Database-Driven Everything
- Widget definitions in database
- Properties in database
- Templates in database
- Transformation rules in database

### 3. Smart Property Handling
```python
# Automatically handles different formats
color: "red"        → Colors.red
color: "#FF5733"    → Color(0xFFFF5733)
color: {"r": 255}   → Color.fromARGB(255, 255, 87, 51)
```

### 4. Template-Based Generation
- Easy to customize output
- Multiple templates per widget
- Conditional templates

### 5. Learning System
- Discovers patterns from packages
- Stores successful patterns
- Improves over time

## Advanced Features

### Custom Property Handlers
```python
from generator.property_handlers import PropertyHandler, PropertyHandlerFactory

class CustomPropertyHandler(PropertyHandler):
    def transform(self, value, context=None):
        # Your custom transformation logic
        return f"CustomValue({value})"
    
    def validate(self, value):
        return True

# Register handler
PropertyHandlerFactory.register_handler('custom_type', CustomPropertyHandler())
```

### Widget Discovery Patterns
Add known patterns for better discovery:
```python
# In package_analyzer.py
self.known_patterns['your_package'] = [
    {
        'name': 'YourWidget',
        'properties': [
            {'name': 'prop1', 'type': 'String', 'required': True},
        ]
    }
]
```

### Generation Rules
Create rules that apply during generation:
```python
from generator.models import GenerationRule

GenerationRule.objects.create(
    rule_type='import',
    name='Add material import',
    condition={'uses_material': True},
    action={'add_import': "import 'package:flutter/material.dart';"},
    priority=100
)
```

## Troubleshooting

### Widget Not Found
```python
# Check if widget is registered
from generator.models import WidgetType
WidgetType.objects.filter(name='YourWidget').exists()

# Re-discover package
python manage.py discover_package your_package --force
```

### Property Not Transforming
```python
# Check property type mapping
from generator.property_handlers import PropertyHandlerFactory
handler = PropertyHandlerFactory.get_handler('your_type')
result = handler.transform(your_value)
print(result)
```

### Template Not Working
```python
# Test template directly
from django.template import Template, Context
template = Template(your_template_string)
context = Context({'widget_name': 'Test', 'properties': []})
print(template.render(context))
```

## Migration Path

### Phase 1: Setup Infrastructure
1. Add new models and files
2. Run migrations
3. Test with one package

### Phase 2: Migrate Existing Widgets
```python
# Script to migrate existing components
from generator.models import PageComponent, DynamicPageComponent, WidgetType

for old_component in PageComponent.objects.all():
    # Find or create widget type
    widget_type, _ = WidgetType.objects.get_or_create(
        name=old_component.component_type,
        defaults={'dart_class_name': old_component.component_type}
    )
    
    # Create dynamic component
    DynamicPageComponent.objects.create(
        project=old_component.project,
        page_name=old_component.page_name,
        widget_type=widget_type,
        properties=old_component.properties,
        order=old_component.order
    )
```

### Phase 3: Switch to Dynamic System
1. Update views to use DynamicPageComponent
2. Update code generation to use DynamicWidgetGenerator
3. Remove hardcoded COMPONENT_TYPES

### Phase 4: Discover All Packages
```bash
# Discover all packages you use
for package in http provider dio shared_preferences; do
    python manage.py discover_package $package
done
```

## Best Practices

1. **Always Test Discovery First**
   ```bash
   python manage.py discover_package package_name --dry-run --verbose
   ```

2. **Create Templates for Common Patterns**
   - One default template
   - Specialized templates for variants

3. **Document Custom Properties**
   - Add documentation to WidgetProperty
   - Include example values

4. **Use Property Validation**
   - Set allowed_values for enums
   - Add validation_rules for constraints

5. **Regular Updates**
   ```bash
   # Update package widgets monthly
   python manage.py discover_package package_name --update
   ```

## Next Steps

1. **Implement Visual Builder** (future)
   - Use widget registry for component palette
   - Generate property forms from definitions
   - Real-time preview with templates

2. **Add More Property Types**
   - Gradient handlers
   - Animation handlers
   - Custom painters

3. **Enhance Discovery**
   - Parse TypeScript definitions
   - Analyze example apps
   - Machine learning for pattern recognition

4. **Community Contributions**
   - Share widget definitions
   - Share templates
   - Share property handlers

## Conclusion

This dynamic backend engine provides a truly extensible system where adding support for any pub.dev package is just a matter of running one command. No more hardcoded widget types, no more manual updates - just pure database-driven flexibility!