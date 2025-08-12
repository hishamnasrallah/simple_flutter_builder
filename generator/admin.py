# generator/admin.py
# COMPLETE VERSION - Admin classes for ALL models

from django.contrib import admin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponse, FileResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
import os
import zipfile
import tempfile
import subprocess
import threading
import json

from .models import (
    # Core models
    FlutterProject, PubDevPackage, ProjectPackage, PageComponent, APKBuild,
    # Dynamic widget models
    WidgetType, WidgetProperty, WidgetTemplate, PropertyTransformer,
    PackageWidgetRegistry, WidgetPattern, GenerationRule, DynamicPageComponent,
    # Extended models (from models_extended.py if they exist)
)

# Try to import extended models if they exist
try:
    from .models import (
        AppRoute, NavigationItem, AppState, StateAction,
        APIConfiguration, APIEndpoint, DataModel,
        AuthConfiguration, FormConfiguration, FormField,
        CustomFunction, EventHandler, LocalStorage,
        DynamicListConfiguration, ConditionalWidget, AppConfiguration
    )

    EXTENDED_MODELS_AVAILABLE = True
except ImportError:
    EXTENDED_MODELS_AVAILABLE = False

from .utils import FlutterCodeGenerator, PubDevSync
from .package_analyzer import PackageAnalyzer
from .widget_generator import DynamicWidgetGenerator


# ==========================================
# CORE PROJECT ADMIN
# ==========================================

