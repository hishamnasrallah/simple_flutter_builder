# generator/utils.py
# FIXED VERSION - Handles carousel_slider import conflict with Flutter 3.16+

import requests
import json
import os
import re
import unicodedata
import yaml
from django.utils.text import slugify


class PubDevSync:
    """Enhanced sync with dynamic widget discovery"""

    def __init__(self):
        self.base_url = "https://pub.dev/api"

    def search_packages(self, query, page=1):
        """Search pub.dev packages"""
        url = f"{self.base_url}/search"
        params = {'q': query, 'page': page}
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else None

    def get_package_info(self, package_name):
        """Get package information"""
        url = f"{self.base_url}/packages/{package_name}"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None

    def update_package_info(self, package):
        """Update package information and discover widgets"""
        from .package_analyzer import PackageAnalyzer

        info = self.get_package_info(package.name)
        if info:
            package.version = info.get('latest', {}).get('version', package.version)
            package.description = info.get('description', package.description)
            package.save()

            # Auto-discover widgets for dynamic system
            analyzer = PackageAnalyzer()
            analyzer.auto_register_widgets(package.name)


class FlutterCodeGenerator:
    """Flutter code generator with automatic dynamic widget support"""

    def __init__(self, project):
        self.project = project

        # Automatically use dynamic generator if dynamic components exist
        if hasattr(project, 'dynamic_components') and project.dynamic_components.exists():
            self.use_dynamic = True
            from .widget_generator import DynamicWidgetGenerator
            self.widget_generator = DynamicWidgetGenerator()
        else:
            self.use_dynamic = False

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
        """Generate pubspec.yaml with dynamic packages"""
        safe_package_name = self.sanitize_package_name(self.project.name)

        dependencies = {
            'flutter': {'sdk': 'flutter'},
            'cupertino_icons': '^1.0.2'
        }

        # Check if carousel_slider is needed
        uses_carousel = False

        # Add project packages
        for project_package in self.project.packages.all():
            # Skip carousel_slider for now due to conflict
            if project_package.package.name == 'carousel_slider':
                uses_carousel = True
                continue

            # Fix version handling - never use "latest"
            version = project_package.version
            if not version or version.lower() == 'latest':
                # Use package's stored version or default to 'any'
                version = project_package.package.version
                if not version or version.lower() == 'latest':
                    version = 'any'  # Flutter accepts 'any' as a version constraint

            # Ensure version has proper format
            if version and version != 'any' and not version.startswith('^') and not version.startswith('>='):
                version = f"^{version}"

            dependencies[project_package.package.name] = version

            # Add packages from dynamic components if using dynamic system
            if self.use_dynamic:
                used_packages = set()
                for component in self.project.dynamic_components.all():
                    if component.widget_type.package:
                        # Skip carousel_slider
                        if component.widget_type.package.name == 'carousel_slider':
                            uses_carousel = True
                            continue
                        used_packages.add(component.widget_type.package)

                for package in used_packages:
                    if package.name not in dependencies:
                        # Fix version handling for dynamic packages
                        version = package.version
                        if not version or version.lower() == 'latest':
                            version = 'any'
                        elif not version.startswith('^') and not version.startswith('>='):
                            version = f"^{version}"
                        dependencies[package.name] = version

        # Use flutter_carousel_widget instead of carousel_slider (no conflicts)
        if uses_carousel:
            dependencies['flutter_carousel_widget'] = '^2.2.0'

        pubspec = {
            'name': safe_package_name,
            'description': self.project.description or "A Flutter project generated with dynamic widgets.",
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

        return yaml.dump(pubspec, default_flow_style=False, allow_unicode=True)

    def generate_main_dart(self):
        """Generate main.dart using dynamic widgets if available"""
        if self.use_dynamic:
            return self._generate_dynamic_main_dart()
        else:
            return self._generate_legacy_main_dart()

    def _generate_dynamic_main_dart(self):
        """Generate main.dart using dynamic widgets"""
        # Collect all components
        components_by_page = {}

        for component in self.project.dynamic_components.all():
            page_name = component.page_name
            if page_name not in components_by_page:
                components_by_page[page_name] = []
            components_by_page[page_name].append(component)

        # Generate imports (with carousel fix)
        imports = self._generate_imports(components_by_page)

        # Generate pages
        pages = self._generate_pages(components_by_page)

        # Use original project name for display
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
        useMaterial3: true,
      ),
      home: HomePage(),
      debugShowCheckedModeBanner: false,
    );
  }}
}}

