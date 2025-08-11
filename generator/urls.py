from django.urls import path
from . import views

app_name = 'generator'

urlpatterns = [
    path('search-packages/', views.search_pub_packages, name='search_packages'),
    path('package-info/<str:package_name>/', views.get_package_info, name='package_info'),
    path('download-apk/<int:build_id>/', views.download_apk, name='download_apk'),
]