@admin.register(FlutterProject)
class FlutterProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'package_name', 'components_count', 'latest_apk_status', 'created_at', 'action_buttons']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'package_name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'package_name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def components_count(self, obj):
        # Count both legacy and dynamic components
        legacy_count = obj.components.count()
        dynamic_count = obj.dynamic_components.count() if hasattr(obj, 'dynamic_components') else 0

        if dynamic_count > 0:
            return format_html(
                '<span style="color: green;">{} dynamic</span>',
                dynamic_count
            )
        elif legacy_count > 0:
            return format_html(
                '<span style="color: orange;">{} legacy</span>',
                legacy_count
            )
        return "0"

    components_count.short_description = 'Components'

    def latest_apk_status(self, obj):
        latest_build = obj.apk_builds.first()
        if latest_build:
            status_colors = {
                'pending': 'orange',
                'building': 'blue',
                'completed': 'green',
                'failed': 'red'
            }
            color = status_colors.get(latest_build.status, 'gray')
            return format_html(
                '<span style="color: {};">● {}</span>',
                color,
                latest_build.get_status_display()
            )
        return '-'

    latest_apk_status.short_description = 'APK Status'

    def action_buttons(self, obj):
        latest_build = obj.apk_builds.filter(status='completed').first()
        download_btn = ''
        if latest_build and latest_build.download_url:
            download_btn = f'<a class="button" href="{latest_build.download_url}">📱 Download APK</a> '

        return format_html(
            '<a class="button" href="{}">👁️ Preview</a> '
            '<a class="button" href="{}">📦 ZIP</a> '
            '<a class="button" href="{}">🔨 Build APK</a> '
            + download_btn,
            reverse('admin:export_flutter_code', args=[obj.pk]),
            reverse('admin:download_project_zip', args=[obj.pk]),
            reverse('admin:build_apk', args=[obj.pk]),
        )

    action_buttons.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:project_id>/export/', self.admin_site.admin_view(self.export_flutter_code),
                 name='export_flutter_code'),
            path('<int:project_id>/download/', self.admin_site.admin_view(self.download_project_zip),
                 name='download_project_zip'),
            path('<int:project_id>/build/', self.admin_site.admin_view(self.build_apk), name='build_apk'),
            path('<int:project_id>/build-status/', self.admin_site.admin_view(self.build_status), name='build_status'),
        ]
        return custom_urls + urls

    def export_flutter_code(self, request, project_id):
        """Export and preview Flutter code"""
        try:
            project = get_object_or_404(FlutterProject, id=project_id)

            # Use dynamic generator if dynamic components exist
            if hasattr(project, 'dynamic_components') and project.dynamic_components.exists():
                from .utils import DynamicFlutterCodeGenerator
                generator = DynamicFlutterCodeGenerator(project)
            else:
                generator = FlutterCodeGenerator(project)

            code = generator.generate_full_project()

            return render(request, 'admin/flutter_code_preview.html', {
                'project': project,
                'code': code,
                'title': f'Flutter Code Preview - {project.name}'
            })
        except Exception as e:
            messages.error(request, f'Error generating code: {str(e)}')
            return redirect('admin:generator_flutterproject_changelist')

    def download_project_zip(self, request, project_id):
        """Download project as ZIP file"""
        try:
            project = get_object_or_404(FlutterProject, id=project_id)

            # Use appropriate generator
            if hasattr(project, 'dynamic_components') and project.dynamic_components.exists():
                from .utils import DynamicFlutterCodeGenerator
                generator = DynamicFlutterCodeGenerator(project)
            else:
                generator = FlutterCodeGenerator(project)

            temp_dir = tempfile.mkdtemp()
            project_name = project.name.replace(' ', '_').replace('-', '_').lower()
            import re
            project_name = re.sub(r'[^a-zA-Z0-9_]', '', project_name)

            project_dir = os.path.join(temp_dir, project_name)
            generator.create_project_files(project_dir)

            zip_filename = f"{project_name}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arc_path)

            response = FileResponse(
                open(zip_path, 'rb'),
                content_type='application/zip',
                as_attachment=True,
                filename=zip_filename
            )
            return response

        except Exception as e:
            messages.error(request, f'Error creating ZIP: {str(e)}')
            return redirect('admin:generator_flutterproject_changelist')

    def build_apk(self, request, project_id):
        """Start APK build process"""
        try:
            project = get_object_or_404(FlutterProject, id=project_id)

            # Check for active builds
            active_build = project.apk_builds.filter(status__in=['pending', 'building']).first()

            if active_build:
                messages.warning(request, f'APK build already in progress for "{project.name}".')
                return redirect('admin:generator_flutterproject_changelist')

            # Create new build
            apk_build = APKBuild.objects.create(project=project, status='pending')

            # Start build in background
            def build_in_background():
                self._build_apk_async(apk_build)

            thread = threading.Thread(target=build_in_background)
            thread.daemon = True
            thread.start()

            messages.success(
                request,
                format_html(
                    'APK build started for "{}". '
                    '<a href="{}">Track progress</a>',
                    project.name,
                    reverse("admin:build_status", args=[project.id])
                )
            )

            return redirect('admin:generator_flutterproject_changelist')

        except Exception as e:
            messages.error(request, f'Error starting APK build: {str(e)}')
            return redirect('admin:generator_flutterproject_changelist')

    def _build_apk_async(self, apk_build):
        """Build APK in background"""
        from .apk_builder import FlutterAPKBuilder

        try:
            apk_build.status = 'building'
            apk_build.save()

            builder = FlutterAPKBuilder()

            def progress_callback(message, percentage):
                apk_build.build_log += f"[{percentage}%] {message}\n"
                apk_build.save()

            result = builder.build_apk(apk_build.project, progress_callback)

            if result['success']:
                apk_build.status = 'completed'
                apk_build.apk_file_path = result['apk_path']
                apk_build.build_log += f"\n✅ Build completed successfully!\n{result.get('build_output', '')}"

                if os.path.exists(result['apk_path']):
                    apk_build.file_size = os.path.getsize(result['apk_path'])
            else:
                apk_build.status = 'failed'
                apk_build.error_message = result['error']
                apk_build.build_log += f"\n❌ Build failed: {result['error']}"

            apk_build.completed_at = timezone.now()
            apk_build.save()

        except Exception as e:
            apk_build.status = 'failed'
            apk_build.error_message = str(e)
            apk_build.build_log += f"\n💥 Unexpected error: {str(e)}"
            apk_build.completed_at = timezone.now()
            apk_build.save()

    def build_status(self, request, project_id):
        """Show build status page"""
        project = get_object_or_404(FlutterProject, id=project_id)
        builds = project.apk_builds.all()[:10]

        return render(request, 'admin/apk_build_status.html', {
            'project': project,
            'builds': builds,
            'title': f'APK Build Status - {project.name}'
        })


# ==========================================
# PACKAGE MANAGEMENT ADMIN
# ==========================================