{pages}
"""

    def _generate_legacy_main_dart(self):
        """Generate main.dart for legacy components"""
        imports = [
            "import 'package:flutter/material.dart';"
        ]

        # Add imports for packages (skip carousel_slider)
        for project_package in self.project.packages.all():
            if project_package.package.name != 'carousel_slider':
                imports.append(f"import 'package:{project_package.package.name}/{project_package.package.name}.dart';")

        pages = self._generate_legacy_pages()

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

    def _generate_imports(self, components_by_page):
        """Generate import statements for dynamic components"""
        imports = set()
        imports.add("import 'package:flutter/material.dart';")

        uses_carousel = False

        # Collect all widget types
        widget_types = set()
        for page_components in components_by_page.values():
            for component in page_components:
                widget_types.add(component.widget_type)
                if component.widget_type.name == 'CarouselSlider':
                    uses_carousel = True
                elif component.widget_type.package:
                    if component.widget_type.import_path:
                        imports.add(f"import '{component.widget_type.import_path}';")
                    else:
                        package_name = component.widget_type.package.name
                        # Skip carousel_slider package
                        if package_name != 'carousel_slider':
                            imports.add(f"import 'package:{package_name}/{package_name}.dart';")

        # Add project package imports (skip carousel_slider)
        for project_package in self.project.packages.all():
            package_name = project_package.package.name
            if package_name != 'carousel_slider':
                imports.add(f"import 'package:{package_name}/{package_name}.dart';")

        # Use alternative carousel if needed
        if uses_carousel:
            imports.add("import 'package:flutter_carousel_widget/flutter_carousel_widget.dart';")

        return sorted(list(imports))

    def _generate_pages(self, components_by_page):
        """Generate page classes for dynamic components"""
        pages_code = []

        for page_name, components in components_by_page.items():
            page_code = self._generate_page_class(page_name, components)
            pages_code.append(page_code)

        # If no pages defined, create a default HomePage
        if not pages_code:
            pages_code.append(self._generate_default_page())

        return "\n\n".join(pages_code)

    def _generate_page_class(self, page_name, components):
        """Generate a single page class with dynamic widgets"""
        widgets = []

        for component in sorted(components, key=lambda x: x.order):
            widget_code = self._generate_dynamic_widget(component)
            if widget_code:
                widgets.append(widget_code)

        # If no widgets, add a placeholder
        if not widgets:
            widgets.append("Center(child: Text('No widgets configured'))")

        # Generate body based on widget count
        if len(widgets) == 1:
            body_content = widgets[0]
        else:
            body_content = f"""SingleChildScrollView(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.start,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            {chr(10).join(f'            {w},' for w in widgets)}
          ],
        ),
      )"""

        return f"""
class {page_name} extends StatelessWidget {{
  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: Text('{page_name}'),
        elevation: 2,
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: {body_content},
      ),
    );
  }}
}}"""

    def _generate_dynamic_widget(self, component):
        """Generate widget code for dynamic component"""
        try:
            # Replace CarouselSlider with alternative implementation
            if component.widget_type.name == 'CarouselSlider':
                return self._generate_alternative_carousel(component)

            component_data = {
                'type': component.widget_type.name,
                'properties': component.properties or {}
            }

            # Handle children if it's a container
            if component.widget_type.is_container:
                children = list(component.dynamicpagecomponent_set.all())
                if children:
                    component_data['children'] = []
                    for child in children:
                        child_data = {
                            'type': child.widget_type.name,
                            'properties': child.properties or {}
                        }
                        component_data['children'].append(child_data)

            return self.widget_generator.generate_widget(component_data)
        except Exception as e:
            print(f"Error generating dynamic widget: {e}")
            return f"Container() // Error: {str(e)}"

    def _generate_alternative_carousel(self, component):
        """Generate alternative carousel using flutter_carousel_widget"""
        props = component.properties or {}

        # Process items
        items = props.get('items', [])
        items_code = []

        for item in items:
            if isinstance(item, dict):
                if 'type' in item:
                    item_code = self.widget_generator.generate_widget(item)
                else:
                    item_code = "Container(color: Colors.grey)"
                items_code.append(item_code)
            else:
                items_code.append("Container(color: Colors.grey)")

        if not items_code:
            items_code = [
                "Container(color: Colors.blue, child: Center(child: Text('Slide 1', style: TextStyle(color: Colors.white))))",
                "Container(color: Colors.red, child: Center(child: Text('Slide 2', style: TextStyle(color: Colors.white))))",
                "Container(color: Colors.green, child: Center(child: Text('Slide 3', style: TextStyle(color: Colors.white))))"
            ]

        # Process options
        options = props.get('options', {})
        height = options.get('height', 200)
        auto_play = str(options.get('autoPlay', True)).lower()
        auto_play_interval = options.get('autoPlayInterval', 3000)

        # Use FlutterCarousel from flutter_carousel_widget package
        return f"""FlutterCarousel(
  options: CarouselOptions(
    height: {height}.0,
    showIndicator: true,
    slideIndicator: CircularSlideIndicator(),
    autoPlay: {auto_play},
    autoPlayInterval: Duration(milliseconds: {auto_play_interval}),
  ),
  items: [
    {chr(10).join(f'    {item},' for item in items_code)}
  ],
)"""

    def _generate_legacy_pages(self):
        """Generate pages for legacy components"""
        pages_code = []

        # Group components by page
        pages = {}
        for component in self.project.components.all():
            page_name = component.page_name
            if page_name not in pages:
                pages[page_name] = []
            pages[page_name].append(component)

        # Generate each page
        for page_name, components in pages.items():
            page_code = self._generate_legacy_page_class(page_name, components)
            pages_code.append(page_code)

        return "\n\n".join(pages_code)

    def _generate_legacy_page_class(self, page_name, components):
        """Generate page class for legacy components"""
        widgets = []

        for component in components:
            widget_code = self._generate_legacy_widget_code(component)
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

    def _generate_legacy_widget_code(self, component):
        """Generate widget code for legacy component"""
        props = component.properties

        def fix_color_name(color_name):
            """Convert color names to proper Flutter format"""
            color_map = {
                'lightblue': 'lightBlue',
                'lightgreen': 'lightGreen',
                'deeporange': 'deepOrange',
                'deeppurple': 'deepPurple',
                'bluegrey': 'blueGrey',
            }
            color_lower = str(color_name).lower()
            return color_map.get(color_lower, color_lower)

        widget_generators = {
            'text': lambda: f"Text('{props.get('text', 'Default Text')}', style: TextStyle(fontSize: {props.get('fontSize', 16)}.0, color: Colors.{fix_color_name(props.get('color', 'black'))}))",
            'container': lambda: f"Container(width: {props.get('width', 100)}.0, height: {props.get('height', 100)}.0, color: Colors.{fix_color_name(props.get('color', 'blue'))})",
            'button': lambda: f"ElevatedButton(onPressed: () {{}}, child: Text('{props.get('text', 'Click Here')}'))",
            'image': lambda: f"Image.network('{props.get('url', 'https://via.placeholder.com/150')}', width: {props.get('width', 150)}.0, height: {props.get('height', 150)}.0)",
            'listview': lambda: "ListView(shrinkWrap: true, children: [Text('Item 1'), Text('Item 2'), Text('Item 3')])",
            'column': lambda: "Column(children: [Text('Column Item')])",
            'row': lambda: "Row(children: [Text('Row Item')])",
            'scaffold': lambda: "Scaffold(body: Text('Scaffold'))",
            'appbar': lambda: f"AppBar(title: Text('{props.get('title', 'Title')}'))"
        }

        generator = widget_generators.get(component.component_type)
        return generator() if generator else f"Text('Unsupported widget: {component.component_type}')"

    def _generate_default_page(self):
        """Generate a default home page"""
        return """
