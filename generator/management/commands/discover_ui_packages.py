# generator/management/commands/discover_ui_packages.py
# Discover essential UI packages for beautiful app design

from django.core.management.base import BaseCommand
from generator.package_analyzer import PackageAnalyzer
from generator.models import PubDevPackage, WidgetType, WidgetProperty, WidgetTemplate
import time


class Command(BaseCommand):
    help = 'Discover and setup essential UI packages for beautiful app design'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎨 Setting up UI packages for beautiful app design...\n'))

        analyzer = PackageAnalyzer()

        # Essential UI packages for beautiful design
        ui_packages = [
            {
                'name': 'google_fonts',
                'description': 'Beautiful typography',
                'widgets': []  # Utility package
            },
            {
                'name': 'font_awesome_flutter',
                'description': 'Awesome icons',
                'widgets': [
                    {
                        'name': 'FaIcon',
                        'properties': [
                            ('icon', 'custom', 'IconData', True),
                            ('size', 'double', 'double', False),
                            ('color', 'color', 'Color', False),
                        ]
                    }
                ]
            },
            {
                'name': 'animated_text_kit',
                'description': 'Animated text effects',
                'widgets': [
                    {
                        'name': 'AnimatedTextKit',
                        'properties': [
                            ('animatedTexts', 'list', 'List<AnimatedText>', True),
                            ('totalRepeatCount', 'int', 'int', False),
                            ('pause', 'duration', 'Duration', False),
                        ]
                    }
                ]
            },
            {
                'name': 'shimmer',
                'description': 'Shimmer loading effects',
                'widgets': [
                    {
                        'name': 'Shimmer',
                        'properties': [
                            ('child', 'widget', 'Widget', True),
                            ('gradient', 'custom', 'Gradient', False),
                            ('direction', 'enum', 'ShimmerDirection', False),
                        ]
                    }
                ]
            },
            {
                'name': 'flutter_staggered_grid_view',
                'description': 'Staggered grid layouts',
                'widgets': [
                    {
                        'name': 'StaggeredGrid',
                        'properties': [
                            ('crossAxisCount', 'int', 'int', True),
                            ('children', 'widget_list', 'List<Widget>', True),
                            ('mainAxisSpacing', 'double', 'double', False),
                            ('crossAxisSpacing', 'double', 'double', False),
                        ]
                    }
                ]
            },
            {
                'name': 'badges',
                'description': 'Beautiful badges for notifications',
                'widgets': [
                    {
                        'name': 'Badge',
                        'properties': [
                            ('child', 'widget', 'Widget', True),
                            ('badgeContent', 'widget', 'Widget', False),
                            ('badgeColor', 'color', 'Color', False),
                            ('position', 'custom', 'BadgePosition', False),
                        ]
                    }
                ]
            },
            {
                'name': 'flutter_speed_dial',
                'description': 'Floating action button with speed dial',
                'widgets': [
                    {
                        'name': 'SpeedDial',
                        'properties': [
                            ('children', 'list', 'List<SpeedDialChild>', False),
                            ('icon', 'custom', 'IconData', False),
                            ('activeIcon', 'custom', 'IconData', False),
                            ('backgroundColor', 'color', 'Color', False),
                        ]
                    }
                ]
            },
            {
                'name': 'percent_indicator',
                'description': 'Progress indicators',
                'widgets': [
                    {
                        'name': 'CircularPercentIndicator',
                        'properties': [
                            ('radius', 'double', 'double', True),
                            ('percent', 'double', 'double', True),
                            ('center', 'widget', 'Widget', False),
                            ('progressColor', 'color', 'Color', False),
                        ]
                    },
                    {
                        'name': 'LinearPercentIndicator',
                        'properties': [
                            ('percent', 'double', 'double', True),
                            ('width', 'double', 'double', False),
                            ('lineHeight', 'double', 'double', False),
                            ('progressColor', 'color', 'Color', False),
                        ]
                    }
                ]
            },
            {
                'name': 'flutter_svg',
                'description': 'SVG rendering',
                'widgets': [
                    {
                        'name': 'SvgPicture',
                        'properties': [
                            ('assetName', 'string', 'String', False),
                            ('width', 'double', 'double', False),
                            ('height', 'double', 'double', False),
                            ('color', 'color', 'Color', False),
                        ]
                    }
                ]
            }
        ]

        # Process each package
        for pkg_info in ui_packages:
            self.stdout.write(f'📦 Setting up {pkg_info["name"]}...')

            try:
                # Create package
                package, created = PubDevPackage.objects.get_or_create(
                    name=pkg_info['name'],
                    defaults={
                        'version': 'latest',
                        'description': pkg_info['description'],
                        'is_active': True
                    }
                )

                # Create widgets for this package
                for widget_info in pkg_info.get('widgets', []):
                    widget_type, created = WidgetType.objects.get_or_create(
                        name=widget_info['name'],
                        package=package,
                        defaults={
                            'dart_class_name': widget_info['name'],
                            'category': 'display',
                            'is_container': any(
                                p[0] in ['child', 'children'] for p in widget_info.get('properties', [])),
                            'is_active': True
                        }
                    )

                    if created:
                        # Add properties
                        for prop_name, prop_type, dart_type, required in widget_info.get('properties', []):
                            WidgetProperty.objects.create(
                                widget_type=widget_type,
                                name=prop_name,
                                property_type=prop_type,
                                dart_type=dart_type,
                                is_required=required
                            )

                        self.stdout.write(f'   ✅ Created widget: {widget_info["name"]}')
                    else:
                        self.stdout.write(f'   ℹ️ Widget exists: {widget_info["name"]}')

                # Try to discover more widgets from pub.dev
                try:
                    analyzer.auto_register_widgets(pkg_info['name'])
                    self.stdout.write(f'   ✅ Auto-discovered additional widgets')
                except:
                    pass  # Some packages might not have discoverable widgets

            except Exception as e:
                self.stdout.write(f'   ⚠️ Error with {pkg_info["name"]}: {str(e)}')

            time.sleep(0.5)  # Be nice to pub.dev API

        # Create additional Flutter navigation widgets
        self._create_navigation_widgets()

        self.stdout.write(self.style.SUCCESS('\n✅ UI packages setup complete!'))
        self.stdout.write('\n📝 Available components for beautiful design:')
        self.stdout.write('   • FaIcon - Font Awesome icons')
        self.stdout.write('   • AnimatedTextKit - Animated text')
        self.stdout.write('   • Shimmer - Loading effects')
        self.stdout.write('   • Badge - Notification badges')
        self.stdout.write('   • SpeedDial - FAB with options')
        self.stdout.write('   • CircularPercentIndicator - Progress circles')
        self.stdout.write('   • SvgPicture - SVG images')
        self.stdout.write('   • Drawer - Navigation drawer')
        self.stdout.write('   • ListTile - List items')
        self.stdout.write('   • Card - Material cards')

    def _create_navigation_widgets(self):
        """Create navigation-related widgets"""
        self.stdout.write('\n🧭 Setting up navigation widgets...')

        # Drawer widget
        drawer, created = WidgetType.objects.get_or_create(
            name='Drawer',
            defaults={
                'dart_class_name': 'Drawer',
                'category': 'navigation',
                'is_container': True,
                'documentation': 'Material Design navigation drawer',
                'is_active': True
            }
        )

        if created:
            WidgetProperty.objects.create(
                widget_type=drawer,
                name='child',
                property_type='widget',
                dart_type='Widget',
                is_required=False
            )
            WidgetProperty.objects.create(
                widget_type=drawer,
                name='backgroundColor',
                property_type='color',
                dart_type='Color',
                is_required=False
            )
            WidgetProperty.objects.create(
                widget_type=drawer,
                name='elevation',
                property_type='double',
                dart_type='double',
                is_required=False
            )
            self.stdout.write('   ✅ Created Drawer widget')

        # DrawerHeader widget
        drawer_header, created = WidgetType.objects.get_or_create(
            name='DrawerHeader',
            defaults={
                'dart_class_name': 'DrawerHeader',
                'category': 'navigation',
                'is_container': True,
                'is_active': True
            }
        )

        if created:
            WidgetProperty.objects.create(
                widget_type=drawer_header,
                name='child',
                property_type='widget',
                dart_type='Widget',
                is_required=True
            )
            WidgetProperty.objects.create(
                widget_type=drawer_header,
                name='decoration',
                property_type='custom',
                dart_type='BoxDecoration',
                is_required=False
            )
            self.stdout.write('   ✅ Created DrawerHeader widget')

        # UserAccountsDrawerHeader
        user_drawer, created = WidgetType.objects.get_or_create(
            name='UserAccountsDrawerHeader',
            defaults={
                'dart_class_name': 'UserAccountsDrawerHeader',
                'category': 'navigation',
                'is_active': True
            }
        )

        if created:
            WidgetProperty.objects.create(
                widget_type=user_drawer,
                name='accountName',
                property_type='widget',
                dart_type='Widget',
                is_required=False
            )
            WidgetProperty.objects.create(
                widget_type=user_drawer,
                name='accountEmail',
                property_type='widget',
                dart_type='Widget',
                is_required=False
            )
            WidgetProperty.objects.create(
                widget_type=user_drawer,
                name='currentAccountPicture',
                property_type='widget',
                dart_type='Widget',
                is_required=False
            )
            self.stdout.write('   ✅ Created UserAccountsDrawerHeader widget')

        # CircleAvatar widget
        avatar, created = WidgetType.objects.get_or_create(
            name='CircleAvatar',
            defaults={
                'dart_class_name': 'CircleAvatar',
                'category': 'display',
                'is_container': True,
                'is_active': True
            }
        )

        if created:
            WidgetProperty.objects.create(
                widget_type=avatar,
                name='radius',
                property_type='double',
                dart_type='double',
                is_required=False
            )
            WidgetProperty.objects.create(
                widget_type=avatar,
                name='backgroundColor',
                property_type='color',
                dart_type='Color',
                is_required=False
            )
            WidgetProperty.objects.create(
                widget_type=avatar,
                name='backgroundImage',
                property_type='custom',
                dart_type='ImageProvider',
                is_required=False
            )
            WidgetProperty.objects.create(
                widget_type=avatar,
                name='child',
                property_type='widget',
                dart_type='Widget',
                is_required=False
            )
            self.stdout.write('   ✅ Created CircleAvatar widget')

        # Divider widget
        divider, created = WidgetType.objects.get_or_create(
            name='Divider',
            defaults={
                'dart_class_name': 'Divider',
                'category': 'display',
                'is_active': True
            }
        )

        if created:
            WidgetProperty.objects.create(
                widget_type=divider,
                name='height',
                property_type='double',
                dart_type='double',
                is_required=False
            )
            WidgetProperty.objects.create(
                widget_type=divider,
                name='thickness',
                property_type='double',
                dart_type='double',
                is_required=False
            )
            WidgetProperty.objects.create(
                widget_type=divider,
                name='color',
                property_type='color',
                dart_type='Color',
                is_required=False
            )
            self.stdout.write('   ✅ Created Divider widget')