@admin.register(PubDevPackage)
class PubDevPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'is_active', 'widgets_count', 'last_updated']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['widgets_count', 'last_updated']

    fieldsets = (
        ('Package Information', {
            'fields': ('name', 'version', 'description')
        }),
        ('Links', {
            'fields': ('homepage', 'documentation')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('widgets_count', 'last_updated'),
            'classes': ('collapse',)
        })
    )

    actions = ['sync_from_pub_dev', 'activate_packages', 'deactivate_packages', 'discover_widgets']

    def widgets_count(self, obj):
        count = WidgetType.objects.filter(package=obj).count()
        if count > 0:
            return format_html(
                '<a href="/admin/generator/widgettype/?package__id={}">{} widgets</a>',
                obj.id, count
            )
        return "0"

    widgets_count.short_description = 'Widgets'

    def last_updated(self, obj):
        registry = PackageWidgetRegistry.objects.filter(package=obj).first()
        if registry and registry.last_analyzed:
            return registry.last_analyzed.strftime("%Y-%m-%d %H:%M")
        return "Not analyzed"

    last_updated.short_description = 'Last Analyzed'

    @admin.action(description="Sync from pub.dev")
    def sync_from_pub_dev(self, request, queryset):
        syncer = PubDevSync()
        updated_count = 0
        for package in queryset:
            try:
                syncer.update_package_info(package)
                updated_count += 1
            except Exception as e:
                messages.warning(request, f'Failed to update {package.name}: {str(e)}')

        messages.success(request, f'Updated {updated_count} packages successfully')

    @admin.action(description="Activate selected packages")
    def activate_packages(self, request, queryset):
        updated = queryset.update(is_active=True)
        messages.success(request, f'Activated {updated} packages')

    @admin.action(description="Deactivate selected packages")
    def deactivate_packages(self, request, queryset):
        updated = queryset.update(is_active=False)
        messages.success(request, f'Deactivated {updated} packages')

    @admin.action(description="Discover widgets from packages")
    def discover_widgets(self, request, queryset):
        analyzer = PackageAnalyzer()
        for package in queryset:
            try:
                analyzer.auto_register_widgets(package.name)
                messages.success(request, f"Discovered widgets for {package.name}")
            except Exception as e:
                messages.error(request, f"Error discovering {package.name}: {str(e)}")


@admin.register(ProjectPackage)
class ProjectPackageAdmin(admin.ModelAdmin):
    list_display = ['project', 'package', 'version', 'package_is_active']
    list_filter = ['project', 'package__is_active']
    search_fields = ['project__name', 'package__name']
    autocomplete_fields = ['project', 'package']

    def package_is_active(self, obj):
        return obj.package.is_active

    package_is_active.boolean = True
    package_is_active.short_description = 'Active'


@admin.register(PageComponent)
class PageComponentAdmin(admin.ModelAdmin):
    list_display = ['project', 'page_name', 'component_type', 'order', 'parent_component']
    list_filter = ['component_type', 'page_name', 'project']
    search_fields = ['project__name', 'page_name']
    list_editable = ['order']
    autocomplete_fields = ['project', 'parent_component']

    fieldsets = (
        ('Location', {
            'fields': ('project', 'page_name', 'parent_component')
        }),
        ('Component', {
            'fields': ('component_type', 'order')
        }),
        ('Properties', {
            'fields': ('properties',),
            'description': 'Enter properties as JSON'
        })
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'properties' in form.base_fields:
            form.base_fields['properties'].help_text = '''
            Enter properties as JSON, example:
            {"text": "Hello", "fontSize": 20, "color": "blue"}
            '''
        return form


@admin.register(APKBuild)
class APKBuildAdmin(admin.ModelAdmin):
    list_display = ['project', 'status', 'created_at', 'completed_at', 'file_size_mb', 'download_link']
    list_filter = ['status', 'created_at', 'completed_at']
    search_fields = ['project__name', 'error_message']
    readonly_fields = ['created_at', 'completed_at', 'file_size', 'apk_file_path', 'apk_filename']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Build Information', {
            'fields': ('project', 'status')
        }),
        ('File Information', {
            'fields': ('apk_file_path', 'apk_filename', 'file_size'),
            'classes': ('collapse',)
        }),
        ('Build Output', {
            'fields': ('build_log', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        })
    )

    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return '-'

    file_size_mb.short_description = 'File Size'

    def download_link(self, obj):
        if obj.download_url:
            return format_html(
                '<a href="{}" class="button">📱 Download</a>',
                obj.download_url
            )
        return '-'

    download_link.short_description = 'Download'


# ==========================================
# DYNAMIC WIDGET SYSTEM ADMIN
# ==========================================

