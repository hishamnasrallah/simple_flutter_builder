import os

from django.db import models
import json


class FlutterProject(models.Model):
    name = models.CharField(max_length=200, verbose_name="اسم المشروع")
    description = models.TextField(blank=True, verbose_name="الوصف")
    package_name = models.CharField(max_length=200, default="com.example.app")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "مشروع Flutter"
        verbose_name_plural = "مشاريع Flutter"


class PubDevPackage(models.Model):
    name = models.CharField(max_length=200, unique=True)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    homepage = models.URLField(blank=True)
    documentation = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.version})"


class ProjectPackage(models.Model):
    project = models.ForeignKey(FlutterProject, on_delete=models.CASCADE, related_name='packages')
    package = models.ForeignKey(PubDevPackage, on_delete=models.CASCADE)
    version = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ('project', 'package')


class PageComponent(models.Model):
    COMPONENT_TYPES = [
        ('scaffold', 'Scaffold'),
        ('appbar', 'AppBar'),
        ('container', 'Container'),
        ('text', 'Text'),
        ('button', 'Button'),
        ('image', 'Image'),
        ('listview', 'ListView'),
        ('column', 'Column'),
        ('row', 'Row'),
    ]

    project = models.ForeignKey(FlutterProject, on_delete=models.CASCADE, related_name='components')
    page_name = models.CharField(max_length=100, default="HomePage")
    component_type = models.CharField(max_length=50, choices=COMPONENT_TYPES)
    properties = models.JSONField(default=dict)  # لتخزين الخصائص مثل الألوان، الأحجام، إلخ
    order = models.IntegerField(default=0)
    parent_component = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.project.name} - {self.component_type}"

    class Meta:
        ordering = ['order']


class APKBuild(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('building', 'Building'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    project = models.ForeignKey(FlutterProject, on_delete=models.CASCADE, related_name='apk_builds')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    apk_file_path = models.CharField(max_length=500, blank=True)
    build_log = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.project.name} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def apk_filename(self):
        if self.apk_file_path:
            return os.path.basename(self.apk_file_path)
        return None

    @property
    def download_url(self):
        if self.apk_file_path and os.path.exists(self.apk_file_path):
            return f'/download-apk/{self.id}/'
        return None

    class Meta:
        ordering = ['-created_at']
        verbose_name = "APK Build"
        verbose_name_plural = "APK Builds"


class WidgetType(models.Model):
    """Dynamic widget type definition - replaces hardcoded COMPONENT_TYPES"""
    WIDGET_CATEGORIES = [
        ('layout', 'Layout'),
        ('input', 'Input'),
        ('display', 'Display'),
        ('media', 'Media'),
        ('navigation', 'Navigation'),
        ('container', 'Container'),
        ('animation', 'Animation'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=100, unique=True, help_text="e.g., CarouselSlider, TextField")
    package = models.ForeignKey('PubDevPackage', on_delete=models.CASCADE, null=True, blank=True,
                                help_text="Package that provides this widget")
    dart_class_name = models.CharField(max_length=100, help_text="Actual Dart class name")
    category = models.CharField(max_length=50, choices=WIDGET_CATEGORIES, default='custom')
    is_container = models.BooleanField(default=False, help_text="Can contain child widgets")
    can_have_multiple_children = models.BooleanField(default=False)
    import_path = models.CharField(max_length=255, blank=True,
                                   help_text="Override default import path")
    documentation = models.TextField(blank=True)
    example_code = models.TextField(blank=True)
    min_flutter_version = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'package']
        ordering = ['category', 'name']

    def __str__(self):
        if self.package:
            return f"{self.name} ({self.package.name})"
        return self.name


class WidgetProperty(models.Model):
    """Defines properties for a widget"""
    PROPERTY_TYPES = [
        ('string', 'String'),
        ('int', 'Integer'),
        ('double', 'Double'),
        ('bool', 'Boolean'),
        ('color', 'Color'),
        ('enum', 'Enum'),
        ('widget', 'Widget'),
        ('widget_list', 'Widget List'),
        ('map', 'Map/Object'),
        ('duration', 'Duration'),
        ('edge_insets', 'EdgeInsets'),
        ('alignment', 'Alignment'),
        ('text_style', 'TextStyle'),
        ('decoration', 'Decoration'),
        ('gradient', 'Gradient'),
        ('shadow', 'Shadow'),
        ('border', 'Border'),
        ('custom', 'Custom Type'),
    ]

    widget_type = models.ForeignKey(WidgetType, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=100, help_text="Property name in Dart")
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES)
    dart_type = models.CharField(max_length=200, help_text="Exact Dart type signature")
    is_required = models.BooleanField(default=False)
    is_positional = models.BooleanField(default=False, help_text="Positional vs named parameter")
    position = models.IntegerField(default=0, help_text="Order for positional parameters")
    default_value = models.TextField(blank=True)
    allowed_values = models.JSONField(default=dict, blank=True,
                                      help_text="For enums/constraints")
    validation_rules = models.JSONField(default=dict, blank=True)
    documentation = models.TextField(blank=True)
    example_value = models.TextField(blank=True)

    class Meta:
        unique_together = ['widget_type', 'name']
        ordering = ['position', 'name']

    def __str__(self):
        return f"{self.widget_type.name}.{self.name}"


