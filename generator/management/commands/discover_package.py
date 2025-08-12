# generator/management/commands/discover_package.py

from django.core.management.base import BaseCommand, CommandError
from generator.package_analyzer import PackageAnalyzer
from generator.models import PubDevPackage, WidgetType, PackageWidgetRegistry
import json


class Command(BaseCommand):
    help = 'Auto-discover and register widgets from a pub.dev package'

    def add_arguments(self, parser):
        parser.add_argument(
            'package_names',
            nargs='+',
            type=str,
            help='Names of packages to discover'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-discovery even if package exists'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing widgets instead of skipping'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be discovered without saving'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed discovery information'
        )

    def handle(self, *args, **options):
        analyzer = PackageAnalyzer()

        for package_name in options['package_names']:
            self.stdout.write(f'\n{"=" * 60}')
            self.stdout.write(f'📦 Discovering package: {package_name}')
            self.stdout.write(f'{"=" * 60}')

            try:
                # Check if package already exists
                if not options['force']:
                    existing_widgets = WidgetType.objects.filter(package__name=package_name)
                    if existing_widgets.exists():
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️  Package "{package_name}" already has {existing_widgets.count()} widgets registered.'
                            )
                        )
                        if not options['update']:
                            self.stdout.write('   Use --force to re-discover or --update to update existing.')
                            continue

                # Analyze package
                self.stdout.write('🔍 Analyzing package structure...')
                analysis = analyzer.analyze_package(package_name)

                if not analysis:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Failed to analyze package "{package_name}"')
                    )
                    continue

                # Show analysis results
                self._display_analysis(analysis, options['verbose'])

                # Save to database if not dry-run
                if not options['dry_run']:
                    self._save_widgets(package_name, analysis, options['update'])
                else:
                    self.stdout.write(
                        self.style.WARNING('🔸 Dry run mode - no changes saved')
                    )

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully processed {package_name}')
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error processing {package_name}: {str(e)}')
                )
                if options['verbose']:
                    import traceback
                    self.stdout.write(traceback.format_exc())

    def _display_analysis(self, analysis, verbose=False):
        """Display analysis results"""

        self.stdout.write(f'\n📊 Analysis Results:')
        self.stdout.write(f'   Package: {analysis["package_name"]}')
        self.stdout.write(f'   Version: {analysis.get("version", "unknown")}')
        self.stdout.write(f'   Widgets found: {len(analysis["widgets"])}')

        if analysis['widgets']:
            self.stdout.write('\n🧩 Discovered Widgets:')
            for widget in analysis['widgets']:
                props_count = len(widget.get('properties', []))
                self.stdout.write(f'   • {widget["name"]} ({props_count} properties)')

                if verbose and widget.get('properties'):
                    for prop in widget['properties']:
                        required = '✓' if prop.get('required') else '○'
                        self.stdout.write(
                            f'      {required} {prop["name"]}: {prop.get("type", "unknown")}'
                        )

        if verbose:
            self.stdout.write('\n📝 Import statements:')
            for import_stmt in analysis.get('imports', []):
                self.stdout.write(f'   {import_stmt}')

    def _save_widgets(self, package_name, analysis, update_existing=False):
        """Save widgets to database"""

        from generator.models import (
            PubDevPackage, WidgetType, WidgetProperty,
            WidgetTemplate, PackageWidgetRegistry
        )

        self.stdout.write('\n💾 Saving to database...')

        # Create or update package
        package, created = PubDevPackage.objects.get_or_create(
            name=package_name,
            defaults={
                'version': analysis.get('version', 'latest'),
                'description': analysis.get('description', '')
            }
        )

        if created:
            self.stdout.write(f'   ✅ Created package: {package_name}')
        elif update_existing:
            package.version = analysis.get('version', package.version)
            package.save()
            self.stdout.write(f'   ✅ Updated package: {package_name}')

        # Create or update registry
        registry, _ = PackageWidgetRegistry.objects.get_or_create(
            package=package,
            defaults={
                'auto_discovered': True,
                'discovery_data': analysis
            }
        )

        # Process each widget
        created_count = 0
        updated_count = 0

        for widget_data in analysis['widgets']:
            if update_existing:
                widget_type, created = WidgetType.objects.update_or_create(
                    name=widget_data['name'],
                    package=package,
                    defaults={
                        'dart_class_name': widget_data['name'],
                        'category': self._guess_category(widget_data['name']),
                        'is_container': self._is_container(widget_data),
                        'import_path': widget_data.get('import_path', ''),
                        'documentation': widget_data.get('documentation', '')
                    }
                )
            else:
                widget_type, created = WidgetType.objects.get_or_create(
                    name=widget_data['name'],
                    package=package,
                    defaults={
                        'dart_class_name': widget_data['name'],
                        'category': self._guess_category(widget_data['name']),
                        'is_container': self._is_container(widget_data),
                        'import_path': widget_data.get('import_path', ''),
                        'documentation': widget_data.get('documentation', '')
                    }
                )

            if created:
                created_count += 1
                self.stdout.write(f'   ✅ Created widget: {widget_data["name"]}')
            elif update_existing:
                updated_count += 1
                self.stdout.write(f'   ✅ Updated widget: {widget_data["name"]}')

            # Add to registry
            registry.widget_types.add(widget_type)

            # Process properties
            if created or update_existing:
                # Clear existing properties if updating
                if update_existing and not created:
                    widget_type.properties.all().delete()

                for prop_data in widget_data.get('properties', []):
                    WidgetProperty.objects.create(
                        widget_type=widget_type,
                        name=prop_data['name'],
                        property_type=self._map_property_type(prop_data.get('type', 'dynamic')),
                        dart_type=prop_data.get('type', 'dynamic'),
                        is_required=prop_data.get('required', False),
                        default_value=json.dumps(prop_data.get('default')) if prop_data.get('default') else ''
                    )

                # Create default template if it doesn't exist
                if not widget_type.templates.filter(template_name='default').exists():
                    WidgetTemplate.objects.create(
                        widget_type=widget_type,
                        template_name='default',
                        template_code=self._generate_default_template(widget_data),
                        is_active=True
                    )

        self.stdout.write(f'\n📈 Summary:')
        self.stdout.write(f'   Widgets created: {created_count}')
        if update_existing:
            self.stdout.write(f'   Widgets updated: {updated_count}')

    def _guess_category(self, widget_name):
        """Guess widget category from name"""

        name_lower = widget_name.lower()

        categories = {
            'input': ['button', 'input', 'field', 'form', 'picker', 'slider', 'switch'],
            'media': ['image', 'video', 'audio', 'player', 'photo', 'camera'],
            'layout': ['list', 'grid', 'column', 'row', 'stack', 'layout', 'flex'],
            'navigation': ['navigation', 'route', 'page', 'tab', 'drawer', 'menu'],
            'container': ['container', 'box', 'card', 'panel', 'dialog'],
            'animation': ['animation', 'animated', 'transition', 'fade', 'slide'],
        }

        for category, patterns in categories.items():
            if any(pattern in name_lower for pattern in patterns):
                return category

        return 'display'

    def _is_container(self, widget_data):
        """Check if widget is a container"""

        # Check properties
        for prop in widget_data.get('properties', []):
            if prop['name'] in ['child', 'children', 'body', 'content']:
                return True

        # Check name
        container_patterns = ['container', 'box', 'panel', 'scaffold', 'layout', 'column', 'row']
        name_lower = widget_data['name'].lower()

        return any(pattern in name_lower for pattern in container_patterns)

    def _map_property_type(self, dart_type):
        """Map Dart type to property type"""

        type_mapping = {
            'String': 'string',
            'int': 'int',
            'double': 'double',
            'bool': 'bool',
            'Color': 'color',
            'Widget': 'widget',
            'List<Widget>': 'widget_list',
            'EdgeInsets': 'edge_insets',
            'Duration': 'duration',
            'TextStyle': 'text_style',
            'Alignment': 'alignment',
        }

        for dart, prop_type in type_mapping.items():
            if dart in dart_type:
                return prop_type

        return 'custom'

    def _generate_default_template(self, widget_data):
        """Generate default template"""

        template_lines = [f"{widget_data['name']}("]

        for prop in widget_data.get('properties', []):
            if prop.get('required'):
                template_lines.append(f"  {prop['name']}: {{{{{prop['name']}}}}},")
            else:
                template_lines.append(
                    f"  {{%if {prop['name']}%}}"
                    f"{prop['name']}: {{{{{prop['name']}}}}},{{%endif%}}"
                )

        template_lines.append(")")

        return '\n'.join(template_lines)