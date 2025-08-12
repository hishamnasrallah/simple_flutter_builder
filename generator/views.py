# generator/views.py
# CONSOLIDATED VERSION - Combines views.py and api_views.py

import os
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, Http404, FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count

from .models import (
    APKBuild, FlutterProject, PubDevPackage,
    WidgetType, WidgetProperty, WidgetTemplate,
    DynamicPageComponent, PackageWidgetRegistry
)
from .utils import PubDevSync
from .widget_generator import DynamicWidgetGenerator
from .package_analyzer import PackageAnalyzer


# ==========================================
# REGULAR VIEWS (Original views.py)
# ==========================================

@require_http_methods(["GET"])
def search_pub_packages(request):
    """Search pub.dev packages"""
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({
            'success': False,
            'error': 'Search parameter required',
            'packages': []
        }, status=400)

    if len(query) < 2:
        return JsonResponse({
            'success': False,
            'error': 'Search must be at least 2 characters',
            'packages': []
        }, status=400)

    try:
        syncer = PubDevSync()
        results = syncer.search_packages(query)

        if results and 'packages' in results:
            packages = []
            for package in results['packages'][:20]:  # Limit to 20 results
                packages.append({
                    'name': package.get('package', ''),
                    'description': package.get('description', 'No description')[:200],
                    'version': package.get('latest', {}).get('version', ''),
                    'popularity': package.get('score', {}).get('popularityScore', 0),
                })

            return JsonResponse({
                'success': True,
                'packages': packages,
                'count': len(packages)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No results found',
                'packages': []
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Search error: {str(e)}',
            'packages': []
        }, status=500)


@require_http_methods(["GET"])
def get_package_info(request, package_name):
    """Get specific package information"""
    try:
        syncer = PubDevSync()
        info = syncer.get_package_info(package_name)

        if info:
            return JsonResponse({
                'success': True,
                'package': {
                    'name': info.get('name', package_name),
                    'description': info.get('description', ''),
                    'version': info.get('latest', {}).get('version', ''),
                    'homepage': info.get('latest', {}).get('pubspec', {}).get('homepage', ''),
                    'documentation': info.get('latest', {}).get('pubspec', {}).get('documentation', ''),
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Package not found'
            }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error fetching package info: {str(e)}'
        }, status=500)


@staff_member_required
def download_apk(request, build_id):
    """Download APK file"""
    build = get_object_or_404(APKBuild, id=build_id)

    if not build.apk_file_path or not os.path.exists(build.apk_file_path):
        raise Http404("APK file not found")

    response = FileResponse(
        open(build.apk_file_path, 'rb'),
        content_type='application/vnd.android.package-archive',
        as_attachment=True,
        filename=build.apk_filename
    )
    return response


# ==========================================
# API VIEWS (Original api_views.py)
# ==========================================

@require_http_methods(["GET"])
def list_widget_types(request):
    """List all available widget types"""
    category = request.GET.get('category')
    package = request.GET.get('package')
    search = request.GET.get('search')

    widgets = WidgetType.objects.filter(is_active=True)

    if category:
        widgets = widgets.filter(category=category)

    if package:
        widgets = widgets.filter(package__name=package)

    if search:
        widgets = widgets.filter(name__icontains=search)

    widget_list = []
    for widget in widgets:
        widget_data = {
            'id': widget.id,
            'name': widget.name,
            'dart_class': widget.dart_class_name,
            'category': widget.category,
            'is_container': widget.is_container,
            'package': widget.package.name if widget.package else None,
            'properties': []
        }

        # Include properties
        for prop in widget.properties.all():
            widget_data['properties'].append({
                'name': prop.name,
                'type': prop.property_type,
                'dart_type': prop.dart_type,
                'required': prop.is_required,
                'default': prop.default_value
            })

        widget_list.append(widget_data)

    return JsonResponse({
        'success': True,
        'widgets': widget_list,
        'count': len(widget_list)
    })


