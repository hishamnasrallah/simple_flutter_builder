# generator/admin.py
# CONSOLIDATED VERSION - Merges admin.py and admin_dynamic.py

from django.contrib import admin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponse, FileResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import os
import zipfile
import tempfile
import subprocess
import threading
import json

from .models import (
    # Original models
    FlutterProject, PubDevPackage, ProjectPackage, PageComponent, APKBuild,
    # Dynamic models
    WidgetType, WidgetProperty, WidgetTemplate, PropertyTransformer,
    PackageWidgetRegistry, WidgetPattern, GenerationRule, DynamicPageComponent
)
from .utils import FlutterCodeGenerator, PubDevSync
from .package_analyzer import PackageAnalyzer


# ==========================================
# ORIGINAL PROJECT ADMIN CLASSES
# ==========================================

@admin.register(FlutterProject)
class FlutterProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'package_name', 'components_count', 'latest_apk_status', 'created_at', 'action_buttons']
    list_filter = ['created_at']
    search_fields = ['name', 'package_name']

    def components_count(self, obj):
        # Count both legacy and dynamic components
        legacy_count = obj.components.count()
        dynamic_count = obj.dynamic_components.count()

        if dynamic_count > 0:
            return f"{dynamic_count} (dynamic)"
        elif legacy_count > 0:
            return f"{legacy_count} (legacy)"
        return "0"

    components_count.short_description = 'عدد المكونات'

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

    latest_apk_status.short_description = 'حالة APK'

    def action_buttons(self, obj):
        latest_build = obj.apk_builds.filter(status='completed').first()
        download_btn = ''
        if latest_build and latest_build.download_url:
            download_btn = f'<a class="button" href="{latest_build.download_url}">📱 تحميل APK</a> '

        return format_html(
            '<a class="button" href="{}">👁️ معاينة</a> '
            '<a class="button" href="{}">📦 ZIP</a> '
            '<a class="button" href="{}">🔨 بناء APK</a> '
            + download_btn,
            reverse('admin:export_flutter_code', args=[obj.pk]),
            reverse('admin:download_project_zip', args=[obj.pk]),
            reverse('admin:build_apk', args=[obj.pk]),
        )

    action_buttons.short_description = 'الإجراءات'

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
            if project.dynamic_components.exists():
                from .utils import DynamicFlutterCodeGenerator
                generator = DynamicFlutterCodeGenerator(project)
            else:
                generator = FlutterCodeGenerator(project)

            code = generator.generate_full_project()

            return render(request, 'admin/flutter_code_preview.html', {
                'project': project,
                'code': code,
                'title': f'معاينة كود {project.name}'
            })
        except Exception as e:
            messages.error(request, f'خطأ في توليد الكود: {str(e)}')
            return redirect('admin:generator_flutterproject_changelist')

    def download_project_zip(self, request, project_id):
        """Download project as ZIP file"""
        try:
            project = get_object_or_404(FlutterProject, id=project_id)

            # Use dynamic generator if dynamic components exist
            if project.dynamic_components.exists():
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
            messages.error(request, f'خطأ في إنشاء ZIP: {str(e)}')
            return redirect('admin:generator_flutterproject_changelist')

    def build_apk(self, request, project_id):
        """Start APK build process"""
        try:
            project = get_object_or_404(FlutterProject, id=project_id)

            active_build = project.apk_builds.filter(status__in=['pending', 'building']).first()

            if active_build:
                messages.warning(request, f'هناك عملية بناء APK قيد التقدم للمشروع "{project.name}".')
                return redirect('admin:generator_flutterproject_changelist')

            apk_build = APKBuild.objects.create(project=project, status='pending')

            def build_in_background():
                self._build_apk_async(apk_build)

            thread = threading.Thread(target=build_in_background)
            thread.daemon = True
            thread.start()

            messages.success(
                request,
                format_html(
                    'تم بدء بناء APK للمشروع "{}". '
                    '<a href="{}">تتبع التقدم</a>',
                    project.name,
                    reverse("admin:build_status", args=[project.id])
                )
            )

            return redirect('admin:generator_flutterproject_changelist')

        except Exception as e:
            messages.error(request, f'خطأ في بدء بناء APK: {str(e)}')
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
            'title': f'حالة بناء APK - {project.name}'
        })


@admin.register(PubDevPackage)
class PubDevPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'is_active', 'widgets_count', 'last_updated']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
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

    discover_widgets.short_description = "Discover widgets"


@admin.register(ProjectPackage)
class ProjectPackageAdmin(admin.ModelAdmin):
    list_display = ['project', 'package', 'version']
    list_filter = ['project', 'package__is_active']
    search_fields = ['project__name', 'package__name']


