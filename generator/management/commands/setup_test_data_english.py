# File: generator/management/commands/setup_test_data_english.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from generator.models import FlutterProject, PubDevPackage, ProjectPackage, PageComponent
import json


class Command(BaseCommand):
    help = 'Creates test data with English project names for better compatibility'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete existing test data before creating new',
        )

    def handle(self, *args, **options):
        project_name = "Simple Store"  # English name

        self.stdout.write(
            self.style.SUCCESS(f'🚀 Setting up test data for: {project_name}')
        )

        try:
            with transaction.atomic():
                if options['clean']:
                    FlutterProject.objects.filter(name=project_name).delete()

                # Create Flutter project with English name
                project, created = FlutterProject.objects.get_or_create(
                    name=project_name,
                    defaults={
                        'package_name': 'com.example.simple_store',
                        'description': 'A simple e-commerce app for testing - created automatically'
                    }
                )

                # Create packages (same as before)
                packages_data = [
                    {'name': 'http', 'version': '0.13.6', 'description': 'HTTP client for API calls'},
                    {'name': 'provider', 'version': '6.1.1', 'description': 'State management solution'},
                ]

                for package_data in packages_data:
                    package, created = PubDevPackage.objects.get_or_create(
                        name=package_data['name'],
                        defaults=package_data
                    )
                    ProjectPackage.objects.get_or_create(
                        project=project,
                        package=package,
                        defaults={'version': package.version}
                    )

                # Create components with English text that displays Arabic
                components_data = [
                    {
                        'page_name': 'HomePage',
                        'component_type': 'text',
                        'properties': {'text': 'مرحباً بكم في متجرنا البسيط', 'fontSize': 28, 'color': 'blue'},
                        'order': 1
                    },
                    {
                        'page_name': 'HomePage',
                        'component_type': 'button',
                        'properties': {'text': 'عرض المنتجات', 'color': 'green'},
                        'order': 2
                    },
                ]

                for comp_data in components_data:
                    PageComponent.objects.get_or_create(
                        project=project,
                        page_name=comp_data['page_name'],
                        component_type=comp_data['component_type'],
                        order=comp_data['order'],
                        defaults={'properties': comp_data['properties']}
                    )

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully created test data for "{project_name}"!')
                )

        except Exception as e:
            raise CommandError(f'Failed to create test data: {str(e)}')