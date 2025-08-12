# generator/management/commands/fix_widget_data.py
# Command to fix existing widget data in database

from django.core.management.base import BaseCommand
from django.db import transaction
from generator.models import (
    WidgetType, WidgetProperty, DynamicPageComponent
)
import json


class Command(BaseCommand):
    help = 'Fix widget data issues (Text widgets, enums, CarouselSlider)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Fixing widget data...'))

        with transaction.atomic():
            self._fix_text_widgets()
            self._fix_enum_properties()
            self._fix_carousel_slider()
            self._fix_existing_components()

        self.stdout.write(self.style.SUCCESS('✅ Widget data fixed successfully!'))

    def _fix_text_widgets(self):
        """Ensure Text widget has proper properties"""
        self.stdout.write('\n📝 Fixing Text widget...')

        try:
            text_widget = WidgetType.objects.get(name='Text')

            # Ensure 'data' property exists and is required
            data_prop, created = WidgetProperty.objects.update_or_create(
                widget_type=text_widget,
                name='data',
                defaults={
                    'property_type': 'string',
                    'dart_type': 'String',
                    'is_required': True,
                    'is_positional': True,
                    'position': 0,
                    'documentation': 'The text to display'
                }
            )

            if created:
                self.stdout.write('   ✅ Created "data" property for Text widget')
            else:
                self.stdout.write('   ✅ Updated "data" property for Text widget')

            # Make style property optional
            style_prop, created = WidgetProperty.objects.update_or_create(
                widget_type=text_widget,
                name='style',
                defaults={
                    'property_type': 'text_style',
                    'dart_type': 'TextStyle',
                    'is_required': False,
                    'is_positional': False,
                    'documentation': 'Text styling properties'
                }
            )

            # Fix textAlign to be enum
            align_prop, created = WidgetProperty.objects.update_or_create(
                widget_type=text_widget,
                name='textAlign',
                defaults={
                    'property_type': 'enum',
                    'dart_type': 'TextAlign',
                    'is_required': False,
                    'allowed_values': {'values': ['left', 'right', 'center', 'justify', 'start', 'end']}
                }
            )

        except WidgetType.DoesNotExist:
            self.stdout.write('   ⚠️ Text widget not found - run setup_dynamic_engine first')

    def _fix_enum_properties(self):
        """Fix enum properties for layout widgets"""
        self.stdout.write('\n🎯 Fixing enum properties...')

        # Fix Column widget
        try:
            column = WidgetType.objects.get(name='Column')

            WidgetProperty.objects.update_or_create(
                widget_type=column,
                name='mainAxisAlignment',
                defaults={
                    'property_type': 'enum',
                    'dart_type': 'MainAxisAlignment',
                    'is_required': False,
                    'allowed_values': {
                        'values': ['start', 'end', 'center', 'spaceBetween', 'spaceAround', 'spaceEvenly']}
                }
            )

            WidgetProperty.objects.update_or_create(
                widget_type=column,
                name='crossAxisAlignment',
                defaults={
                    'property_type': 'enum',
                    'dart_type': 'CrossAxisAlignment',
                    'is_required': False,
                    'allowed_values': {'values': ['start', 'end', 'center', 'stretch', 'baseline']}
                }
            )

            self.stdout.write('   ✅ Fixed Column widget enums')

        except WidgetType.DoesNotExist:
            pass

        # Fix Row widget
        try:
            row = WidgetType.objects.get(name='Row')

            WidgetProperty.objects.update_or_create(
                widget_type=row,
                name='mainAxisAlignment',
                defaults={
                    'property_type': 'enum',
                    'dart_type': 'MainAxisAlignment',
                    'is_required': False,
                    'allowed_values': {
                        'values': ['start', 'end', 'center', 'spaceBetween', 'spaceAround', 'spaceEvenly']}
                }
            )

            WidgetProperty.objects.update_or_create(
                widget_type=row,
                name='crossAxisAlignment',
                defaults={
                    'property_type': 'enum',
                    'dart_type': 'CrossAxisAlignment',
                    'is_required': False,
                    'allowed_values': {'values': ['start', 'end', 'center', 'stretch', 'baseline']}
                }
            )

            self.stdout.write('   ✅ Fixed Row widget enums')

        except WidgetType.DoesNotExist:
            pass

        # Fix Image widget
        try:
            image = WidgetType.objects.get(name='Image')

            WidgetProperty.objects.update_or_create(
                widget_type=image,
                name='fit',
                defaults={
                    'property_type': 'enum',
                    'dart_type': 'BoxFit',
                    'is_required': False,
                    'allowed_values': {
                        'values': ['fill', 'contain', 'cover', 'fitWidth', 'fitHeight', 'none', 'scaleDown']}
                }
            )

            self.stdout.write('   ✅ Fixed Image widget enums')

        except WidgetType.DoesNotExist:
            pass

    def _fix_carousel_slider(self):
        """Fix CarouselSlider widget structure"""
        self.stdout.write('\n🎠 Fixing CarouselSlider...')

        try:
            carousel = WidgetType.objects.get(name='CarouselSlider')

            # Update to be a container that can have multiple children
            carousel.is_container = True
            carousel.can_have_multiple_children = True
            carousel.save()

            # Add/update properties
            WidgetProperty.objects.update_or_create(
                widget_type=carousel,
                name='items',
                defaults={
                    'property_type': 'widget_list',
                    'dart_type': 'List<Widget>',
                    'is_required': True,
                    'documentation': 'List of widgets to display in carousel'
                }
            )

            WidgetProperty.objects.update_or_create(
                widget_type=carousel,
                name='options',
                defaults={
                    'property_type': 'map',
                    'dart_type': 'CarouselOptions',
                    'is_required': True,
                    'documentation': 'Carousel configuration options'
                }
            )

            self.stdout.write('   ✅ Fixed CarouselSlider widget')

        except WidgetType.DoesNotExist:
            self.stdout.write('   ⚠️ CarouselSlider not found - run discover_package carousel_slider')

    def _fix_existing_components(self):
        """Fix existing component data"""
        self.stdout.write('\n🔄 Fixing existing components...')

        fixed_count = 0

        # Fix Text components
        text_components = DynamicPageComponent.objects.filter(widget_type__name='Text')
        for component in text_components:
            properties = component.properties or {}

            # Ensure 'data' property exists
            if 'data' not in properties and 'text' in properties:
                properties['data'] = properties['text']
                component.properties = properties
                component.save()
                fixed_count += 1
            elif 'data' not in properties and 'text' not in properties:
                properties['data'] = 'Text'
                component.properties = properties
                component.save()
                fixed_count += 1

        # Fix Row/Column components with string enums
        layout_components = DynamicPageComponent.objects.filter(
            widget_type__name__in=['Row', 'Column']
        )
        for component in layout_components:
            properties = component.properties or {}
            changed = False

            # Fix mainAxisAlignment if it's quoted
            if 'mainAxisAlignment' in properties:
                value = properties['mainAxisAlignment']
                if isinstance(value, str) and value.startswith("'"):
                    # Remove quotes
                    properties['mainAxisAlignment'] = value.strip("'\"")
                    changed = True

            # Fix crossAxisAlignment if it's quoted
            if 'crossAxisAlignment' in properties:
                value = properties['crossAxisAlignment']
                if isinstance(value, str) and value.startswith("'"):
                    # Remove quotes
                    properties['crossAxisAlignment'] = value.strip("'\"")
                    changed = True

            if changed:
                component.properties = properties
                component.save()
                fixed_count += 1

        # Fix CarouselSlider components
        carousel_components = DynamicPageComponent.objects.filter(widget_type__name='CarouselSlider')
        for component in carousel_components:
            properties = component.properties or {}
            changed = False

            # Ensure items is a list
            if 'items' in properties and not isinstance(properties['items'], list):
                properties['items'] = [properties['items']]
                changed = True

            # Ensure options exists
            if 'options' not in properties:
                properties['options'] = {'height': 200}
                changed = True

            if changed:
                component.properties = properties
                component.save()
                fixed_count += 1

        self.stdout.write(f'   ✅ Fixed {fixed_count} components')

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )