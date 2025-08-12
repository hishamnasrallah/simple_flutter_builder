# generator/management/commands/setup_dynamic_engine.py
# Quick setup script for the dynamic backend engine

from django.core.management.base import BaseCommand
from django.db import transaction
import json


class Command(BaseCommand):
    help = 'Setup dynamic backend engine with initial data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Setting up Dynamic Backend Engine...'))

        try:
            with transaction.atomic():
                # Step 1: Create basic Flutter widgets
                self._create_flutter_widgets()

                # Step 2: Create common property transformers
                self._create_property_transformers()

                # Step 3: Discover popular packages
                self._discover_popular_packages()

                # Step 4: Create sample templates
                self._create_sample_templates()

                # Step 5: Migrate existing components if any
                self._migrate_existing_components()

                self.stdout.write(self.style.SUCCESS('\n✅ Dynamic Backend Engine setup complete!'))
                self._print_next_steps()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Setup failed: {str(e)}'))

    def _create_flutter_widgets(self):
        """Create basic Flutter widgets in database"""
        from generator.models import WidgetType, WidgetProperty, WidgetTemplate

        self.stdout.write('\n📦 Creating basic Flutter widgets...')

        flutter_widgets = [
            {
                'name': 'Container',
                'properties': [
                    {'name': 'width', 'type': 'double'},
                    {'name': 'height', 'type': 'double'},
                    {'name': 'color', 'type': 'color'},
                    {'name': 'padding', 'type': 'edge_insets'},
                    {'name': 'margin', 'type': 'edge_insets'},
                    {'name': 'child', 'type': 'widget'},
                ],
                'is_container': True,
                'category': 'container'
            },
            {
                'name': 'Text',
                'properties': [
                    {'name': 'data', 'type': 'string', 'required': True, 'positional': True},
                    {'name': 'style', 'type': 'text_style'},
                    {'name': 'textAlign', 'type': 'enum', 'dart_type': 'TextAlign'},
                ],
                'category': 'display'
            },
            {
                'name': 'Column',
                'properties': [
                    {'name': 'children', 'type': 'widget_list'},
                    {'name': 'mainAxisAlignment', 'type': 'enum', 'dart_type': 'MainAxisAlignment'},
                    {'name': 'crossAxisAlignment', 'type': 'enum', 'dart_type': 'CrossAxisAlignment'},
                ],
                'is_container': True,
                'can_have_multiple_children': True,
                'category': 'layout'
            },
            {
                'name': 'Row',
                'properties': [
                    {'name': 'children', 'type': 'widget_list'},
                    {'name': 'mainAxisAlignment', 'type': 'enum', 'dart_type': 'MainAxisAlignment'},
                    {'name': 'crossAxisAlignment', 'type': 'enum', 'dart_type': 'CrossAxisAlignment'},
                ],
                'is_container': True,
                'can_have_multiple_children': True,
                'category': 'layout'
            },
            {
                'name': 'ElevatedButton',
                'properties': [
                    {'name': 'onPressed', 'type': 'custom', 'required': True},
                    {'name': 'child', 'type': 'widget'},
                ],
                'is_container': True,
                'category': 'input'
            },
            {
                'name': 'Image',
                'properties': [
                    {'name': 'image', 'type': 'custom', 'required': True},
                    {'name': 'width', 'type': 'double'},
                    {'name': 'height', 'type': 'double'},
                    {'name': 'fit', 'type': 'enum', 'dart_type': 'BoxFit'},
                ],
                'category': 'media'
            },
        ]

        for widget_data in flutter_widgets:
            widget_type, created = WidgetType.objects.get_or_create(
                name=widget_data['name'],
                defaults={
                    'dart_class_name': widget_data['name'],
                    'category': widget_data.get('category', 'display'),
                    'is_container': widget_data.get('is_container', False),
                    'can_have_multiple_children': widget_data.get('can_have_multiple_children', False),
                }
            )

            if created:
                self.stdout.write(f'   ✅ Created widget: {widget_data["name"]}')

                # Add properties
                for prop_data in widget_data.get('properties', []):
                    WidgetProperty.objects.create(
                        widget_type=widget_type,
                        name=prop_data['name'],
                        property_type=prop_data.get('type', 'string'),
                        dart_type=prop_data.get('dart_type', prop_data.get('type', 'dynamic')),
                        is_required=prop_data.get('required', False),
                        is_positional=prop_data.get('positional', False),
                        position=prop_data.get('position', 0)
                    )

                # Create default template
                if not widget_type.templates.exists():
                    template = self._generate_widget_template(widget_data)
                    WidgetTemplate.objects.create(
                        widget_type=widget_type,
                        template_name='default',
                        template_code=template
                    )

    def _create_property_transformers(self):
        """Create common property transformers"""
        from generator.models import PropertyTransformer

        self.stdout.write('\n🔧 Creating property transformers...')

        transformers = [
            {
                'property_type': 'color',
                'transformer_name': 'color_mapper',
                'transformer_code': '''# Maps color values to Flutter
if value.startswith('#'):
    return f"Color({value.replace('#', '0xFF')})"
elif value in ['red', 'blue', 'green', 'yellow', 'orange', 'purple']:
    return f"Colors.{value}"
else:
    return "Colors.grey"''',
                'priority': 10
            },
            {
                'property_type': 'edge_insets',
                'transformer_name': 'edge_insets_mapper',
                'transformer_code': '''# Maps edge insets values
if isinstance(value, (int, float)):
    return f"EdgeInsets.all({value}.0)"
elif isinstance(value, dict):
    if 'all' in value:
        return f"EdgeInsets.all({value['all']}.0)"
    else:
        l = value.get('left', 0)
        t = value.get('top', 0)
        r = value.get('right', 0)
        b = value.get('bottom', 0)
        return f"EdgeInsets.fromLTRB({l}.0, {t}.0, {r}.0, {b}.0)"
return "EdgeInsets.zero"''',
                'priority': 10
            }
        ]

        for transformer_data in transformers:
            transformer, created = PropertyTransformer.objects.get_or_create(
                property_type=transformer_data['property_type'],
                transformer_name=transformer_data['transformer_name'],
                defaults={
                    'transformer_code': transformer_data['transformer_code'],
                    'priority': transformer_data['priority']
                }
            )

            if created:
                self.stdout.write(f'   ✅ Created transformer: {transformer_data["transformer_name"]}')

    def _discover_popular_packages(self):
        """Discover popular packages"""
        from generator.package_analyzer import PackageAnalyzer

        self.stdout.write('\n🔍 Discovering popular packages...')

        packages = [
            'http',
            'provider',
            'shared_preferences',
            'cached_network_image',
        ]

        analyzer = PackageAnalyzer()

        for package_name in packages:
            try:
                self.stdout.write(f'   🔍 Discovering {package_name}...')
                success = analyzer.auto_register_widgets(package_name)
                if success:
                    self.stdout.write(f'   ✅ Discovered {package_name}')
                else:
                    self.stdout.write(f'   ⚠️  Could not discover {package_name}')
            except Exception as e:
                self.stdout.write(f'   ⚠️  Error with {package_name}: {str(e)}')

    def _create_sample_templates(self):
        """Create sample templates"""
        from generator.models import WidgetType, WidgetTemplate

        self.stdout.write('\n📝 Creating sample templates...')

        # Create a fancy button template
        try:
            button = WidgetType.objects.get(name='ElevatedButton')
            WidgetTemplate.objects.get_or_create(
                widget_type=button,
                template_name='fancy',
                defaults={
                    'template_code': '''ElevatedButton(
  onPressed: () {},
  style: ElevatedButton.styleFrom(
    padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(8),
    ),
  ),
  child: {{ children.0|default:"Text('Click Me')" }},
)''',
                    'priority': 5,
                    'conditions': {'style': 'fancy'}
                }
            )
            self.stdout.write('   ✅ Created fancy button template')
        except:
            pass

    def _migrate_existing_components(self):
        """Migrate existing PageComponent to DynamicPageComponent"""
        from generator.models import PageComponent, DynamicPageComponent, WidgetType

        self.stdout.write('\n🔄 Migrating existing components...')

        migrated = 0
        for old_component in PageComponent.objects.all():
            # Find or create widget type
            widget_type, created = WidgetType.objects.get_or_create(
                name=old_component.component_type.title().replace('_', ''),
                defaults={
                    'dart_class_name': old_component.component_type.title().replace('_', ''),
                    'category': 'custom'
                }
            )

            # Check if already migrated
            if not DynamicPageComponent.objects.filter(
                    project=old_component.project,
                    page_name=old_component.page_name,
                    widget_type=widget_type,
                    order=old_component.order
            ).exists():
                DynamicPageComponent.objects.create(
                    project=old_component.project,
                    page_name=old_component.page_name,
                    widget_type=widget_type,
                    properties=old_component.properties,
                    order=old_component.order,
                    parent_component=None  # Handle parent relationships separately if needed
                )
                migrated += 1

        if migrated > 0:
            self.stdout.write(f'   ✅ Migrated {migrated} components')
        else:
            self.stdout.write('   ℹ️  No components to migrate')

    def _generate_widget_template(self, widget_data):
        """Generate a default template for a widget"""
        lines = [f"{widget_data['name']}("]

        for prop in widget_data.get('properties', []):
            if prop.get('required'):
                lines.append(f"  {prop['name']}: {{{{{prop['name']}}}}},")
            else:
                lines.append(f"  {{%if {prop['name']}%}}{prop['name']}: {{{{{prop['name']}}}}},{{%endif%}}")

        lines.append(")")
        return '\n'.join(lines)

    def _print_next_steps(self):
        """Print next steps for the user"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('🎉 SETUP COMPLETE!'))
        self.stdout.write('=' * 60)

        self.stdout.write('\n📋 Next Steps:')
        self.stdout.write('1. Go to Django Admin: http://127.0.0.1:8000/admin/')
        self.stdout.write('2. Check "Widget Types" to see all registered widgets')
        self.stdout.write('3. Discover more packages:')
        self.stdout.write('   python manage.py discover_package carousel_slider')
        self.stdout.write('4. Create projects using dynamic widgets')
        self.stdout.write('5. Customize templates and add new property handlers')

        self.stdout.write('\n🔧 Useful Commands:')
        self.stdout.write('• Discover package: python manage.py discover_package PACKAGE_NAME')
        self.stdout.write(
            '• List widgets: python manage.py shell -c "from generator.models import WidgetType; print(WidgetType.objects.values_list(\'name\', flat=True))"')
        self.stdout.write('• Test generator: python manage.py shell < test_dynamic_generation.py')

        self.stdout.write('\n📚 Documentation:')
        self.stdout.write('• Check README_DYNAMIC_ENGINE.md for detailed documentation')
        self.stdout.write('• Property handlers: generator/property_handlers.py')
        self.stdout.write('• Widget generator: generator/widget_generator.py')
        self.stdout.write('• Package analyzer: generator/package_analyzer.py')

        self.stdout.write('\n✨ Happy coding with your dynamic Flutter generator!')
        self.stdout.write('=' * 60)