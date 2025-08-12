# generator/management/commands/setup_complete_system.py
# Management command to setup the complete app building system

from django.core.management.base import BaseCommand
from django.db import transaction
import json


class Command(BaseCommand):
    help = 'Setup complete app building system with navigation, API, state management, etc.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Setting up Complete App Building System...'))

        try:
            # First, import the extended models
            self._setup_extended_models()

            # Setup sample configurations
            self._create_sample_app_configurations()

            self.stdout.write(self.style.SUCCESS('\n✅ Complete system setup finished!'))
            self._print_next_steps()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

    def _setup_extended_models(self):
        """Import and register extended models"""
        self.stdout.write('\n📦 Setting up extended models...')

        # Import the models to register them
        try:
            from generator.models_extended import (
                AppRoute, NavigationItem, AppState, StateAction,
                APIConfiguration, APIEndpoint, DataModel,
                AuthConfiguration, FormConfiguration, FormField,
                CustomFunction, EventHandler, LocalStorage,
                DynamicListConfiguration, ConditionalWidget,
                AppConfiguration
            )
            self.stdout.write('   ✅ Extended models imported successfully')

            # Run migrations
            self.stdout.write('   📝 Run these commands to create migrations:')
            self.stdout.write('      python manage.py makemigrations')
            self.stdout.write('      python manage.py migrate')

        except ImportError as e:
            self.stdout.write(self.style.WARNING(
                '   ⚠️  Extended models not found. Please create generator/models_extended.py first'
            ))

    def _create_sample_app_configurations(self):
        """Create sample configurations for testing"""
        self.stdout.write('\n📱 Creating sample app configurations...')

        from generator.models import FlutterProject
        from generator.models_extended import (
            AppConfiguration, AppRoute, AppState,
            APIConfiguration, APIEndpoint, DataModel
        )

        # Get or create a sample project
        project, created = FlutterProject.objects.get_or_create(
            name='Complete App Example',
            defaults={
                'package_name': 'com.example.complete',
                'description': 'A complete app with all features'
            }
        )

        if created:
            self.stdout.write(f'   ✅ Created sample project: {project.name}')

        with transaction.atomic():
            # 1. App Configuration
            app_config, _ = AppConfiguration.objects.get_or_create(
                project=project,
                defaults={
                    'app_type': 'ecommerce',
                    'state_management': 'provider',
                    'navigation_type': 'bottom_nav',
                    'uses_authentication': True,
                    'uses_api': True,
                    'uses_local_storage': True,
                    'primary_color': '#6366F1',
                    'secondary_color': '#10B981'
                }
            )
            self.stdout.write('   ✅ Created app configuration')

            # 2. Routes
            routes_data = [
                {'route_name': '/', 'page_name': 'HomePage', 'is_initial': True},
                {'route_name': '/products', 'page_name': 'ProductsPage'},
                {'route_name': '/product/:id', 'page_name': 'ProductDetailPage'},
                {'route_name': '/cart', 'page_name': 'CartPage'},
                {'route_name': '/profile', 'page_name': 'ProfilePage', 'is_protected': True},
                {'route_name': '/login', 'page_name': 'LoginPage'},
                {'route_name': '/register', 'page_name': 'RegisterPage'},
            ]

            for route_data in routes_data:
                AppRoute.objects.get_or_create(
                    project=project,
                    route_name=route_data['route_name'],
                    defaults={
                        'route_path': route_data['route_name'],
                        'page_name': route_data['page_name'],
                        'is_protected': route_data.get('is_protected', False),
                        'is_initial': route_data.get('is_initial', False)
                    }
                )
            self.stdout.write(f'   ✅ Created {len(routes_data)} routes')

            # 3. State Variables
            states_data = [
                {'variable_name': 'user', 'variable_type': 'map', 'initial_value': {}},
                {'variable_name': 'isAuthenticated', 'variable_type': 'bool', 'initial_value': False},
                {'variable_name': 'products', 'variable_type': 'list', 'initial_value': []},
                {'variable_name': 'cart', 'variable_type': 'list', 'initial_value': []},
                {'variable_name': 'cartTotal', 'variable_type': 'double', 'initial_value': 0.0},
                {'variable_name': 'isLoading', 'variable_type': 'bool', 'initial_value': False},
            ]

            for state_data in states_data:
                AppState.objects.get_or_create(
                    project=project,
                    variable_name=state_data['variable_name'],
                    defaults={
                        'variable_type': state_data['variable_type'],
                        'initial_value': state_data['initial_value'],
                        'is_persistent': state_data['variable_name'] in ['user', 'cart']
                    }
                )
            self.stdout.write(f'   ✅ Created {len(states_data)} state variables')

            # 4. API Configuration
            api_config, _ = APIConfiguration.objects.get_or_create(
                project=project,
                defaults={
                    'base_url': 'https://api.example.com',
                    'timeout': 30,
                    'retry_count': 3,
                    'default_headers': {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                }
            )
            self.stdout.write('   ✅ Created API configuration')

            # 5. API Endpoints
            endpoints_data = [
                {
                    'endpoint_name': 'login',
                    'endpoint_path': '/auth/login',
                    'method': 'POST',
                    'request_body_template': {'email': '', 'password': ''}
                },
                {
                    'endpoint_name': 'register',
                    'endpoint_path': '/auth/register',
                    'method': 'POST',
                    'request_body_template': {'name': '', 'email': '', 'password': ''}
                },
                {
                    'endpoint_name': 'get_products',
                    'endpoint_path': '/products',
                    'method': 'GET'
                },
                {
                    'endpoint_name': 'get_product',
                    'endpoint_path': '/products/:id',
                    'method': 'GET'
                },
                {
                    'endpoint_name': 'add_to_cart',
                    'endpoint_path': '/cart/add',
                    'method': 'POST',
                    'requires_auth': True,
                    'request_body_template': {'product_id': '', 'quantity': 1}
                },
            ]

            for endpoint_data in endpoints_data:
                APIEndpoint.objects.get_or_create(
                    project=project,
                    endpoint_name=endpoint_data['endpoint_name'],
                    defaults={
                        'endpoint_path': endpoint_data['endpoint_path'],
                        'method': endpoint_data['method'],
                        'requires_auth': endpoint_data.get('requires_auth', False),
                        'request_body_template': endpoint_data.get('request_body_template', {})
                    }
                )
            self.stdout.write(f'   ✅ Created {len(endpoints_data)} API endpoints')

            # 6. Data Models
            models_data = [
                {
                    'model_name': 'User',
                    'fields': [
                        {'name': 'id', 'type': 'int', 'required': True},
                        {'name': 'name', 'type': 'String', 'required': True},
                        {'name': 'email', 'type': 'String', 'required': True},
                        {'name': 'avatar', 'type': 'String', 'required': False},
                    ]
                },
                {
                    'model_name': 'Product',
                    'fields': [
                        {'name': 'id', 'type': 'int', 'required': True},
                        {'name': 'name', 'type': 'String', 'required': True},
                        {'name': 'description', 'type': 'String', 'required': False},
                        {'name': 'price', 'type': 'double', 'required': True},
                        {'name': 'image', 'type': 'String', 'required': False},
                    ]
                },
                {
                    'model_name': 'CartItem',
                    'fields': [
                        {'name': 'product', 'type': 'Product', 'required': True},
                        {'name': 'quantity', 'type': 'int', 'required': True},
                    ]
                }
            ]

            for model_data in models_data:
                DataModel.objects.get_or_create(
                    project=project,
                    model_name=model_data['model_name'],
                    defaults={
                        'fields': model_data['fields']
                    }
                )
            self.stdout.write(f'   ✅ Created {len(models_data)} data models')

    def _print_next_steps(self):
        """Print next steps for the user"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📋 NEXT STEPS')
        self.stdout.write('=' * 60)

        self.stdout.write('\n1️⃣  Run migrations:')
        self.stdout.write('   python manage.py makemigrations')
        self.stdout.write('   python manage.py migrate')

        self.stdout.write('\n2️⃣  Create a complete app:')
        self.stdout.write('   python manage.py create_complete_app --name "My App"')

        self.stdout.write('\n3️⃣  Configure in Admin:')
        self.stdout.write('   - Add routes and navigation')
        self.stdout.write('   - Configure API endpoints')
        self.stdout.write('   - Setup state management')
        self.stdout.write('   - Create forms')

        self.stdout.write('\n4️⃣  Generate and build:')
        self.stdout.write('   - Preview code')
        self.stdout.write('   - Download ZIP')
        self.stdout.write('   - Build APK')

        self.stdout.write('\n' + '=' * 60)