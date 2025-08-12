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


# generator/models_extended.py
# Add this as a new file in your generator app

from django.db import models
import json


# ============================================
# NAVIGATION & ROUTING SYSTEM
# ============================================

class AppRoute(models.Model):
    """Define app routes and navigation"""
    project = models.ForeignKey('FlutterProject', on_delete=models.CASCADE, related_name='routes')
    route_name = models.CharField(max_length=100, unique=True)  # e.g., '/home', '/profile'
    route_path = models.CharField(max_length=200)  # e.g., '/product/:id'
    page_name = models.CharField(max_length=100)  # Which page to show
    is_protected = models.BooleanField(default=False)  # Requires auth
    is_initial = models.BooleanField(default=False)  # Starting route
    transition_type = models.CharField(max_length=50, default='material', choices=[
        ('material', 'Material'),
        ('cupertino', 'Cupertino'),
        ('fade', 'Fade'),
        ('slide', 'Slide'),
        ('scale', 'Scale'),
    ])

    class Meta:
        unique_together = ['project', 'route_name']

    def __str__(self):
        return f"{self.project.name} - {self.route_name}"


class NavigationItem(models.Model):
    """Bottom navigation or drawer items"""
    project = models.ForeignKey('FlutterProject', on_delete=models.CASCADE, related_name='nav_items')
    label = models.CharField(max_length=50)
    icon = models.CharField(max_length=100)  # Icon name
    route = models.ForeignKey(AppRoute, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']


# ============================================
# STATE MANAGEMENT SYSTEM
# ============================================

class AppState(models.Model):
    """Global app state variables"""
    STATE_TYPES = [
        ('string', 'String'),
        ('int', 'Integer'),
        ('double', 'Double'),
        ('bool', 'Boolean'),
        ('list', 'List'),
        ('map', 'Map/Object'),
        ('custom', 'Custom Class'),
    ]

    project = models.ForeignKey('FlutterProject', on_delete=models.CASCADE, related_name='states')
    variable_name = models.CharField(max_length=100)
    variable_type = models.CharField(max_length=50, choices=STATE_TYPES)
    initial_value = models.JSONField(default=dict)
    is_persistent = models.BooleanField(default=False)  # Save to local storage
    is_observable = models.BooleanField(default=True)  # Can trigger UI updates

    class Meta:
        unique_together = ['project', 'variable_name']

    def __str__(self):
        return f"{self.project.name} - {self.variable_name}"


class StateAction(models.Model):
    """Actions that modify state"""
    ACTION_TYPES = [
        ('set', 'Set Value'),
        ('increment', 'Increment'),
        ('decrement', 'Decrement'),
        ('toggle', 'Toggle Boolean'),
        ('add_to_list', 'Add to List'),
        ('remove_from_list', 'Remove from List'),
        ('update_map', 'Update Map'),
        ('api_response', 'From API Response'),
    ]

    state = models.ForeignKey(AppState, on_delete=models.CASCADE, related_name='actions')
    action_name = models.CharField(max_length=100)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    action_value = models.JSONField(null=True, blank=True)  # Value or transformation

    def __str__(self):
        return f"{self.action_name} - {self.state.variable_name}"


# ============================================
# API INTEGRATION SYSTEM
# ============================================

class APIConfiguration(models.Model):
    """Global API configuration for project"""
    project = models.OneToOneField('FlutterProject', on_delete=models.CASCADE)
    base_url = models.URLField()
    timeout = models.IntegerField(default=30)  # seconds
    retry_count = models.IntegerField(default=3)
    default_headers = models.JSONField(default=dict)

    def __str__(self):
        return f"API Config - {self.project.name}"


class APIEndpoint(models.Model):
    """API endpoints configuration"""
    HTTP_METHODS = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
    ]

    project = models.ForeignKey('FlutterProject', on_delete=models.CASCADE, related_name='api_endpoints')
    endpoint_name = models.CharField(max_length=100)
    endpoint_path = models.CharField(max_length=200)  # e.g., /users/:id
    method = models.CharField(max_length=10, choices=HTTP_METHODS)
    headers = models.JSONField(default=dict, blank=True)
    requires_auth = models.BooleanField(default=False)

    # Request configuration
    request_body_template = models.JSONField(null=True, blank=True)
    query_parameters = models.JSONField(default=list, blank=True)  # List of param names

    # Response configuration
    response_type = models.CharField(max_length=50, default='json')
    success_state_update = models.ForeignKey(AppState, on_delete=models.SET_NULL,
                                             null=True, blank=True, related_name='api_updates')
    error_message = models.CharField(max_length=200, default='An error occurred')

    class Meta:
        unique_together = ['project', 'endpoint_name']

    def __str__(self):
        return f"{self.endpoint_name} - {self.method}"