class WidgetTemplate(models.Model):
    """Code generation templates for widgets"""
    widget_type = models.ForeignKey(WidgetType, on_delete=models.CASCADE, related_name='templates')
    template_name = models.CharField(max_length=100, default='default')
    template_code = models.TextField(help_text="Django template syntax")
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority templates are used first")
    conditions = models.JSONField(default=dict, blank=True,
                                  help_text="When to use this template")
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ['widget_type', 'template_name']
        ordering = ['-priority', 'template_name']

    def __str__(self):
        return f"{self.widget_type.name} - {self.template_name}"


class PropertyTransformer(models.Model):
    """Rules for transforming property values to Dart code"""
    property_type = models.CharField(max_length=50, help_text="matches WidgetProperty.property_type")
    transformer_name = models.CharField(max_length=100)
    transformer_code = models.TextField(help_text="Python code or template")
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-priority', 'transformer_name']

    def __str__(self):
        return f"{self.property_type} - {self.transformer_name}"


class PackageWidgetRegistry(models.Model):
    """Registry of all widgets provided by a package"""
    package = models.ForeignKey('PubDevPackage', on_delete=models.CASCADE)
    widget_types = models.ManyToManyField(WidgetType)
    auto_discovered = models.BooleanField(default=False)
    discovery_data = models.JSONField(default=dict, help_text="Metadata from discovery")
    last_analyzed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Registry for {self.package.name}"


class WidgetPattern(models.Model):
    """Common patterns for widget usage"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    widget_type = models.ForeignKey(WidgetType, on_delete=models.CASCADE)
    pattern_template = models.TextField(help_text="Template for this pattern")
    example_properties = models.JSONField(default=dict)
    category = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class GenerationRule(models.Model):
    """Rules for code generation"""
    RULE_TYPES = [
        ('import', 'Import Rule'),
        ('property', 'Property Rule'),
        ('wrapper', 'Wrapper Rule'),
        ('validation', 'Validation Rule'),
        ('transform', 'Transform Rule'),
    ]

    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    name = models.CharField(max_length=100)
    condition = models.JSONField(default=dict, help_text="When to apply this rule")
    action = models.JSONField(default=dict, help_text="What action to take")
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-priority', 'name']

    def __str__(self):
        return f"{self.rule_type} - {self.name}"


# Update existing PageComponent to use dynamic WidgetType
class DynamicPageComponent(models.Model):
    """Replacement for PageComponent using dynamic widget types"""
    project = models.ForeignKey('FlutterProject', on_delete=models.CASCADE,
                                related_name='dynamic_components')
    page_name = models.CharField(max_length=100, default="HomePage")
    widget_type = models.ForeignKey(WidgetType, on_delete=models.CASCADE)
    properties = models.JSONField(default=dict)
    order = models.IntegerField(default=0)
    parent_component = models.ForeignKey('self', on_delete=models.CASCADE,
                                         null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.project.name} - {self.page_name} - {self.widget_type.name}"