@admin.register(WidgetType)
class WidgetTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'package', 'dart_class_name', 'category', 'is_container', 'is_active', 'properties_count']
    list_filter = ['category', 'is_container', 'is_active', 'package']
    search_fields = ['name', 'dart_class_name', 'package__name', 'documentation']
    readonly_fields = ['created_at', 'updated_at', 'properties_count']
    autocomplete_fields = ['package']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'dart_class_name', 'package', 'category')
        }),
        ('Widget Configuration', {
            'fields': ('is_container', 'can_have_multiple_children', 'is_active')
        }),
        ('Import Settings', {
            'fields': ('import_path', 'min_flutter_version')
        }),
        ('Documentation', {
            'fields': ('documentation', 'example_code'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def properties_count(self, obj):
        count = obj.properties.count()
        return format_html(
            '<a href="/admin/generator/widgetproperty/?widget_type__id={}">{} properties</a>',
            obj.id, count
        )

    properties_count.short_description = 'Properties'

    actions = ['duplicate_widget_type', 'create_default_template', 'export_to_json']

    @admin.action(description="Duplicate selected widget types")
    def duplicate_widget_type(self, request, queryset):
        for widget_type in queryset:
            # Create copy of widget type
            new_widget = WidgetType.objects.create(
                name=f"{widget_type.name}_copy",
                dart_class_name=widget_type.dart_class_name,
                package=widget_type.package,
                category=widget_type.category,
                is_container=widget_type.is_container,
                can_have_multiple_children=widget_type.can_have_multiple_children,
                import_path=widget_type.import_path,
                documentation=widget_type.documentation,
                example_code=widget_type.example_code,
                min_flutter_version=widget_type.min_flutter_version,
                is_active=False  # Set to inactive by default
            )

            # Copy properties
            for prop in widget_type.properties.all():
                WidgetProperty.objects.create(
                    widget_type=new_widget,
                    name=prop.name,
                    property_type=prop.property_type,
                    dart_type=prop.dart_type,
                    is_required=prop.is_required,
                    is_positional=prop.is_positional,
                    position=prop.position,
                    default_value=prop.default_value,
                    allowed_values=prop.allowed_values,
                    validation_rules=prop.validation_rules,
                    documentation=prop.documentation,
                    example_value=prop.example_value
                )

            messages.success(request, f"Duplicated {widget_type.name}")

    @admin.action(description="Create default templates")
    def create_default_template(self, request, queryset):
        for widget_type in queryset:
            if not widget_type.templates.filter(template_name='default').exists():
                WidgetTemplate.objects.create(
                    widget_type=widget_type,
                    template_name='default',
                    template_code=self._generate_default_template(widget_type)
                )
                messages.success(request, f"Created template for {widget_type.name}")

    @admin.action(description="Export to JSON")
    def export_to_json(self, request, queryset):
        data = []
        for widget in queryset:
            widget_data = {
                'name': widget.name,
                'dart_class_name': widget.dart_class_name,
                'category': widget.category,
                'properties': []
            }
            for prop in widget.properties.all():
                widget_data['properties'].append({
                    'name': prop.name,
                    'type': prop.property_type,
                    'dart_type': prop.dart_type,
                    'required': prop.is_required
                })
            data.append(widget_data)

        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="widgets.json"'
        return response

    def _generate_default_template(self, widget_type):
        """Generate default template for a widget type"""
        if widget_type.is_container and widget_type.can_have_multiple_children:
            return """{{ widget_name }}(
{% for prop in properties %}  {{ prop.name }}: {{ prop.value }},
{% endfor %}{% if children %}  children: [
{% for child in children %}    {{ child }},
{% endfor %}  ],
{% endif %})"""
        elif widget_type.is_container:
            return """{{ widget_name }}(
{% for prop in properties %}  {{ prop.name }}: {{ prop.value }},
{% endfor %}{% if children %}  child: {{ children.0 }},
{% endif %})"""
        else:
            return """{{ widget_name }}(
{% for prop in properties %}  {{ prop.name }}: {{ prop.value }},
{% endfor %})"""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('discover-package/', self.admin_site.admin_view(self.discover_package_view),
                 name='discover_package'),
            path('api/analyze-package/', self.analyze_package_api,
                 name='analyze_package_api'),
        ]
        return custom_urls + urls

    def discover_package_view(self, request):
        """View for discovering packages"""
        if request.method == 'POST':
            package_name = request.POST.get('package_name')

            if package_name:
                analyzer = PackageAnalyzer()
                try:
                    success = analyzer.auto_register_widgets(package_name)
                    if success:
                        messages.success(request, f"Successfully discovered widgets from {package_name}")
                    else:
                        messages.error(request, f"Failed to discover widgets from {package_name}")
                except Exception as e:
                    messages.error(request, f"Error: {str(e)}")

                return redirect('/admin/generator/widgettype/')

        return render(request, 'admin/discover_package.html', {
            'title': 'Discover Package Widgets'
        })

    @csrf_exempt
    def analyze_package_api(self, request):
        """API endpoint for analyzing packages"""
        if request.method == 'POST':
            data = json.loads(request.body)
            package_name = data.get('package_name')

            analyzer = PackageAnalyzer()
            analysis = analyzer.analyze_package(package_name)

            if analysis:
                return JsonResponse({
                    'success': True,
                    'data': analysis
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to analyze package'
                })

        return JsonResponse({'error': 'Method not allowed'}, status=405)


@admin.register(WidgetProperty)
class WidgetPropertyAdmin(admin.ModelAdmin):
    list_display = ['widget_type', 'name', 'property_type', 'dart_type', 'is_required', 'is_positional', 'position']
    list_filter = ['property_type', 'is_required', 'is_positional', 'widget_type__category']
    search_fields = ['name', 'widget_type__name', 'dart_type']
    list_editable = ['position', 'is_required', 'is_positional']
    autocomplete_fields = ['widget_type']

    fieldsets = (
        ('Widget Association', {
            'fields': ('widget_type',)
        }),
        ('Property Definition', {
            'fields': ('name', 'property_type', 'dart_type')
        }),
        ('Constraints', {
            'fields': ('is_required', 'is_positional', 'position', 'default_value')
        }),
        ('Validation', {
            'fields': ('allowed_values', 'validation_rules'),
            'classes': ('collapse',)
        }),
        ('Documentation', {
            'fields': ('documentation', 'example_value'),
            'classes': ('collapse',)
        })
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if 'allowed_values' in form.base_fields:
            form.base_fields['allowed_values'].help_text = '''
            For enum types, use: {"values": ["value1", "value2", "value3"]}
            '''

        if 'validation_rules' in form.base_fields:
            form.base_fields['validation_rules'].help_text = '''
            Example: {"min": 0, "max": 100, "pattern": "^[A-Z]"}
            '''

        return form


@admin.register(WidgetTemplate)
class WidgetTemplateAdmin(admin.ModelAdmin):
    list_display = ['widget_type', 'template_name', 'priority', 'is_active']
    list_filter = ['is_active', 'widget_type__category']
    search_fields = ['widget_type__name', 'template_name', 'description']
    list_editable = ['priority', 'is_active']
    autocomplete_fields = ['widget_type']

    fieldsets = (
        ('Template Info', {
            'fields': ('widget_type', 'template_name', 'description')
        }),
        ('Template Configuration', {
            'fields': ('priority', 'is_active', 'conditions')
        }),
        ('Template Code', {
            'fields': ('template_code',),
            'classes': ('wide',)
        })
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if 'template_code' in form.base_fields:
            form.base_fields['template_code'].widget.attrs['rows'] = 15
            form.base_fields['template_code'].widget.attrs['style'] = 'font-family: monospace;'

        if 'conditions' in form.base_fields:
            form.base_fields['conditions'].help_text = '''
            Conditions for using this template. Example:
            {"properties.style": "outlined", "properties.size": ["large", "medium"]}
            '''

        return form


@admin.register(PropertyTransformer)
class PropertyTransformerAdmin(admin.ModelAdmin):
    list_display = ['property_type', 'transformer_name', 'priority', 'is_active']
    list_filter = ['property_type', 'is_active']
    search_fields = ['transformer_name', 'property_type', 'description']
    list_editable = ['priority', 'is_active']

    fieldsets = (
        ('Transformer Info', {
            'fields': ('property_type', 'transformer_name', 'description')
        }),
        ('Configuration', {
            'fields': ('priority', 'is_active')
        }),
        ('Transformer Code', {
            'fields': ('transformer_code',),
            'classes': ('wide',),
            'description': 'Python code for transformation'
        })
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'transformer_code' in form.base_fields:
            form.base_fields['transformer_code'].widget.attrs['rows'] = 10
            form.base_fields['transformer_code'].widget.attrs['style'] = 'font-family: monospace;'
        return form


@admin.register(PackageWidgetRegistry)
class PackageWidgetRegistryAdmin(admin.ModelAdmin):
    list_display = ['package', 'widgets_count', 'auto_discovered', 'last_analyzed']
    list_filter = ['auto_discovered', 'last_analyzed']
    search_fields = ['package__name']
    filter_horizontal = ['widget_types']
    readonly_fields = ['last_analyzed', 'discovery_data_formatted']
    autocomplete_fields = ['package']

    def widgets_count(self, obj):
        return obj.widget_types.count()

    widgets_count.short_description = 'Widgets'

    def discovery_data_formatted(self, obj):
        if obj.discovery_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.discovery_data, indent=2))
        return '-'

    discovery_data_formatted.short_description = 'Discovery Data'

    actions = ['rediscover_widgets']

    @admin.action(description="Rediscover widgets from packages")
    def rediscover_widgets(self, request, queryset):
        analyzer = PackageAnalyzer()
        for registry in queryset:
            try:
                analyzer.auto_register_widgets(registry.package.name)
                messages.success(request, f"Rediscovered widgets for {registry.package.name}")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")


@admin.register(WidgetPattern)
class WidgetPatternAdmin(admin.ModelAdmin):
    list_display = ['name', 'widget_type', 'category']
    list_filter = ['category', 'widget_type__category']
    search_fields = ['name', 'description', 'widget_type__name']
    autocomplete_fields = ['widget_type']

    fieldsets = (
        ('Pattern Info', {
            'fields': ('name', 'widget_type', 'category', 'description')
        }),
        ('Pattern Template', {
            'fields': ('pattern_template',),
            'classes': ('wide',)
        }),
        ('Example', {
            'fields': ('example_properties',),
            'classes': ('collapse',)
        })
    )


@admin.register(GenerationRule)
class GenerationRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'priority', 'is_active']
    list_filter = ['rule_type', 'is_active']
    search_fields = ['name']
    list_editable = ['priority', 'is_active']

    fieldsets = (
        ('Rule Info', {
            'fields': ('name', 'rule_type')
        }),
        ('Configuration', {
            'fields': ('priority', 'is_active')
        }),
        ('Rule Definition', {
            'fields': ('condition', 'action'),
            'description': 'JSON format for conditions and actions'
        })
    )


@admin.register(DynamicPageComponent)
class DynamicPageComponentAdmin(admin.ModelAdmin):
    list_display = ['project', 'page_name', 'widget_type', 'order', 'parent_component', 'preview']
    list_filter = ['page_name', 'widget_type__category', 'project']
    search_fields = ['project__name', 'page_name', 'widget_type__name']
    list_editable = ['order']
    autocomplete_fields = ['project', 'widget_type', 'parent_component']

    fieldsets = (
        ('Component Location', {
            'fields': ('project', 'page_name', 'parent_component')
        }),
        ('Widget Configuration', {
            'fields': ('widget_type', 'order')
        }),
        ('Properties', {
            'fields': ('properties',),
            'classes': ('wide',)
        })
    )

    def preview(self, obj):
        """Show a preview of the generated code"""
        try:
            generator = DynamicWidgetGenerator()

            component_data = {
                'type': obj.widget_type.name,
                'properties': obj.properties
            }

            code = generator.generate_widget(component_data)
            if len(code) > 100:
                code = code[:100] + '...'

            return format_html('<code style="font-family: monospace; font-size: 11px;">{}</code>', code)
        except:
            return '-'

    preview.short_description = 'Code Preview'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if 'properties' in form.base_fields:
            form.base_fields['properties'].widget.attrs['rows'] = 10
            form.base_fields['properties'].help_text = '''
            Enter properties as JSON. Example:
            {
                "text": "Hello World",
                "fontSize": 24,
                "color": "blue",
                "alignment": "center"
            }
            '''

        return form


# ==========================================
# EXTENDED MODELS ADMIN (Navigation, API, etc.)
# ==========================================

if EXTENDED_MODELS_AVAILABLE:

    @admin.register(AppRoute)
    class AppRouteAdmin(admin.ModelAdmin):
        list_display = ['route_name', 'project', 'page_name', 'is_protected', 'is_initial', 'transition_type']
        list_filter = ['is_protected', 'is_initial', 'transition_type', 'project']
        search_fields = ['route_name', 'route_path', 'page_name']
        autocomplete_fields = ['project']

        fieldsets = (
            ('Route Configuration', {
                'fields': ('project', 'route_name', 'route_path', 'page_name')
            }),
            ('Route Properties', {
                'fields': ('is_protected', 'is_initial', 'transition_type')
            })
        )


    @admin.register(NavigationItem)
    class NavigationItemAdmin(admin.ModelAdmin):
        list_display = ['label', 'project', 'route', 'icon', 'order', 'is_active']
        list_filter = ['is_active', 'project']
        search_fields = ['label', 'icon']
        list_editable = ['order', 'is_active']
        autocomplete_fields = ['project', 'route']


    @admin.register(AppState)
    class AppStateAdmin(admin.ModelAdmin):
        list_display = ['variable_name', 'project', 'variable_type', 'is_persistent', 'is_observable']
        list_filter = ['variable_type', 'is_persistent', 'is_observable', 'project']
        search_fields = ['variable_name', 'project__name']
        autocomplete_fields = ['project']

        fieldsets = (
            ('State Variable', {
                'fields': ('project', 'variable_name', 'variable_type')
            }),
            ('Configuration', {
                'fields': ('initial_value', 'is_persistent', 'is_observable')
            })
        )


    @admin.register(StateAction)
    class StateActionAdmin(admin.ModelAdmin):
        list_display = ['action_name', 'state', 'action_type']
        list_filter = ['action_type', 'state__project']
        search_fields = ['action_name', 'state__variable_name']
        autocomplete_fields = ['state']


    @admin.register(APIConfiguration)
    class APIConfigurationAdmin(admin.ModelAdmin):
        list_display = ['project', 'base_url', 'timeout', 'retry_count']
        search_fields = ['project__name', 'base_url']

        fieldsets = (
            ('Project', {
                'fields': ('project',)
            }),
            ('API Settings', {
                'fields': ('base_url', 'timeout', 'retry_count')
            }),
            ('Headers', {
                'fields': ('default_headers',)
            })
        )


    @admin.register(APIEndpoint)
    class APIEndpointAdmin(admin.ModelAdmin):
        list_display = ['endpoint_name', 'project', 'method', 'endpoint_path', 'requires_auth']
        list_filter = ['method', 'requires_auth', 'project']
        search_fields = ['endpoint_name', 'endpoint_path']
        autocomplete_fields = ['project', 'success_state_update']

        fieldsets = (
            ('Endpoint Configuration', {
                'fields': ('project', 'endpoint_name', 'endpoint_path', 'method')
            }),
            ('Request Configuration', {
                'fields': ('headers', 'requires_auth', 'request_body_template', 'query_parameters')
            }),
            ('Response Configuration', {
                'fields': ('response_type', 'success_state_update', 'error_message')
            })
        )


    @admin.register(DataModel)
    class DataModelAdmin(admin.ModelAdmin):
        list_display = ['model_name', 'project', 'fields_count']
        search_fields = ['model_name', 'project__name']
        autocomplete_fields = ['project']

        def fields_count(self, obj):
            if obj.fields:
                return len(obj.fields)
            return 0

        fields_count.short_description = 'Fields'


    @admin.register(AuthConfiguration)
    class AuthConfigurationAdmin(admin.ModelAdmin):
        list_display = ['project', 'auth_type', 'token_storage_key']
        list_filter = ['auth_type']
        search_fields = ['project__name']
        autocomplete_fields = ['project', 'login_endpoint', 'register_endpoint', 'logout_endpoint', 'refresh_endpoint',
                               'user_model']


    @admin.register(FormConfiguration)
    class FormConfigurationAdmin(admin.ModelAdmin):
        list_display = ['form_name', 'project', 'page_name', 'fields_count', 'submit_endpoint']
        list_filter = ['project', 'page_name']
        search_fields = ['form_name', 'page_name']
        autocomplete_fields = ['project', 'submit_endpoint', 'success_route']

        def fields_count(self, obj):
            return obj.fields.count()

        fields_count.short_description = 'Fields'

        class FormFieldInline(admin.TabularInline):
            model = FormField
            extra = 1
            fields = ['field_name', 'field_type', 'label', 'is_required', 'order']
            ordering = ['order']

        inlines = [FormFieldInline]


    @admin.register(FormField)
    class FormFieldAdmin(admin.ModelAdmin):
        list_display = ['field_name', 'form', 'field_type', 'label', 'is_required', 'order']
        list_filter = ['field_type', 'is_required', 'form__project']
        search_fields = ['field_name', 'label', 'form__form_name']
        list_editable = ['order', 'is_required']
        autocomplete_fields = ['form', 'bind_to_state']


    @admin.register(CustomFunction)
    class CustomFunctionAdmin(admin.ModelAdmin):
        list_display = ['function_name', 'project', 'return_type', 'is_async']
        list_filter = ['is_async', 'return_type', 'project']
        search_fields = ['function_name', 'function_body']
        autocomplete_fields = ['project']

        fieldsets = (
            ('Function Definition', {
                'fields': ('project', 'function_name', 'return_type', 'is_async')
            }),
            ('Parameters', {
                'fields': ('parameters',),
                'description': 'List of {"name": "param", "type": "String"}'
            }),
            ('Function Body', {
                'fields': ('function_body',),
                'classes': ('wide',)
            })
        )

        def get_form(self, request, obj=None, **kwargs):
            form = super().get_form(request, obj, **kwargs)
            if 'function_body' in form.base_fields:
                form.base_fields['function_body'].widget.attrs['rows'] = 15
                form.base_fields['function_body'].widget.attrs['style'] = 'font-family: monospace;'
            return form


    @admin.register(EventHandler)
    class EventHandlerAdmin(admin.ModelAdmin):
        list_display = ['component', 'event_type', 'action_type', 'get_target']
        list_filter = ['event_type', 'action_type', 'component__project']
        search_fields = ['component__page_name']
        autocomplete_fields = ['component', 'target_route', 'target_api', 'target_state', 'target_function']

        def get_target(self, obj):
            if obj.target_route:
                return f"Route: {obj.target_route.route_name}"
            elif obj.target_api:
                return f"API: {obj.target_api.endpoint_name}"
            elif obj.target_state:
                return f"State: {obj.target_state.variable_name}"
            elif obj.target_function:
                return f"Function: {obj.target_function.function_name}"
            return "-"

        get_target.short_description = 'Target'


    @admin.register(LocalStorage)
    class LocalStorageAdmin(admin.ModelAdmin):
        list_display = ['key_name', 'project', 'data_type', 'default_value']
        list_filter = ['data_type', 'project']
        search_fields = ['key_name', 'description']
        autocomplete_fields = ['project']


    @admin.register(DynamicListConfiguration)
    class DynamicListConfigurationAdmin(admin.ModelAdmin):
        list_display = ['component', 'data_source', 'item_widget_type', 'enable_pull_refresh', 'enable_pagination']
        list_filter = ['data_source', 'enable_pull_refresh', 'enable_pagination']
        autocomplete_fields = ['component', 'api_endpoint', 'state_variable', 'item_widget_type']

        fieldsets = (
            ('List Configuration', {
                'fields': ('component', 'data_source')
            }),
            ('Data Source', {
                'fields': ('api_endpoint', 'state_variable', 'static_data')
            }),
            ('Item Template', {
                'fields': ('item_widget_type', 'item_properties_mapping')
            }),
            ('UI States', {
                'fields': ('loading_widget', 'empty_widget', 'error_widget'),
                'classes': ('collapse',)
            }),
            ('Features', {
                'fields': ('enable_pull_refresh', 'enable_pagination', 'items_per_page')
            })
        )


    @admin.register(ConditionalWidget)
    class ConditionalWidgetAdmin(admin.ModelAdmin):
        list_display = ['component', 'condition_type', 'state_variable', 'condition_value']
        list_filter = ['condition_type', 'component__project']
        autocomplete_fields = ['component', 'state_variable']


    @admin.register(AppConfiguration)
    class AppConfigurationAdmin(admin.ModelAdmin):
        list_display = ['project', 'app_type', 'state_management', 'navigation_type', 'get_features']
        list_filter = ['app_type', 'state_management', 'navigation_type']
        search_fields = ['project__name']

        fieldsets = (
            ('Project', {
                'fields': ('project',)
            }),
            ('App Configuration', {
                'fields': ('app_type', 'state_management', 'navigation_type')
            }),
            ('Theme', {
                'fields': ('primary_color', 'secondary_color', 'dark_mode_enabled', 'font_family')
            }),
            ('Features', {
                'fields': (
                    'uses_authentication', 'uses_api', 'uses_local_storage',
                    'uses_push_notifications', 'uses_maps', 'uses_camera',
                    'uses_payments', 'uses_social_login', 'uses_analytics', 'uses_ads'
                )
            }),
            ('Localization', {
                'fields': ('supported_languages', 'default_language'),
                'classes': ('collapse',)
            })
        )

        def get_features(self, obj):
            features = []
            if obj.uses_authentication: features.append('🔐')
            if obj.uses_api: features.append('🌐')
            if obj.uses_local_storage: features.append('💾')
            if obj.uses_maps: features.append('🗺️')
            if obj.uses_camera: features.append('📷')
            if obj.uses_payments: features.append('💳')
            return ' '.join(features) if features else '-'

        get_features.short_description = 'Features'

# ==========================================
# CUSTOM ADMIN SITE CONFIGURATION
# ==========================================

# Customize admin site headers
admin.site.site_header = "Flutter Code Generator Admin"
admin.site.site_title = "Flutter Generator"
admin.site.index_title = "Dynamic Flutter Code Generator Dashboard"

# Add custom CSS
admin.site.enable_nav_sidebar = True