class DataModel(models.Model):
    """Data models for API responses and app data"""
    project = models.ForeignKey('FlutterProject', on_delete=models.CASCADE, related_name='data_models')
    model_name = models.CharField(max_length=100)
    fields = models.JSONField(default=list)  # List of {name, type, required}

    # Example fields format:
    # [
    #   {"name": "id", "type": "int", "required": true},
    #   {"name": "name", "type": "String", "required": true},
    #   {"name": "email", "type": "String", "required": false}
    # ]

    class Meta:
        unique_together = ['project', 'model_name']

    def __str__(self):
        return self.model_name


# ============================================
# AUTHENTICATION SYSTEM
# ============================================

class AuthConfiguration(models.Model):
    """Authentication setup for the app"""
    AUTH_TYPES = [
        ('jwt', 'JWT Token'),
        ('firebase', 'Firebase Auth'),
        ('oauth', 'OAuth 2.0'),
        ('basic', 'Basic Auth'),
        ('custom', 'Custom Auth'),
    ]

    project = models.OneToOneField('FlutterProject', on_delete=models.CASCADE)
    auth_type = models.CharField(max_length=50, choices=AUTH_TYPES)

    # Endpoints
    login_endpoint = models.ForeignKey(APIEndpoint, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='login_endpoint')
    register_endpoint = models.ForeignKey(APIEndpoint, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='register_endpoint')
    logout_endpoint = models.ForeignKey(APIEndpoint, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='logout_endpoint')
    refresh_endpoint = models.ForeignKey(APIEndpoint, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='refresh_endpoint')

    # Storage
    token_storage_key = models.CharField(max_length=100, default='auth_token')
    user_storage_key = models.CharField(max_length=100, default='user_data')

    # User model
    user_model = models.ForeignKey(DataModel, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Auth - {self.project.name}"


# ============================================
# FORMS & VALIDATION
# ============================================

class FormConfiguration(models.Model):
    """Form handling and validation"""
    project = models.ForeignKey('FlutterProject', on_delete=models.CASCADE, related_name='forms')
    form_name = models.CharField(max_length=100)
    page_name = models.CharField(max_length=100)

    # Form submission
    submit_endpoint = models.ForeignKey(APIEndpoint, on_delete=models.SET_NULL, null=True, blank=True)
    success_action = models.CharField(max_length=100, default='show_success')  # navigate, show_message, etc.
    success_route = models.ForeignKey(AppRoute, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['project', 'form_name']

    def __str__(self):
        return f"{self.form_name} - {self.project.name}"


class FormField(models.Model):
    """Form field definitions"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('email', 'Email Input'),
        ('password', 'Password Input'),
        ('number', 'Number Input'),
        ('phone', 'Phone Input'),
        ('multiline', 'Multiline Text'),
        ('dropdown', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio Button'),
        ('date', 'Date Picker'),
        ('time', 'Time Picker'),
        ('file', 'File Upload'),
    ]

    form = models.ForeignKey(FormConfiguration, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    label = models.CharField(max_length=100)
    placeholder = models.CharField(max_length=200, blank=True)
    initial_value = models.CharField(max_length=200, blank=True)

    # Validation
    is_required = models.BooleanField(default=False)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    regex_pattern = models.CharField(max_length=200, blank=True)
    error_message = models.CharField(max_length=200, default='Invalid input')

    # For dropdowns
    options = models.JSONField(default=list, blank=True)  # List of {label, value}

    # Binding
    bind_to_state = models.ForeignKey(AppState, on_delete=models.SET_NULL, null=True, blank=True)

    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.field_name} - {self.form.form_name}"


# ============================================
# BUSINESS LOGIC & FUNCTIONS
# ============================================

class CustomFunction(models.Model):
    """Custom Dart functions for business logic"""
    project = models.ForeignKey('FlutterProject', on_delete=models.CASCADE, related_name='custom_functions')
    function_name = models.CharField(max_length=100)
    parameters = models.JSONField(default=list)  # List of {name, type}
    return_type = models.CharField(max_length=50, default='void')
    function_body = models.TextField()  # Actual Dart code
    is_async = models.BooleanField(default=False)

    class Meta:
        unique_together = ['project', 'function_name']

    def __str__(self):
        return self.function_name


class EventHandler(models.Model):
    """Event handling for components"""
    EVENT_TYPES = [
        ('onTap', 'On Tap'),
        ('onPressed', 'On Pressed'),
        ('onLongPress', 'On Long Press'),
        ('onChanged', 'On Changed'),
        ('onSubmit', 'On Submit'),
        ('onInit', 'On Init'),
        ('onDispose', 'On Dispose'),
    ]

    ACTION_TYPES = [
        ('navigate', 'Navigate'),
        ('navigate_back', 'Navigate Back'),
        ('api_call', 'API Call'),
        ('update_state', 'Update State'),
        ('show_dialog', 'Show Dialog'),
        ('show_snackbar', 'Show Snackbar'),
        ('custom_function', 'Custom Function'),
        ('submit_form', 'Submit Form'),
    ]

    component = models.ForeignKey('DynamicPageComponent', on_delete=models.CASCADE, related_name='event_handlers')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)

    # Action configuration
    target_route = models.ForeignKey(AppRoute, on_delete=models.SET_NULL, null=True, blank=True)
    target_api = models.ForeignKey(APIEndpoint, on_delete=models.SET_NULL, null=True, blank=True)
    target_state = models.ForeignKey(AppState, on_delete=models.SET_NULL, null=True, blank=True)
    target_function = models.ForeignKey(CustomFunction, on_delete=models.SET_NULL, null=True, blank=True)

    # Additional parameters
    action_parameters = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.event_type} - {self.action_type}"


# ============================================
# LOCAL STORAGE
# ============================================

class LocalStorage(models.Model):
    """Local storage configuration using SharedPreferences"""
    STORAGE_TYPES = [
        ('string', 'String'),
        ('int', 'Integer'),
        ('double', 'Double'),
        ('bool', 'Boolean'),
        ('stringList', 'String List'),
    ]

    project = models.ForeignKey('FlutterProject', on_delete=models.CASCADE, related_name='storage_keys')
    key_name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=50, choices=STORAGE_TYPES)
    default_value = models.JSONField(null=True, blank=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['project', 'key_name']

    def __str__(self):
        return f"{self.key_name} - {self.project.name}"


# ============================================
# DYNAMIC LISTS & DATA BINDING
# ============================================

class DynamicListConfiguration(models.Model):
    """Configuration for dynamic lists (ListView.builder)"""
    DATA_SOURCES = [
        ('api', 'API Endpoint'),
        ('state', 'App State'),
        ('firebase', 'Firebase'),
        ('static', 'Static Data'),
    ]

    component = models.OneToOneField('DynamicPageComponent', on_delete=models.CASCADE)
    data_source = models.CharField(max_length=20, choices=DATA_SOURCES)

    # Data source configuration
    api_endpoint = models.ForeignKey(APIEndpoint, on_delete=models.SET_NULL, null=True, blank=True)
    state_variable = models.ForeignKey(AppState, on_delete=models.SET_NULL, null=True, blank=True)
    static_data = models.JSONField(default=list, blank=True)

    # Item template
    item_widget_type = models.ForeignKey('WidgetType', on_delete=models.CASCADE)
    item_properties_mapping = models.JSONField(default=dict)  # Map data fields to widget properties

    # UI states
    loading_widget = models.JSONField(default=dict)  # Widget while loading
    empty_widget = models.JSONField(default=dict)  # Widget when no data
    error_widget = models.JSONField(default=dict)  # Widget on error

    # Features
    enable_pull_refresh = models.BooleanField(default=True)
    enable_pagination = models.BooleanField(default=False)
    items_per_page = models.IntegerField(default=20)

    def __str__(self):
        return f"Dynamic List - {self.component.page_name}"


# ============================================
# CONDITIONAL RENDERING
# ============================================

class ConditionalWidget(models.Model):
    """Show/hide widgets based on conditions"""
    CONDITION_TYPES = [
        ('state_equals', 'State Equals'),
        ('state_not_equals', 'State Not Equals'),
        ('state_greater', 'State Greater Than'),
        ('state_less', 'State Less Than'),
        ('state_contains', 'State Contains'),
        ('is_authenticated', 'Is Authenticated'),
        ('is_not_authenticated', 'Is Not Authenticated'),
        ('platform_is', 'Platform Is'),
    ]

    component = models.ForeignKey('DynamicPageComponent', on_delete=models.CASCADE,
                                  related_name='conditional_rendering')
    condition_type = models.CharField(max_length=50, choices=CONDITION_TYPES)

    # Condition configuration
    state_variable = models.ForeignKey(AppState, on_delete=models.SET_NULL, null=True, blank=True)
    condition_value = models.JSONField(null=True, blank=True)

    # Widgets to show
    show_widget = models.JSONField(default=dict)  # Widget to show if condition is true
    hide_widget = models.JSONField(null=True, blank=True)  # Optional widget for false condition

    def __str__(self):
        return f"Conditional - {self.condition_type}"


# ============================================
# APP CONFIGURATION
# ============================================

class AppConfiguration(models.Model):
    """Enhanced app configuration"""
    project = models.OneToOneField('FlutterProject', on_delete=models.CASCADE)

    # App type and features
    app_type = models.CharField(max_length=50, choices=[
        ('ecommerce', 'E-commerce'),
        ('social', 'Social Media'),
        ('business', 'Business'),
        ('education', 'Education'),
        ('health', 'Healthcare'),
        ('finance', 'Finance'),
        ('news', 'News'),
        ('entertainment', 'Entertainment'),
        ('productivity', 'Productivity'),
        ('custom', 'Custom'),
    ])

    # State management
    state_management = models.CharField(max_length=50, choices=[
        ('provider', 'Provider'),
        ('riverpod', 'Riverpod'),
        ('getx', 'GetX'),
        ('bloc', 'BLoC'),
        ('mobx', 'MobX'),
    ], default='provider')

    # Navigation type
    navigation_type = models.CharField(max_length=50, choices=[
        ('drawer', 'Navigation Drawer'),
        ('bottom_nav', 'Bottom Navigation'),
        ('tab_bar', 'Tab Bar'),
        ('custom', 'Custom Navigation'),
    ], default='drawer')

    # Theme configuration
    primary_color = models.CharField(max_length=7, default='#2196F3')
    secondary_color = models.CharField(max_length=7, default='#FF4081')
    dark_mode_enabled = models.BooleanField(default=True)
    font_family = models.CharField(max_length=100, default='Roboto')

    # Features flags
    uses_authentication = models.BooleanField(default=False)
    uses_api = models.BooleanField(default=False)
    uses_local_storage = models.BooleanField(default=False)
    uses_push_notifications = models.BooleanField(default=False)
    uses_maps = models.BooleanField(default=False)
    uses_camera = models.BooleanField(default=False)
    uses_payments = models.BooleanField(default=False)
    uses_social_login = models.BooleanField(default=False)
    uses_analytics = models.BooleanField(default=False)
    uses_ads = models.BooleanField(default=False)

    # Localization
    supported_languages = models.JSONField(default=list)  # ['en', 'es', 'fr']
    default_language = models.CharField(max_length=5, default='en')

    def __str__(self):
        return f"Config - {self.project.name}"