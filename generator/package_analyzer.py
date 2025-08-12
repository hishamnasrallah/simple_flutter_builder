# generator/package_analyzer.py

import requests
import re
import json
import yaml
import logging
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PackageAnalyzer:
    """Analyzes pub.dev packages to extract widget information"""

    def __init__(self):
        self.pub_api_base = "https://pub.dev/api"
        self.pub_base = "https://pub.dev"
        self.github_api = "https://api.github.com"

        # Common widget patterns in popular packages
        self.known_patterns = self._load_known_patterns()

    def _load_known_patterns(self) -> Dict[str, List[Dict]]:
        """Load known widget patterns for popular packages"""
        return {
            'carousel_slider': [
                {
                    'name': 'CarouselSlider',
                    'properties': [
                        {'name': 'items', 'type': 'List<Widget>', 'required': True},
                        {'name': 'options', 'type': 'CarouselOptions', 'required': False},
                        {'name': 'carouselController', 'type': 'CarouselController', 'required': False},
                    ]
                },
                {
                    'name': 'CarouselOptions',
                    'properties': [
                        {'name': 'height', 'type': 'double', 'required': False},
                        {'name': 'aspectRatio', 'type': 'double', 'required': False},
                        {'name': 'viewportFraction', 'type': 'double', 'required': False},
                        {'name': 'initialPage', 'type': 'int', 'required': False},
                        {'name': 'enableInfiniteScroll', 'type': 'bool', 'required': False},
                        {'name': 'autoPlay', 'type': 'bool', 'required': False},
                        {'name': 'autoPlayInterval', 'type': 'Duration', 'required': False},
                        {'name': 'autoPlayAnimationDuration', 'type': 'Duration', 'required': False},
                    ]
                }
            ],
            'video_player': [
                {
                    'name': 'VideoPlayer',
                    'properties': [
                        {'name': 'controller', 'type': 'VideoPlayerController', 'required': True},
                    ]
                },
                {
                    'name': 'VideoPlayerController',
                    'properties': [
                        {'name': 'dataSource', 'type': 'String', 'required': True},
                        {'name': 'videoPlayerOptions', 'type': 'VideoPlayerOptions', 'required': False},
                    ]
                }
            ],
            'image_picker': [
                {
                    'name': 'ImagePicker',
                    'properties': []
                }
            ],
            'google_maps_flutter': [
                {
                    'name': 'GoogleMap',
                    'properties': [
                        {'name': 'initialCameraPosition', 'type': 'CameraPosition', 'required': True},
                        {'name': 'mapType', 'type': 'MapType', 'required': False},
                        {'name': 'markers', 'type': 'Set<Marker>', 'required': False},
                        {'name': 'circles', 'type': 'Set<Circle>', 'required': False},
                        {'name': 'polygons', 'type': 'Set<Polygon>', 'required': False},
                        {'name': 'onMapCreated', 'type': 'Function', 'required': False},
                    ]
                }
            ],
            'cached_network_image': [
                {
                    'name': 'CachedNetworkImage',
                    'properties': [
                        {'name': 'imageUrl', 'type': 'String', 'required': True},
                        {'name': 'placeholder', 'type': 'Widget', 'required': False},
                        {'name': 'errorWidget', 'type': 'Widget', 'required': False},
                        {'name': 'width', 'type': 'double', 'required': False},
                        {'name': 'height', 'type': 'double', 'required': False},
                        {'name': 'fit', 'type': 'BoxFit', 'required': False},
                    ]
                }
            ],
        }

    def analyze_package(self, package_name: str) -> Dict[str, Any]:
        """Analyze a package and extract widget definitions"""

        logger.info(f"Analyzing package: {package_name}")

        # First check if we have known patterns
        if package_name in self.known_patterns:
            logger.info(f"Using known patterns for {package_name}")
            return self._process_known_patterns(package_name)

        # Fetch package info from pub.dev
        package_info = self._fetch_package_info(package_name)
        if not package_info:
            return None

        # Try multiple strategies to extract widget information
        widgets = []

        # Strategy 1: Extract from example code
        example_widgets = self._extract_widgets_from_examples(package_info)
        widgets.extend(example_widgets)

        # Strategy 2: Parse documentation
        doc_widgets = self._extract_widgets_from_documentation(package_name, package_info)
        widgets.extend(doc_widgets)

        # Strategy 3: Analyze GitHub repository if available
        github_widgets = self._extract_widgets_from_github(package_info)
        widgets.extend(github_widgets)

        # Deduplicate and process
        processed_widgets = self._process_widgets(widgets, package_name)

        return {
            'package_name': package_name,
            'version': package_info.get('latest', {}).get('version'),
            'description': package_info.get('latest', {}).get('pubspec', {}).get('description', ''),
            'widgets': processed_widgets,
            'imports': self._generate_imports(package_name, processed_widgets)
        }

    def _fetch_package_info(self, package_name: str) -> Optional[Dict]:
        """Fetch package information from pub.dev API"""

        try:
            response = requests.get(f"{self.pub_api_base}/packages/{package_name}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch package info: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching package info: {e}")

        return None

    def _extract_widgets_from_examples(self, package_info: Dict) -> List[Dict]:
        """Extract widget definitions from example code"""

        widgets = []

        # Get example from package info
        example = package_info.get('latest', {}).get('example', '')
        if not example:
            return widgets

        # Pattern to find class definitions that extend Widget classes
        widget_pattern = r'class\s+(\w+)\s+extends\s+(StatelessWidget|StatefulWidget|Widget)'
        matches = re.findall(widget_pattern, example)

        for widget_name, widget_type in matches:
            widgets.append({
                'name': widget_name,
                'base_class': widget_type,
                'properties': self._extract_constructor_params(example, widget_name)
            })

        # Also look for widget instantiations
        instantiation_pattern = r'(\w+)\s*\([^)]*\)'
        used_widgets = re.findall(instantiation_pattern, example)

        # Filter out Flutter built-in widgets
        flutter_builtins = {
            'Container', 'Text', 'Column', 'Row', 'Stack', 'Scaffold',
            'AppBar', 'Center', 'Padding', 'SizedBox', 'Expanded',
            'ListView', 'GridView', 'Image', 'Icon', 'Card'
        }

        for widget in used_widgets:
            if widget not in flutter_builtins and not any(w['name'] == widget for w in widgets):
                widgets.append({
                    'name': widget,
                    'base_class': 'Widget',
                    'properties': []
                })

        return widgets

    def _extract_constructor_params(self, code: str, class_name: str) -> List[Dict]:
        """Extract constructor parameters from code"""

        properties = []

        # Find constructor
        constructor_pattern = rf'{class_name}\s*\({{([^}}]*)}}\)'
        match = re.search(constructor_pattern, code)

        if match:
            params = match.group(1)

            # Parse parameters
            param_pattern = r'(?:(required)\s+)?(?:this\.)?(\w+)(?:\s*=\s*([^,}]+))?'
            param_matches = re.findall(param_pattern, params)

            for required, param_name, default_value in param_matches:
                properties.append({
                    'name': param_name,
                    'type': 'dynamic',  # Type inference would require more parsing
                    'required': bool(required),
                    'default': default_value.strip() if default_value else None
                })

        return properties

    def _extract_widgets_from_documentation(self, package_name: str, package_info: Dict) -> List[Dict]:
        """Extract widget info from package documentation"""

        widgets = []

        # Try to fetch documentation page
        try:
            doc_url = f"{self.pub_base}/documentation/{package_name}/latest/"
            response = requests.get(doc_url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for class definitions in documentation
                class_elements = soup.find_all('div', class_='class')

                for element in class_elements:
                    class_name = element.find('h1', class_='title')
                    if class_name:
                        widget_name = class_name.text.strip()

                        # Check if it's likely a widget
                        if 'Widget' in widget_name or any(
                                keyword in element.text
                                for keyword in ['extends StatelessWidget', 'extends StatefulWidget', 'Widget build']
                        ):
                            widgets.append({
                                'name': widget_name,
                                'base_class': 'Widget',
                                'properties': []
                            })
        except Exception as e:
            logger.warning(f"Could not fetch documentation: {e}")

        return widgets

    def _extract_widgets_from_github(self, package_info: Dict) -> List[Dict]:
        """Extract widget info from GitHub repository"""

        widgets = []

        # Get repository URL
        homepage = package_info.get('latest', {}).get('pubspec', {}).get('homepage', '')
        repository = package_info.get('latest', {}).get('pubspec', {}).get('repository', '')

        github_url = repository or homepage
        if 'github.com' not in github_url:
            return widgets

        # Extract owner and repo name
        match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
        if not match:
            return widgets

        owner, repo = match.groups()
        repo = repo.replace('.git', '')

        try:
            # Fetch lib directory contents
            api_url = f"{self.github_api}/repos/{owner}/{repo}/contents/lib"
            response = requests.get(api_url, timeout=10)

            if response.status_code == 200:
                files = response.json()

                # Look for main library file
                for file in files:
                    if file['name'].endswith('.dart'):
                        # Could fetch and parse file content here
                        # For now, just note that the file exists
                        pass
        except Exception as e:
            logger.warning(f"Could not fetch GitHub data: {e}")

        return widgets

    def _process_known_patterns(self, package_name: str) -> Dict[str, Any]:
        """Process known widget patterns for a package"""

        patterns = self.known_patterns[package_name]

        widgets = []
        for pattern in patterns:
            widget = {
                'name': pattern['name'],
                'package': package_name,
                'import_path': f"package:{package_name}/{package_name}.dart",
                'properties': pattern.get('properties', [])
            }
            widgets.append(widget)

        return {
            'package_name': package_name,
            'version': 'latest',
            'widgets': widgets,
            'imports': [f"import 'package:{package_name}/{package_name}.dart';"]
        }

    def _process_widgets(self, widgets: List[Dict], package_name: str) -> List[Dict]:
        """Process and deduplicate widgets"""

        seen = set()
        processed = []

        for widget in widgets:
            if widget['name'] not in seen:
                seen.add(widget['name'])

                # Add package context
                widget['package'] = package_name
                widget['import_path'] = widget.get('import_path',
                                                   f"package:{package_name}/{package_name}.dart")

                # Ensure properties have proper types
                for prop in widget.get('properties', []):
                    prop['type'] = self._map_dart_type(prop.get('type', 'dynamic'))

                processed.append(widget)

        return processed

    def _map_dart_type(self, dart_type: str) -> str:
        """Map Dart type to our property type system"""

        type_mapping = {
            'String': 'string',
            'int': 'int',
            'double': 'double',
            'bool': 'bool',
            'Color': 'color',
            'Widget': 'widget',
            'List<Widget>': 'widget_list',
            'EdgeInsets': 'edge_insets',
            'EdgeInsetsGeometry': 'edge_insets',
            'Duration': 'duration',
            'TextStyle': 'text_style',
            'Alignment': 'alignment',
            'AlignmentGeometry': 'alignment',
            'BoxFit': 'enum',
            'MapType': 'enum',
            'dynamic': 'custom',
        }

        # Check for exact match
        if dart_type in type_mapping:
            return type_mapping[dart_type]

        # Check for patterns
        if 'List<' in dart_type:
            return 'list'
        elif 'Set<' in dart_type:
            return 'list'
        elif 'Map<' in dart_type:
            return 'map'
        elif dart_type.startswith('Function'):
            return 'custom'

        return 'custom'

    def _generate_imports(self, package_name: str, widgets: List[Dict]) -> List[str]:
        """Generate import statements needed"""

        imports = set()

        # Main package import
        imports.add(f"import 'package:{package_name}/{package_name}.dart';")

        # Check if specific imports are needed
        for widget in widgets:
            if 'import_path' in widget and widget['import_path'] not in imports:
                imports.add(f"import '{widget['import_path']}';")

        return sorted(list(imports))

    def auto_register_widgets(self, package_name: str) -> bool:
        """Automatically register widgets in database"""

        from .models import PubDevPackage, WidgetType, WidgetProperty, WidgetTemplate

        analysis = self.analyze_package(package_name)
        if not analysis:
            logger.error(f"Failed to analyze package {package_name}")
            return False

        # Get or create package
        package, _ = PubDevPackage.objects.get_or_create(
            name=package_name,
            defaults={
                'version': analysis['version'],
                'description': analysis.get('description', f"Package {package_name}")
            }
        )

        # Register each widget
        for widget_data in analysis['widgets']:
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
                logger.info(f"Created widget type: {widget_data['name']}")

                # Add properties
                for prop_data in widget_data.get('properties', []):
                    WidgetProperty.objects.create(
                        widget_type=widget_type,
                        name=prop_data['name'],
                        property_type=prop_data.get('type', 'custom'),
                        dart_type=prop_data.get('dart_type', 'dynamic'),
                        is_required=prop_data.get('required', False),
                        default_value=json.dumps(prop_data.get('default')) if prop_data.get('default') else ''
                    )

                # Create default template
                WidgetTemplate.objects.create(
                    widget_type=widget_type,
                    template_name='default',
                    template_code=self._generate_default_template(widget_data)
                )

        return True

    def _guess_category(self, widget_name: str) -> str:
        """Guess widget category from name"""

        name_lower = widget_name.lower()

        if any(x in name_lower for x in ['button', 'input', 'field', 'form', 'picker']):
            return 'input'
        elif any(x in name_lower for x in ['image', 'video', 'audio', 'player', 'photo']):
            return 'media'
        elif any(x in name_lower for x in ['list', 'grid', 'column', 'row', 'stack', 'layout']):
            return 'layout'
        elif any(x in name_lower for x in ['navigation', 'route', 'page', 'tab', 'drawer']):
            return 'navigation'
        elif any(x in name_lower for x in ['container', 'box', 'card', 'panel']):
            return 'container'
        elif any(x in name_lower for x in ['animation', 'animated', 'transition']):
            return 'animation'
        else:
            return 'display'

    def _is_container(self, widget_data: Dict) -> bool:
        """Check if widget is a container"""

        # Check for children-related properties
        for prop in widget_data.get('properties', []):
            if prop['name'] in ['child', 'children', 'body', 'content']:
                return True

        # Check name patterns
        name_lower = widget_data['name'].lower()
        container_patterns = ['container', 'box', 'panel', 'scaffold', 'layout']

        return any(pattern in name_lower for pattern in container_patterns)

    def _generate_default_template(self, widget_data: Dict) -> str:
        """Generate a default template for the widget"""

        template_lines = [f"{widget_data['name']}("]

        for prop in widget_data.get('properties', []):
            if prop.get('required'):
                template_lines.append(f"  {prop['name']}: {{{{{prop['name']}}}}},")
            else:
                template_lines.append(f"  {{%if {prop['name']}%}}{prop['name']}: {{{{{prop['name']}}}}},{{%endif%}}")

        template_lines.append(")")

        return '\n'.join(template_lines)