@require_http_methods(["GET"])
def get_widget_detail(request, widget_id):
    """Get detailed information about a widget type"""
    widget = get_object_or_404(WidgetType, id=widget_id)

    # Get all properties
    properties = []
    for prop in widget.properties.all():
        properties.append({
            'name': prop.name,
            'type': prop.property_type,
            'dart_type': prop.dart_type,
            'required': prop.is_required,
            'positional': prop.is_positional,
            'position': prop.position,
            'default': prop.default_value,
            'allowed_values': prop.allowed_values,
            'documentation': prop.documentation,
            'example': prop.example_value
        })

    # Get templates
    templates = []
    for template in widget.templates.filter(is_active=True):
        templates.append({
            'name': template.template_name,
            'priority': template.priority,
            'conditions': template.conditions,
            'code': template.template_code
        })

    return JsonResponse({
        'success': True,
        'widget': {
            'id': widget.id,
            'name': widget.name,
            'dart_class': widget.dart_class_name,
            'category': widget.category,
            'is_container': widget.is_container,
            'can_have_multiple_children': widget.can_have_multiple_children,
            'package': widget.package.name if widget.package else None,
            'import_path': widget.import_path,
            'documentation': widget.documentation,
            'example_code': widget.example_code,
            'properties': properties,
            'templates': templates
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def generate_widget_code(request):
    """Generate Flutter code for a widget configuration"""
    try:
        data = json.loads(request.body)
        generator = DynamicWidgetGenerator()

        # Validate component
        validation = generator.validate_component(data)
        if not validation['valid']:
            return JsonResponse({
                'success': False,
                'errors': validation['errors'],
                'warnings': validation['warnings']
            }, status=400)

        # Generate code
        code = generator.generate_widget(data)

        return JsonResponse({
            'success': True,
            'code': code,
            'warnings': validation.get('warnings', [])
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def preview_component(request):
    """Preview a component with live code generation"""
    try:
        data = json.loads(request.body)
        generator = DynamicWidgetGenerator()

        # Generate widget code
        widget_code = generator.generate_widget(data)

        # Generate complete preview code
        preview_code = f"""
import 'package:flutter/material.dart';

void main() => runApp(PreviewApp());

class PreviewApp extends StatelessWidget {{
  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: Text('Widget Preview')),
        body: Center(
          child: {widget_code},
        ),
      ),
    );
  }}
}}"""

        return JsonResponse({
            'success': True,
            'widget_code': widget_code,
            'preview_code': preview_code
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def list_packages(request):
    """List all registered packages with widget counts"""
    packages = PubDevPackage.objects.filter(is_active=True)

    package_list = []
    for package in packages:
        widget_count = WidgetType.objects.filter(package=package, is_active=True).count()
        package_list.append({
            'id': package.id,
            'name': package.name,
            'version': package.version,
            'description': package.description,
            'widget_count': widget_count
        })

    return JsonResponse({
        'success': True,
        'packages': package_list,
        'count': len(package_list)
    })


@csrf_exempt
@require_http_methods(["POST"])
def discover_package_api(request):
    """Discover widgets from a pub.dev package"""
    try:
        data = json.loads(request.body)
        package_name = data.get('package_name')

        if not package_name:
            return JsonResponse({
                'success': False,
                'error': 'Package name is required'
            }, status=400)

        analyzer = PackageAnalyzer()

        # First analyze without saving
        analysis = analyzer.analyze_package(package_name)

        if not analysis:
            return JsonResponse({
                'success': False,
                'error': f'Failed to analyze package {package_name}'
            }, status=404)

        # If not dry run, save to database
        if not data.get('dry_run', False):
            success = analyzer.auto_register_widgets(package_name)

            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully registered widgets from {package_name}',
                    'data': analysis
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to register widgets',
                    'data': analysis
                }, status=500)
        else:
            return JsonResponse({
                'success': True,
                'dry_run': True,
                'data': analysis
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_project_widgets(request, project_id):
    """Get all widgets used in a project"""
    project = get_object_or_404(FlutterProject, id=project_id)

    # Get dynamic components
    components = []
    for component in project.dynamic_components.all().order_by('page_name', 'order'):
        components.append({
            'id': component.id,
            'page': component.page_name,
            'widget': component.widget_type.name,
            'properties': component.properties,
            'order': component.order
        })

    # Get unique widget types used
    widget_types = set()
    for component in project.dynamic_components.all():
        widget_types.add(component.widget_type)

    widgets_used = [
        {
            'name': widget.name,
            'category': widget.category,
            'package': widget.package.name if widget.package else None
        }
        for widget in widget_types
    ]

    return JsonResponse({
        'success': True,
        'project': {
            'id': project.id,
            'name': project.name,
            'package_name': project.package_name
        },
        'components': components,
        'widgets_used': widgets_used,
        'component_count': len(components),
        'widget_count': len(widgets_used)
    })


@csrf_exempt
@require_http_methods(["POST"])
def create_component(request):
    """Create a new dynamic component"""
    try:
        data = json.loads(request.body)

        # Validate required fields
        required = ['project_id', 'widget_type_id', 'page_name']
        for field in required:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'{field} is required'
                }, status=400)

        project = get_object_or_404(FlutterProject, id=data['project_id'])
        widget_type = get_object_or_404(WidgetType, id=data['widget_type_id'])

        # Create component
        component = DynamicPageComponent.objects.create(
            project=project,
            widget_type=widget_type,
            page_name=data['page_name'],
            properties=data.get('properties', {}),
            order=data.get('order', 0)
        )

        # Generate code for preview
        generator = DynamicWidgetGenerator()
        code = generator.generate_widget({
            'type': widget_type.name,
            'properties': component.properties
        })

        return JsonResponse({
            'success': True,
            'component': {
                'id': component.id,
                'widget': widget_type.name,
                'page': component.page_name,
                'properties': component.properties,
                'code': code
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_component(request, component_id):
    """Update a dynamic component"""
    try:
        component = get_object_or_404(DynamicPageComponent, id=component_id)
        data = json.loads(request.body)

        # Update fields
        if 'properties' in data:
            component.properties = data['properties']
        if 'order' in data:
            component.order = data['order']
        if 'page_name' in data:
            component.page_name = data['page_name']

        component.save()

        # Generate updated code
        generator = DynamicWidgetGenerator()
        code = generator.generate_widget({
            'type': component.widget_type.name,
            'properties': component.properties
        })

        return JsonResponse({
            'success': True,
            'component': {
                'id': component.id,
                'widget': component.widget_type.name,
                'page': component.page_name,
                'properties': component.properties,
                'code': code
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["DELETE"])
def delete_component(request, component_id):
    """Delete a dynamic component"""
    component = get_object_or_404(DynamicPageComponent, id=component_id)
    component.delete()

    return JsonResponse({
        'success': True,
        'message': 'Component deleted successfully'
    })


@require_http_methods(["GET"])
def widget_categories(request):
    """Get all widget categories with counts"""
    categories = WidgetType.objects.filter(is_active=True).values('category').annotate(
        count=Count('id')
    ).order_by('category')

    return JsonResponse({
        'success': True,
        'categories': list(categories)
    })


@require_http_methods(["GET"])
def property_types(request):
    """Get all available property types"""
    property_types = [
        {
            'value': choice[0],
            'label': choice[1],
            'description': f"Property of type {choice[1]}"
        }
        for choice in WidgetProperty.PROPERTY_TYPES
    ]

    return JsonResponse({
        'success': True,
        'property_types': property_types
    })