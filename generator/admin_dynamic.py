# generator/admin_dynamic.py
# Add this to your existing admin.py or create as separate file

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Import the new models (add to your existing models import)
from .models import (
    WidgetType, WidgetProperty, WidgetTemplate,
    PropertyTransformer, PackageWidgetRegistry,
    WidgetPattern, GenerationRule, DynamicPageComponent
)
from .package_analyzer import PackageAnalyzer


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
            # Duplicate widget type
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
                is_active=False  # Start as inactive
            )

            # Duplicate properties
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

        # Add help text
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
            # Truncate if too long
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


# Custom admin views for package discovery
class PackageDiscoveryAdmin(admin.ModelAdmin):
    """Custom admin for discovering and adding packages"""

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