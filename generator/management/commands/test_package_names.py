# File: generator/management/commands/test_package_names.py
from django.core.management.base import BaseCommand
from generator.utils import FlutterCodeGenerator


class Command(BaseCommand):
    help = 'Test package name sanitization'

    def handle(self, *args, **options):
        generator = FlutterCodeGenerator(None)

        test_cases = [
            "متجر بسيط",
            "My Flutter App",
            "Test@App#123",
            "مرحبا Hello World",
            "123Numbers",
            "",
            "   spaces   "
        ]

        self.stdout.write("Testing package name sanitization:")
        for name in test_cases:
            result = generator.sanitize_package_name(name)
            self.stdout.write(f"'{name}' -> '{result}'")