@admin.register(PageComponent)
class PageComponentAdmin(admin.ModelAdmin):
    list_display = ['project', 'page_name', 'component_type', 'order', 'parent_component']
    list_filter = ['component_type', 'page_name']
    search_fields = ['project__name', 'page_name']
    list_editable = ['order']

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
    list_filter = ['status', 'created_at']
    search_fields = ['project__name']
    readonly_fields = ['created_at', 'completed_at', 'file_size', 'apk_file_path']

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
# DYNAMIC WIDGET SYSTEM ADMIN CLASSES
# ==========================================

@admin.register(WidgetType)
class WidgetTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'package', 'dart_class_name', 'category', 'is_container', 'is_active', 'properties_count']
    list_filter = ['category', 'is_container', 'is_active', 'package']
    search_fields = ['name', 'dart_class_name', 'package__name']
    readonly_fields = ['created_at', 'updated_at']

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

    actions = ['duplicate_widget_type', 'create_template']

    def duplicate_widget_type(self, request, queryset):
        for widget_type in queryset:
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
                is_active=False
            )

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
                    documentation=prop.documentation
                )

            messages.success(request, f"Duplicated {widget_type.name}")

    duplicate_widget_type.short_description = "Duplicate selected widget types"

    def create_template(self, request, queryset):
        for widget_type in queryset:
            if not widget_type.templates.filter(template_name='default').exists():
                WidgetTemplate.objects.create(
                    widget_type=widget_type,
                    template_name='default',
                    template_code=self._generate_default_template(widget_type)
                )
                messages.success(request, f"Created template for {widget_type.name}")

    create_template.short_description = "Create default templates"

    def _generate_default_template(self, widget_type):
        """Generate default template for a widget type"""
        if widget_type.is_container:
            return """{{ widget_name }}(
{% for prop in properties %}  {{ prop.name }}: {{ prop.value }},
{% endfor %}{% if children %}  children: [
{% for child in children %}    {{ child }},
{% endfor %}  ],
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
                        messages.success(request, f"Successfully discovered and registered widgets from {package_name}")
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
    list_editable = ['position', 'is_required']

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
    search_fields = ['widget_type__name', 'template_name']
    list_editable = ['priority', 'is_active']

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
    search_fields = ['transformer_name', 'property_type']
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
            'classes': ('wide',)
        })
    )


@admin.register(PackageWidgetRegistry)
class PackageWidgetRegistryAdmin(admin.ModelAdmin):
    list_display = ['package', 'widgets_count', 'auto_discovered', 'last_analyzed']
    list_filter = ['auto_discovered']
    search_fields = ['package__name']
    filter_horizontal = ['widget_types']
    readonly_fields = ['last_analyzed', 'discovery_data_formatted']

    def widgets_count(self, obj):
        return obj.widget_types.count()

    widgets_count.short_description = 'Widgets'

    def discovery_data_formatted(self, obj):
        if obj.discovery_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.discovery_data, indent=2))
        return '-'

    discovery_data_formatted.short_description = 'Discovery Data'

    actions = ['rediscover_widgets']

    def rediscover_widgets(self, request, queryset):
        analyzer = PackageAnalyzer()
        for registry in queryset:
            try:
                analyzer.auto_register_widgets(registry.package.name)
                messages.success(request, f"Rediscovered widgets for {registry.package.name}")
            except Exception as e:
                messages.error(request, f"Error discovering {registry.package.name}: {str(e)}")

    rediscover_widgets.short_description = "Rediscover widgets from packages"


@admin.register(WidgetPattern)
class WidgetPatternAdmin(admin.ModelAdmin):
    list_display = ['name', 'widget_type', 'category']
    list_filter = ['category', 'widget_type__category']
    search_fields = ['name', 'description', 'widget_type__name']

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
            'fields': ('condition', 'action')
        })
    )


@admin.register(DynamicPageComponent)
class DynamicPageComponentAdmin(admin.ModelAdmin):
    list_display = ['project', 'page_name', 'widget_type', 'order', 'parent_component', 'preview']
    list_filter = ['page_name', 'widget_type__category', 'project']
    search_fields = ['project__name', 'page_name', 'widget_type__name']
    list_editable = ['order']

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
            from .widget_generator import DynamicWidgetGenerator
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


# Customize admin site headers
admin.site.site_header = "Flutter Code Generator"
admin.site.site_title = "Flutter Generator"
admin.site.index_title = "Dynamic Flutter Code Generator Admin"