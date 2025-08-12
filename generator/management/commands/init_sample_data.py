# generator/management/commands/init_sample_data.py
# Initialize sample data for the dynamic widget system

from django.core.management.base import BaseCommand
from django.db import transaction
from generator.models import (
    FlutterProject, PubDevPackage, ProjectPackage,
    WidgetType, WidgetProperty, WidgetTemplate,
    DynamicPageComponent, PropertyTransformer
)
import json


class Command(BaseCommand):
    help = 'Initialize sample data for testing the dynamic widget system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing sample data before creating new'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Initializing Sample Data...'))

        try:
            with transaction.atomic():
                if options['clean']:
                    self._clean_sample_data()

                # Create sample project
                project = self._create_sample_project()

                # Create dynamic components
                self._create_dynamic_components(project)

                self.stdout.write(self.style.SUCCESS('\n✅ Sample data initialized successfully!'))
                self._print_summary(project)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

    def _clean_sample_data(self):
        """Clean existing sample data"""
        self.stdout.write('🧹 Cleaning existing sample data...')

        # Delete sample projects
        FlutterProject.objects.filter(name__startswith='Sample').delete()

    def _create_sample_project(self):
        """Create a sample e-commerce project"""
        self.stdout.write('\n📱 Creating sample project...')

        project = FlutterProject.objects.create(
            name='Sample E-Commerce App',
            package_name='com.example.ecommerce',
            description='A sample e-commerce app demonstrating dynamic widgets'
        )

        self.stdout.write(f'   ✅ Created project: {project.name}')

        # Add packages
        packages_data = [
            {'name': 'carousel_slider', 'version': '4.2.1'},
            {'name': 'cached_network_image', 'version': '3.3.0'},
            {'name': 'http', 'version': '0.13.6'},
        ]

        for pkg_data in packages_data:
            package, _ = PubDevPackage.objects.get_or_create(
                name=pkg_data['name'],
                defaults={'version': pkg_data['version']}
            )
            ProjectPackage.objects.create(
                project=project,
                package=package,
                version=pkg_data['version']
            )

        return project

    def _create_dynamic_components(self, project):
        """Create dynamic components for the project"""
        self.stdout.write('\n🧩 Creating dynamic components...')

        # Ensure basic widgets exist
        self._ensure_basic_widgets()

        # HomePage Components
        self._create_homepage_components(project)

        # ProductsPage Components
        self._create_products_page_components(project)

        # CartPage Components
        self._create_cart_page_components(project)

    def _ensure_basic_widgets(self):
        """Ensure basic Flutter widgets exist"""
        basic_widgets = [
            {
                'name': 'Container',
                'category': 'container',
                'is_container': True,
                'properties': [
                    ('width', 'double', False),
                    ('height', 'double', False),
                    ('color', 'color', False),
                    ('padding', 'edge_insets', False),
                    ('child', 'widget', False),
                ]
            },
            {
                'name': 'Text',
                'category': 'display',
                'properties': [
                    ('data', 'string', True),
                    ('style', 'text_style', False),
                ]
            },
            {
                'name': 'Column',
                'category': 'layout',
                'is_container': True,
                'can_have_multiple_children': True,
                'properties': [
                    ('children', 'widget_list', False),
                    ('mainAxisAlignment', 'enum', False),
                    ('crossAxisAlignment', 'enum', False),
                ]
            },
            {
                'name': 'Row',
                'category': 'layout',
                'is_container': True,
                'can_have_multiple_children': True,
                'properties': [
                    ('children', 'widget_list', False),
                    ('mainAxisAlignment', 'enum', False),
                    ('crossAxisAlignment', 'enum', False),
                ]
            },
            {
                'name': 'Card',
                'category': 'container',
                'is_container': True,
                'properties': [
                    ('child', 'widget', False),
                    ('elevation', 'double', False),
                    ('color', 'color', False),
                ]
            },
            {
                'name': 'ElevatedButton',
                'category': 'input',
                'is_container': True,
                'properties': [
                    ('onPressed', 'custom', True),
                    ('child', 'widget', False),
                ]
            },
            {
                'name': 'Image',
                'category': 'media',
                'properties': [
                    ('image', 'custom', True),
                    ('width', 'double', False),
                    ('height', 'double', False),
                    ('fit', 'enum', False),
                ]
            },
            {
                'name': 'ListTile',
                'category': 'display',
                'properties': [
                    ('title', 'widget', False),
                    ('subtitle', 'widget', False),
                    ('leading', 'widget', False),
                    ('trailing', 'widget', False),
                ]
            },
            {
                'name': 'SizedBox',
                'category': 'layout',
                'is_container': True,
                'properties': [
                    ('width', 'double', False),
                    ('height', 'double', False),
                    ('child', 'widget', False),
                ]
            },
        ]

        for widget_data in basic_widgets:
            widget_type, created = WidgetType.objects.get_or_create(
                name=widget_data['name'],
                defaults={
                    'dart_class_name': widget_data['name'],
                    'category': widget_data['category'],
                    'is_container': widget_data.get('is_container', False),
                    'can_have_multiple_children': widget_data.get('can_have_multiple_children', False),
                }
            )

            if created:
                # Add properties
                for prop_name, prop_type, is_required in widget_data.get('properties', []):
                    WidgetProperty.objects.create(
                        widget_type=widget_type,
                        name=prop_name,
                        property_type=prop_type,
                        dart_type=prop_type.title() if prop_type != 'custom' else 'dynamic',
                        is_required=is_required
                    )

                # Create default template
                self._create_default_template(widget_type)

    def _create_homepage_components(self, project):
        """Create HomePage components"""
        self.stdout.write('   📄 Creating HomePage...')

        # Title
        DynamicPageComponent.objects.create(
            project=project,
            page_name='HomePage',
            widget_type=WidgetType.objects.get(name='Text'),
            properties={
                'data': 'Welcome to Our Store',
                'style': {
                    'fontSize': 32,
                    'fontWeight': 'bold',
                    'color': '#2196F3'
                }
            },
            order=1
        )

        # Spacing
        DynamicPageComponent.objects.create(
            project=project,
            page_name='HomePage',
            widget_type=WidgetType.objects.get(name='SizedBox'),
            properties={'height': 20},
            order=2
        )

        # Hero Banner (if CarouselSlider exists)
        try:
            carousel = WidgetType.objects.get(name='CarouselSlider')
            DynamicPageComponent.objects.create(
                project=project,
                page_name='HomePage',
                widget_type=carousel,
                properties={
                    'items': [
                        {
                            'type': 'Container',
                            'properties': {
                                'width': 400,
                                'height': 200,
                                'color': '#FF5722'
                            }
                        },
                        {
                            'type': 'Container',
                            'properties': {
                                'width': 400,
                                'height': 200,
                                'color': '#4CAF50'
                            }
                        }
                    ],
                    'options': {
                        'height': 200,
                        'autoPlay': True,
                        'autoPlayInterval': 3000
                    }
                },
                order=3
            )
        except WidgetType.DoesNotExist:
            # Fallback to simple container
            DynamicPageComponent.objects.create(
                project=project,
                page_name='HomePage',
                widget_type=WidgetType.objects.get(name='Container'),
                properties={
                    'width': 400,
                    'height': 200,
                    'color': '#2196F3'
                },
                order=3
            )

        # Feature Cards Row
        DynamicPageComponent.objects.create(
            project=project,
            page_name='HomePage',
            widget_type=WidgetType.objects.get(name='Row'),
            properties={
                'mainAxisAlignment': 'spaceEvenly',
                'children': [
                    {
                        'type': 'Card',
                        'properties': {
                            'elevation': 4,
                            'child': {
                                'type': 'Container',
                                'properties': {
                                    'padding': {'all': 16},
                                    'child': {
                                        'type': 'Text',
                                        'properties': {'data': '🛍️ Shop Now'}
                                    }
                                }
                            }
                        }
                    },
                    {
                        'type': 'Card',
                        'properties': {
                            'elevation': 4,
                            'child': {
                                'type': 'Container',
                                'properties': {
                                    'padding': {'all': 16},
                                    'child': {
                                        'type': 'Text',
                                        'properties': {'data': '🎁 Deals'}
                                    }
                                }
                            }
                        }
                    },
                    {
                        'type': 'Card',
                        'properties': {
                            'elevation': 4,
                            'child': {
                                'type': 'Container',
                                'properties': {
                                    'padding': {'all': 16},
                                    'child': {
                                        'type': 'Text',
                                        'properties': {'data': '⭐ Popular'}
                                    }
                                }
                            }
                        }
                    }
                ]
            },
            order=4
        )

    def _create_products_page_components(self, project):
        """Create ProductsPage components"""
        self.stdout.write('   📄 Creating ProductsPage...')

        # Title
        DynamicPageComponent.objects.create(
            project=project,
            page_name='ProductsPage',
            widget_type=WidgetType.objects.get(name='Text'),
            properties={
                'data': 'Our Products',
                'style': {'fontSize': 28, 'fontWeight': 'bold'}
            },
            order=1
        )

        # Product List
        products = []
        for i in range(1, 4):
            products.append({
                'type': 'Card',
                'properties': {
                    'elevation': 2,
                    'child': {
                        'type': 'ListTile',
                        'properties': {
                            'title': {
                                'type': 'Text',
                                'properties': {'data': f'Product {i}'}
                            },
                            'subtitle': {
                                'type': 'Text',
                                'properties': {'data': f'${i * 10}.99'}
                            },
                            'leading': {
                                'type': 'Container',
                                'properties': {
                                    'width': 50,
                                    'height': 50,
                                    'color': '#E0E0E0'
                                }
                            },
                            'trailing': {
                                'type': 'ElevatedButton',
                                'properties': {
                                    'onPressed': '() {}',
                                    'child': {
                                        'type': 'Text',
                                        'properties': {'data': 'Add'}
                                    }
                                }
                            }
                        }
                    }
                }
            })

        DynamicPageComponent.objects.create(
            project=project,
            page_name='ProductsPage',
            widget_type=WidgetType.objects.get(name='Column'),
            properties={'children': products},
            order=2
        )

    def _create_cart_page_components(self, project):
        """Create CartPage components"""
        self.stdout.write('   📄 Creating CartPage...')

        # Title
        DynamicPageComponent.objects.create(
            project=project,
            page_name='CartPage',
            widget_type=WidgetType.objects.get(name='Text'),
            properties={
                'data': 'Shopping Cart',
                'style': {'fontSize': 28, 'fontWeight': 'bold'}
            },
            order=1
        )

        # Cart Items
        DynamicPageComponent.objects.create(
            project=project,
            page_name='CartPage',
            widget_type=WidgetType.objects.get(name='Card'),
            properties={
                'elevation': 2,
                'child': {
                    'type': 'Container',
                    'properties': {
                        'padding': {'all': 16},
                        'child': {
                            'type': 'Column',
                            'properties': {
                                'children': [
                                    {
                                        'type': 'Text',
                                        'properties': {'data': 'Cart is empty'}
                                    },
                                    {
                                        'type': 'SizedBox',
                                        'properties': {'height': 20}
                                    },
                                    {
                                        'type': 'ElevatedButton',
                                        'properties': {
                                            'onPressed': '() {}',
                                            'child': {
                                                'type': 'Text',
                                                'properties': {'data': 'Continue Shopping'}
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            },
            order=2
        )

    def _create_default_template(self, widget_type):
        """Create default template for a widget"""
        if widget_type.templates.filter(template_name='default').exists():
            return

        if widget_type.can_have_multiple_children:
            template_code = """{{ widget_name }}(
{% for prop in properties %}{% if prop.value != "null" %}  {{ prop.name }}: {{ prop.value }},
{% endif %}{% endfor %}{% if children %}  children: [
{% for child in children %}    {{ child }},
{% endfor %}  ],
{% endif %})"""
        elif widget_type.is_container:
            template_code = """{{ widget_name }}(
{% for prop in properties %}{% if prop.value != "null" %}  {{ prop.name }}: {{ prop.value }},
{% endif %}{% endfor %}{% if children %}  child: {{ children.0 }},
{% endif %})"""
        else:
            template_code = """{{ widget_name }}(
{% for prop in properties %}{% if prop.value != "null" %}  {{ prop.name }}: {{ prop.value }},
{% endif %}{% endfor %})"""

        WidgetTemplate.objects.create(
            widget_type=widget_type,
            template_name='default',
            template_code=template_code,
            is_active=True
        )

    def _print_summary(self, project):
        """Print summary of created data"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 SAMPLE DATA SUMMARY')
        self.stdout.write('=' * 60)

        # Project info
        self.stdout.write(f'\n🏗️ Project: {project.name}')
        self.stdout.write(f'   Package: {project.package_name}')

        # Components by page
        pages = project.dynamic_components.values_list('page_name', flat=True).distinct()
        self.stdout.write(f'\n📄 Pages ({pages.count()}):')
        for page in pages:
            component_count = project.dynamic_components.filter(page_name=page).count()
            self.stdout.write(f'   • {page}: {component_count} components')

        # Widget types used
        widget_types = set()
        for component in project.dynamic_components.all():
            widget_types.add(component.widget_type.name)

        self.stdout.write(f'\n🧩 Widget Types Used ({len(widget_types)}):')
        for widget in sorted(widget_types):
            self.stdout.write(f'   • {widget}')

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('🚀 NEXT STEPS:')
        self.stdout.write('=' * 60)
        self.stdout.write('1. Go to Django Admin to view the project')
        self.stdout.write('2. Generate Flutter code for the project')
        self.stdout.write('3. Test the dynamic widget generation')
        self.stdout.write('4. Discover more packages:')
        self.stdout.write('   python manage.py discover_package carousel_slider')
        self.stdout.write('5. Run tests:')
        self.stdout.write('   python manage.py shell < test_dynamic_generation.py')