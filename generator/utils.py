# ===========================================
# File: generator/utils.py (UPDATED - Fix package name generation)
# ===========================================

import requests
import json
import os
import re
import unicodedata
from django.utils.text import slugify


class PubDevSync:
    def __init__(self):
        self.base_url = "https://pub.dev/api"

    def search_packages(self, query, page=1):
        """البحث في pub.dev"""
        url = f"{self.base_url}/search"
        params = {'q': query, 'page': page}
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else None

    def get_package_info(self, package_name):
        """جلب معلومات حزمة محددة"""
        url = f"{self.base_url}/packages/{package_name}"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None

    def update_package_info(self, package):
        """تحديث معلومات حزمة موجودة"""
        info = self.get_package_info(package.name)
        if info:
            package.version = info.get('latest', {}).get('version', package.version)
            package.description = info.get('description', package.description)
            package.save()


class FlutterCodeGenerator:
    def __init__(self, project):
        self.project = project

    def sanitize_package_name(self, name):
        """Convert any name to valid Dart package name"""
        # Remove Arabic and special characters, convert to ASCII
        ascii_name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

        # If nothing left after ASCII conversion, use a default
        if not ascii_name.strip():
            ascii_name = "flutter_app"

        # Convert to lowercase and replace spaces/special chars with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', ascii_name.lower())

        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)

        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')

        # Ensure it starts with a letter
        if sanitized and sanitized[0].isdigit():
            sanitized = 'app_' + sanitized

        # Ensure it's not empty
        if not sanitized:
            sanitized = "flutter_app"

        return sanitized

    def generate_pubspec_yaml(self):
        """إنشاء ملف pubspec.yaml"""
        # Create safe package name from project name
        safe_package_name = self.sanitize_package_name(self.project.name)

        dependencies = {
            'flutter': {'sdk': 'flutter'},
            'cupertino_icons': '^1.0.2'
        }

        # إضافة حزم المشروع
        for project_package in self.project.packages.all():
            version = project_package.version or f"^{project_package.package.version}"
            dependencies[project_package.package.name] = version

        pubspec = {
            'name': safe_package_name,  # Use sanitized name
            'description': self.project.description or "A new Flutter project.",
            'version': '1.0.0+1',
            'environment': {
                'sdk': '>=2.17.0 <4.0.0'
            },
            'dependencies': dependencies,
            'dev_dependencies': {
                'flutter_test': {'sdk': 'flutter'},
                'flutter_lints': '^2.0.0'
            },
            'flutter': {
                'uses-material-design': True
            }
        }

        import yaml
        return yaml.dump(pubspec, default_flow_style=False, allow_unicode=True)

    def generate_main_dart(self):
        """إنشاء ملف main.dart"""
        imports = [
            "import 'package:flutter/material.dart';"
        ]

        # إضافة imports للحزم المستخدمة
        for project_package in self.project.packages.all():
            imports.append(f"import 'package:{project_package.package.name}/{project_package.package.name}.dart';")

        pages = self.generate_pages()

        # Use original project name for display (supports Arabic)
        display_name = self.project.name

        return f"""
{chr(10).join(imports)}

void main() {{
  runApp(MyApp());
}}

class MyApp extends StatelessWidget {{
  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{display_name}',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: HomePage(),
    );
  }}
}}

{pages}
"""

    def generate_pages(self):
        """إنشاء صفحات المشروع"""
        pages_code = []

        # تجميع المكونات حسب الصفحة
        pages = {}
        for component in self.project.components.all():
            page_name = component.page_name
            if page_name not in pages:
                pages[page_name] = []
            pages[page_name].append(component)

        # إنشاء كود كل صفحة
        for page_name, components in pages.items():
            page_code = self.generate_page_class(page_name, components)
            pages_code.append(page_code)

        return "\n\n".join(pages_code)

    def generate_page_class(self, page_name, components):
        """إنشاء كلاس صفحة واحدة"""
        widgets = []

        for component in components:
            widget_code = self.generate_widget_code(component)
            widgets.append(widget_code)

        body_content = "Column(children: [" + ", ".join(widgets) + "])"

        return f"""
class {page_name} extends StatelessWidget {{
  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: Text('{page_name}'),
      ),
      body: {body_content},
    );
  }}
}}
"""

    def generate_widget_code(self, component):
        """إنشاء كود widget واحد"""
        props = component.properties

        widget_generators = {
            'text': lambda: f"Text('{props.get('text', 'نص افتراضي')}', style: TextStyle(fontSize: {props.get('fontSize', 16)}.0, color: Colors.{props.get('color', 'black')}))",
            'container': lambda: f"Container(width: {props.get('width', 100)}.0, height: {props.get('height', 100)}.0, color: Colors.{props.get('color', 'blue')})",
            'button': lambda: f"ElevatedButton(onPressed: () {{}}, child: Text('{props.get('text', 'اضغط هنا')}'))",
        }

        generator = widget_generators.get(component.component_type)
        return generator() if generator else f"Text('مكون غير مدعوم: {component.component_type}')"

    def create_project_files(self, project_dir):
        """إنشاء ملفات المشروع"""
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'lib'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'android'), exist_ok=True)

        # إنشاء pubspec.yaml
        with open(os.path.join(project_dir, 'pubspec.yaml'), 'w', encoding='utf-8') as f:
            f.write(self.generate_pubspec_yaml())

        # إنشاء main.dart
        with open(os.path.join(project_dir, 'lib', 'main.dart'), 'w', encoding='utf-8') as f:
            f.write(self.generate_main_dart())

    def generate_full_project(self):
        """إنشاء كود المشروع الكامل"""
        return {
            'pubspec.yaml': self.generate_pubspec_yaml(),
            'lib/main.dart': self.generate_main_dart()
        }


# ===========================================
# Test the package name sanitization
# ===========================================

def test_package_name_sanitization():
    """Test function to verify package name conversion"""
    generator = FlutterCodeGenerator(None)

    test_cases = [
        ("متجر بسيط", "flutter_app"),  # Arabic -> default
        ("My App", "my_app"),
        ("Test-App_2023", "test_app_2023"),
        ("123 Numbers", "app_123_numbers"),
        ("Special@#$%Chars", "special_chars"),
        ("", "flutter_app"),
        ("   ", "flutter_app"),
        ("مرحبا Hello", "hello"),  # Mixed Arabic/English
    ]

    print("Testing package name sanitization:")
    for input_name, expected in test_cases:
        result = generator.sanitize_package_name(input_name)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_name}' -> '{result}' (expected: '{expected}')")
