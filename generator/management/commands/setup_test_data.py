# ===========================================
# File: generator/management/commands/setup_test_data.py
# ===========================================

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from generator.models import FlutterProject, PubDevPackage, ProjectPackage, PageComponent
import json


class Command(BaseCommand):
    help = 'Creates test data for Flutter Generator - E-commerce app with multiple screens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete existing test data before creating new',
        )
        parser.add_argument(
            '--project-name',
            type=str,
            default='متجر بسيط',
            help='Name of the test project (default: متجر بسيط)',
        )

    def handle(self, *args, **options):
        project_name = options['project_name']

        self.stdout.write(
            self.style.SUCCESS(f'🚀 Setting up test data for: {project_name}')
        )

        try:
            with transaction.atomic():
                if options['clean']:
                    self.clean_existing_data(project_name)

                # Step 1: Create/Get Flutter Project
                project = self.create_flutter_project(project_name)

                # Step 2: Create/Get Packages
                packages = self.create_packages()

                # Step 3: Link Packages to Project
                self.link_packages_to_project(project, packages)

                # Step 4: Create Components for all pages
                self.create_components(project)

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully created test data for "{project_name}"!')
                )
                self.print_summary(project)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating test data: {str(e)}')
            )
            raise CommandError(f'Failed to create test data: {str(e)}')

    def clean_existing_data(self, project_name):
        """Delete existing test data"""
        self.stdout.write('🧹 Cleaning existing test data...')

        # Delete project and all related data will cascade
        deleted_projects = FlutterProject.objects.filter(name=project_name).delete()
        if deleted_projects[0] > 0:
            self.stdout.write(f'   Deleted existing project: {project_name}')

        # Clean orphaned packages (not linked to any project)
        orphaned_packages = PubDevPackage.objects.filter(projectpackage__isnull=True)
        deleted_packages = orphaned_packages.delete()
        if deleted_packages[0] > 0:
            self.stdout.write(f'   Deleted {deleted_packages[0]} orphaned packages')

    def create_flutter_project(self, project_name):
        """Create the main Flutter project"""
        self.stdout.write('📱 Creating Flutter project...')

        project, created = FlutterProject.objects.get_or_create(
            name=project_name,
            defaults={
                'package_name': 'com.example.simple_store',
                'description': 'تطبيق متجر إلكتروني بسيط للاختبار - تم إنشاؤه تلقائياً'
            }
        )

        if created:
            self.stdout.write(f'   ✅ Created new project: {project_name}')
        else:
            self.stdout.write(f'   ℹ️  Using existing project: {project_name}')

        return project

    def create_packages(self):
        """Create pub.dev packages"""
        self.stdout.write('📦 Creating pub.dev packages...')

        packages_data = [
            {
                'name': 'http',
                'version': '0.13.6',
                'description': 'HTTP client for API calls',
                'homepage': 'https://pub.dev/packages/http'
            },
            {
                'name': 'provider',
                'version': '6.1.1',
                'description': 'State management solution',
                'homepage': 'https://pub.dev/packages/provider'
            },
            {
                'name': 'cached_network_image',
                'version': '3.3.0',
                'description': 'Image loading and caching',
                'homepage': 'https://pub.dev/packages/cached_network_image'
            },
            {
                'name': 'shared_preferences',
                'version': '2.2.2',
                'description': 'Local data storage',
                'homepage': 'https://pub.dev/packages/shared_preferences'
            }
        ]

        created_packages = []
        for package_data in packages_data:
            package, created = PubDevPackage.objects.get_or_create(
                name=package_data['name'],
                defaults=package_data
            )

            if created:
                self.stdout.write(f'   ✅ Created package: {package_data["name"]} v{package_data["version"]}')
            else:
                self.stdout.write(f'   ℹ️  Using existing package: {package_data["name"]}')

            created_packages.append(package)

        return created_packages

    def link_packages_to_project(self, project, packages):
        """Link packages to the project"""
        self.stdout.write('🔗 Linking packages to project...')

        for package in packages:
            project_package, created = ProjectPackage.objects.get_or_create(
                project=project,
                package=package,
                defaults={'version': package.version}
            )

            if created:
                self.stdout.write(f'   ✅ Linked: {package.name}')
            else:
                self.stdout.write(f'   ℹ️  Already linked: {package.name}')

    def create_components(self, project):
        """Create all page components"""
        self.stdout.write('🧩 Creating page components...')

        components_data = [
            # HomePage Components
            {
                'page_name': 'HomePage',
                'component_type': 'text',
                'properties': {
                    'text': 'مرحباً بكم في متجرنا البسيط',
                    'fontSize': 28,
                    'color': 'blue'
                },
                'order': 1
            },
            {
                'page_name': 'HomePage',
                'component_type': 'button',
                'properties': {
                    'text': 'عرض المنتجات',
                    'color': 'green'
                },
                'order': 2
            },
            {
                'page_name': 'HomePage',
                'component_type': 'button',
                'properties': {
                    'text': 'السلة',
                    'color': 'orange'
                },
                'order': 3
            },

            # ProductsPage Components
            {
                'page_name': 'ProductsPage',
                'component_type': 'text',
                'properties': {
                    'text': 'قائمة المنتجات',
                    'fontSize': 24,
                    'color': 'black'
                },
                'order': 1
            },
            {
                'page_name': 'ProductsPage',
                'component_type': 'container',
                'properties': {
                    'width': 300,
                    'height': 150,
                    'color': 'lightblue'
                },
                'order': 2
            },
            {
                'page_name': 'ProductsPage',
                'component_type': 'button',
                'properties': {
                    'text': 'إضافة للسلة',
                    'color': 'red'
                },
                'order': 3
            },

            # CartPage Components
            {
                'page_name': 'CartPage',
                'component_type': 'text',
                'properties': {
                    'text': 'سلة التسوق',
                    'fontSize': 24,
                    'color': 'purple'
                },
                'order': 1
            },
            {
                'page_name': 'CartPage',
                'component_type': 'container',
                'properties': {
                    'width': 350,
                    'height': 200,
                    'color': 'yellow'
                },
                'order': 2
            },

            # ProfilePage Components
            {
                'page_name': 'ProfilePage',
                'component_type': 'text',
                'properties': {
                    'text': 'الملف الشخصي',
                    'fontSize': 24,
                    'color': 'brown'
                },
                'order': 1
            },
            {
                'page_name': 'ProfilePage',
                'component_type': 'container',
                'properties': {
                    'width': 300,
                    'height': 100,
                    'color': 'pink'
                },
                'order': 2
            }
        ]

        created_count = 0
        for comp_data in components_data:
            component, created = PageComponent.objects.get_or_create(
                project=project,
                page_name=comp_data['page_name'],
                component_type=comp_data['component_type'],
                order=comp_data['order'],
                defaults={
                    'properties': comp_data['properties']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    f'   ✅ Created: {comp_data["page_name"]} -> {comp_data["component_type"]}'
                )
            else:
                self.stdout.write(
                    f'   ℹ️  Exists: {comp_data["page_name"]} -> {comp_data["component_type"]}'
                )

        self.stdout.write(f'   📊 Total components created: {created_count}')

    def print_summary(self, project):
        """Print summary of created data"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('📊 TEST DATA SUMMARY'))
        self.stdout.write('=' * 50)

        # Project info
        self.stdout.write(f'🏗️  Project: {project.name}')
        self.stdout.write(f'   Package: {project.package_name}')
        self.stdout.write(f'   Created: {project.created_at.strftime("%Y-%m-%d %H:%M")}')

        # Packages info
        packages = project.packages.all()
        self.stdout.write(f'\n📦 Packages ({packages.count()}):')
        for proj_pkg in packages:
            self.stdout.write(f'   • {proj_pkg.package.name} v{proj_pkg.package.version}')

        # Components info by page
        components = project.components.all()
        self.stdout.write(f'\n🧩 Components ({components.count()}):')

        pages = components.values_list('page_name', flat=True).distinct()
        for page in pages:
            page_components = components.filter(page_name=page)
            self.stdout.write(f'   📄 {page} ({page_components.count()} components):')
            for comp in page_components:
                self.stdout.write(f'      - {comp.component_type}')

        # Next steps
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.WARNING('🚀 NEXT STEPS:'))
        self.stdout.write('=' * 50)
        self.stdout.write('1. Go to Django Admin: http://127.0.0.1:8000/admin/')
        self.stdout.write('2. Navigate to Flutter Projects')
        self.stdout.write(f'3. Find "{project.name}" and click "👁️ معاينة"')
        self.stdout.write('4. Review generated code')
        self.stdout.write('5. Click "📦 ZIP" to download')
        self.stdout.write('6. Test with: flutter pub get && flutter run')
        self.stdout.write('\n✨ Happy testing!')


# ===========================================
# Alternative Command: setup_single_project.py
# For creating just one project quickly
# ===========================================

class Command2(BaseCommand):
    help = 'Creates a single simple Flutter project for quick testing'

    def add_arguments(self, parser):
        parser.add_argument('project_name', type=str, help='Name of the project to create')
        parser.add_argument(
            '--package-name',
            type=str,
            help='Flutter package name (default: com.example.PROJECT_NAME)',
        )

    def handle(self, *args, **options):
        project_name = options['project_name']
        package_name = options.get('package_name') or f'com.example.{project_name.lower().replace(" ", "_")}'

        self.stdout.write(f'Creating simple project: {project_name}')

        # Create project
        project = FlutterProject.objects.create(
            name=project_name,
            package_name=package_name,
            description=f'Test project created via management command'
        )

        # Add basic http package
        http_package, _ = PubDevPackage.objects.get_or_create(
            name='http',
            defaults={
                'version': '0.13.6',
                'description': 'HTTP client'
            }
        )

        ProjectPackage.objects.create(
            project=project,
            package=http_package
        )

        # Add simple components
        PageComponent.objects.create(
            project=project,
            page_name='HomePage',
            component_type='text',
            properties={'text': f'Welcome to {project_name}', 'fontSize': 24},
            order=1
        )

        PageComponent.objects.create(
            project=project,
            page_name='HomePage',
            component_type='button',
            properties={'text': 'Click Me', 'color': 'blue'},
            order=2
        )

        self.stdout.write(
            self.style.SUCCESS(f'✅ Created simple project: {project_name}')
        )


# ===========================================
# USAGE EXAMPLES AND INSTRUCTIONS
# ===========================================

"""
DIRECTORY STRUCTURE TO CREATE:
generator/
├── management/
│   ├── __init__.py          (empty file)
│   └── commands/
│       ├── __init__.py      (empty file)
│       └── setup_test_data.py   (main command file above)

USAGE COMMANDS:

1. Create full test data:
   python manage.py setup_test_data

2. Clean and recreate:
   python manage.py setup_test_data --clean

3. Custom project name:
   python manage.py setup_test_data --project-name "My Test App"

4. Clean with custom name:
   python manage.py setup_test_data --clean --project-name "My Test App"

WHAT THIS CREATES:
- 1 Flutter project: "متجر بسيط"
- 4 pub.dev packages: http, provider, cached_network_image, shared_preferences
- 4 project-package links
- 10 page components across 4 pages (HomePage, ProductsPage, CartPage, ProfilePage)

AFTER RUNNING:
1. Check Django admin to see all created data
2. Go to Flutter Projects and test the "معاينة" and "ZIP" buttons
3. Extract ZIP and test with Flutter: flutter pub get && flutter run
"""