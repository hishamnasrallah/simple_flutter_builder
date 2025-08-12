# generator/api_urls.py
# URL configuration for the dynamic widget API

from django.urls import path
from . import api_views

app_name = 'generator_api'

urlpatterns = [
    # Widget Types
    path('widgets/', api_views.list_widget_types, name='list_widgets'),
    path('widgets/<int:widget_id>/', api_views.get_widget_detail, name='widget_detail'),
    path('widgets/categories/', api_views.widget_categories, name='widget_categories'),
    path('widgets/property-types/', api_views.property_types, name='property_types'),

    # Code Generation
    path('generate/', api_views.generate_widget_code, name='generate_code'),
    path('preview/', api_views.preview_component, name='preview_component'),

    # Packages
    path('packages/', api_views.list_packages, name='list_packages'),
    path('packages/discover/', api_views.discover_package_api, name='discover_package'),

    # Projects & Components
    path('projects/<int:project_id>/widgets/', api_views.get_project_widgets, name='project_widgets'),
    path('components/create/', api_views.create_component, name='create_component'),
    path('components/<int:component_id>/update/', api_views.update_component, name='update_component'),
    path('components/<int:component_id>/delete/', api_views.delete_component, name='delete_component'),
]

# Add to your main urls.py:
# path('api/generator/', include('generator.api_urls')),