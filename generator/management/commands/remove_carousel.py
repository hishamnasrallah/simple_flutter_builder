# generator/management/commands/remove_carousel.py
# Command to remove carousel_slider components temporarily

from django.core.management.base import BaseCommand
from django.db import transaction
from generator.models import (
    DynamicPageComponent, WidgetType, ProjectPackage,
    PubDevPackage
)


class Command(BaseCommand):
    help = 'Remove carousel_slider components to fix build issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Replace carousel with simple container'
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete carousel components entirely'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🎠 Handling carousel_slider conflict...'))

        with transaction.atomic():
            # Find all CarouselSlider components
            carousel_components = DynamicPageComponent.objects.filter(
                widget_type__name='CarouselSlider'
            )

            count = carousel_components.count()
            self.stdout.write(f'\n📊 Found {count} CarouselSlider components')

            if count == 0:
                self.stdout.write('   No carousel components to fix')
                return

            if options['delete']:
                # Delete all carousel components
                carousel_components.delete()
                self.stdout.write(f'   ❌ Deleted {count} carousel components')

            elif options['replace']:
                # Replace with container
                container_widget, _ = WidgetType.objects.get_or_create(
                    name='Container',
                    defaults={
                        'dart_class_name': 'Container',
                        'category': 'container',
                        'is_container': True
                    }
                )

                for component in carousel_components:
                    # Extract first item or create placeholder
                    items = component.properties.get('items', [])
                    if items and isinstance(items, list) and len(items) > 0:
                        # Use first item
                        first_item = items[0]
                        if isinstance(first_item, dict):
                            component.properties = first_item.get('properties', {
                                'color': 'blue',
                                'height': 200,
                                'child': {'type': 'Text', 'properties': {'data': 'Carousel replaced'}}
                            })
                    else:
                        # Create placeholder
                        component.properties = {
                            'height': 200,
                            'color': 'grey',
                            'child': {
                                'type': 'Center',
                                'properties': {
                                    'child': {
                                        'type': 'Text',
                                        'properties': {'data': 'Carousel temporarily disabled'}
                                    }
                                }
                            }
                        }

                    component.widget_type = container_widget
                    component.save()

                self.stdout.write(f'   ✅ Replaced {count} carousel components with containers')

            else:
                # Just show what would be affected
                self.stdout.write('\n   Affected projects:')
                projects = set()
                for component in carousel_components:
                    projects.add(component.project.name)
                    self.stdout.write(f'      • {component.project.name} - {component.page_name}')

                self.stdout.write('\n   ℹ️ Use --replace to convert to containers')
                self.stdout.write('   ℹ️ Use --delete to remove entirely')

            # Remove carousel_slider from project packages
            carousel_package = PubDevPackage.objects.filter(name='carousel_slider').first()
            if carousel_package:
                project_packages = ProjectPackage.objects.filter(package=carousel_package)
                if project_packages.exists():
                    count = project_packages.count()
                    project_packages.delete()
                    self.stdout.write(f'\n   🗑️ Removed carousel_slider from {count} projects')

        self.stdout.write(self.style.SUCCESS('\n✅ Carousel conflict handled!'))
        self.stdout.write('\n📝 Next steps:')
        self.stdout.write('   1. Try building APK again')
        self.stdout.write('   2. Consider using alternative carousel packages')
        self.stdout.write('   3. Or wait for carousel_slider package update')