class HomePage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Home'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.flutter_dash, size: 100, color: Colors.blue),
            SizedBox(height: 20),
            Text(
              'Welcome to Flutter!',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 10),
            Text(
              'Your app is ready to build',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}"""

    def create_project_files(self, project_dir):
        """Create all project files"""
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'lib'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'android'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'ios'), exist_ok=True)

        # Generate pubspec.yaml
        with open(os.path.join(project_dir, 'pubspec.yaml'), 'w', encoding='utf-8') as f:
            f.write(self.generate_pubspec_yaml())

        # Generate main.dart
        with open(os.path.join(project_dir, 'lib', 'main.dart'), 'w', encoding='utf-8') as f:
            f.write(self.generate_main_dart())

        # Create .gitignore
        gitignore_content = """
# Flutter/Dart
.dart_tool/
.packages
.pub/
build/
*.iml
*.ipr
*.iws
.idea/
.DS_Store

# Android
android/.gradle/
android/captures/
android/local.properties

# iOS
ios/Flutter/
ios/Pods/
ios/.symlinks/
ios/Runner.xcworkspace/
ios/Runner.xcodeproj/xcuserdata/
"""
        with open(os.path.join(project_dir, '.gitignore'), 'w') as f:
            f.write(gitignore_content)

        # Create README
        readme_content = f"""# {self.project.name}

{self.project.description or 'A Flutter application built with dynamic widgets.'}

## Getting Started

1. Install dependencies:
   ```bash
   flutter pub get
   ```

2. Run the app:
   ```bash
   flutter run
   ```

## Features

This app was generated using the Dynamic Flutter Code Generator with the following features:
- Dynamic widget system
- Database-driven components
- Auto-discovered packages

## Packages Used

"""
        for package in self.project.packages.all():
            readme_content += f"- {package.package.name} v{package.version}\n"

        # Add dynamic widget info if applicable
        if self.use_dynamic:
            readme_content += "\n## Dynamic Widgets\n\n"
            widget_types = set()
            for component in self.project.dynamic_components.all():
                widget_types.add(component.widget_type.name)
            for widget in sorted(widget_types):
                readme_content += f"- {widget}\n"

        with open(os.path.join(project_dir, 'README.md'), 'w') as f:
            f.write(readme_content)

    def generate_full_project(self):
        """Generate complete project code"""
        return {
            'pubspec.yaml': self.generate_pubspec_yaml(),
            'lib/main.dart': self.generate_main_dart()
        }


# Alias for backward compatibility
DynamicFlutterCodeGenerator = FlutterCodeGenerator