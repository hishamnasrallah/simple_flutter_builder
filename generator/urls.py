# generator/urls.py
# CONSOLIDATED VERSION - Combines urls.py and api_urls.py

from django.urls import path
from . import views

app_name = 'generator'

urlpatterns = [
    # ==========================================
    # REGULAR VIEWS (Original urls.py)
    # ==========================================
    path('search-packages/', views.search_pub_packages, name='search_packages'),
    path('package-info/<str:package_name>/', views.get_package_info, name='package_info'),
    path('download-apk/<int:build_id>/', views.download_apk, name='download_apk'),

    # ==========================================
    # API ENDPOINTS (Original api_urls.py)
    # ==========================================

    # Widget Types API
    path('api/widgets/', views.list_widget_types, name='api_list_widgets'),
    path('api/widgets/<int:widget_id>/', views.get_widget_detail, name='api_widget_detail'),
    path('api/widgets/categories/', views.widget_categories, name='api_widget_categories'),
    path('api/widgets/property-types/', views.property_types, name='api_property_types'),

    # Code Generation API
    path('api/generate/', views.generate_widget_code, name='api_generate_code'),
    path('api/preview/', views.preview_component, name='api_preview_component'),

    # Packages API
    path('api/packages/', views.list_packages, name='api_list_packages'),
    path('api/packages/discover/', views.discover_package_api, name='api_discover_package'),

    # Projects & Components API
    path('api/projects/<int:project_id>/widgets/', views.get_project_widgets, name='api_project_widgets'),
    path('api/components/create/', views.create_component, name='api_create_component'),
    path('api/components/<int:component_id>/update/', views.update_component, name='api_update_component'),
    path('api/components/<int:component_id>/delete/', views.delete_component, name='api_delete_component'),
]