# ===========================================
# File: generator/management/commands/test_apk_build.py
# Quick APK build test command
# ===========================================

from django.core.management.base import BaseCommand
from generator.models import FlutterProject
from generator.apk_builder import FlutterAPKBuilder


class Command(BaseCommand):
    help = 'Test APK building with a simple project'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-name',
            type=str,
            default='Test APK',
            help='Name of project to test with',
        )

    def handle(self, *args, **options):
        project_name = options['project_name']

        # Find or create test project
        try:
            project = FlutterProject.objects.get(name=project_name)
            self.stdout.write(f'Using existing project: {project_name}')
        except FlutterProject.DoesNotExist:
            self.stdout.write(f'Project "{project_name}" not found. Run setup_test_data first.')
            return

        # Test APK build
        self.stdout.write('🔨 Starting APK build test...')

        builder = FlutterAPKBuilder()

        def progress_callback(message, percentage):
            self.stdout.write(f'[{percentage}%] {message}')

        result = builder.build_apk(project, progress_callback)

        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ APK build successful!')
            )
            self.stdout.write(f'📱 APK file: {result["apk_filename"]}')
            self.stdout.write(f'📁 Location: {result["apk_path"]}')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ APK build failed: {result["error"]}')
            )