# ===========================================
# File: generator/admin.py (COMPLETE VERSION)
# ===========================================

from django.contrib import admin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponse, FileResponse
from django.contrib import messages
from django.utils import timezone
from .models import FlutterProject, PubDevPackage, ProjectPackage, PageComponent, APKBuild
from .utils import FlutterCodeGenerator, PubDevSync
import os
import zipfile
import tempfile
import subprocess
import threading


@admin.register(FlutterProject)
class FlutterProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'package_name', 'components_count', 'latest_apk_status', 'created_at', 'action_buttons']
    list_filter = ['created_at']
    search_fields = ['name', 'package_name']

    def components_count(self, obj):
        return obj.components.count()

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
        # Check if there's a completed APK build
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
            generator = FlutterCodeGenerator(project)

            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            project_name = project.name.replace(' ', '_').replace('-', '_').lower()
            # Remove any non-alphanumeric characters except underscore
            import re
            project_name = re.sub(r'[^a-zA-Z0-9_]', '', project_name)

            project_dir = os.path.join(temp_dir, project_name)

            # Generate project files
            generator.create_project_files(project_dir)

            # Create ZIP file
            zip_filename = f"{project_name}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arc_path)

            # Return file response
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

            # Check if there's already a pending/building APK
            active_build = project.apk_builds.filter(
                status__in=['pending', 'building']
            ).first()

            if active_build:
                messages.warning(
                    request,
                    f'هناك عملية بناء APK قيد التقدم للمشروع "{project.name}". '
                    'يرجى الانتظار حتى اكتمالها.'
                )
                return redirect('admin:generator_flutterproject_changelist')

            # Create new APK build record
            apk_build = APKBuild.objects.create(
                project=project,
                status='pending'
            )

            # Start build process in background
            def build_in_background():
                self._build_apk_async(apk_build)

            thread = threading.Thread(target=build_in_background)
            thread.daemon = True
            thread.start()

            messages.success(
                request,
                format_html(
                    'تم بدء بناء APK للمشروع "{}". '
                    'ستتلقى إشعاراً عند اكتمال البناء. '
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

                # Get file size
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
        builds = project.apk_builds.all()[:10]  # Last 10 builds

        return render(request, 'admin/apk_build_status.html', {
            'project': project,
            'builds': builds,
            'title': f'حالة بناء APK - {project.name}'
        })


@admin.register(PubDevPackage)
class PubDevPackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'is_active', 'last_updated']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    actions = ['sync_from_pub_dev', 'activate_packages', 'deactivate_packages']

    def last_updated(self, obj):
        return "غير محدد"  # You can add a timestamp field later

    last_updated.short_description = 'آخر تحديث'

    @admin.action(description="تحديث من pub.dev")
    def sync_from_pub_dev(self, request, queryset):
        syncer = PubDevSync()
        updated_count = 0
        for package in queryset:
            try:
                syncer.update_package_info(package)
                updated_count += 1
            except Exception as e:
                messages.warning(request, f'فشل تحديث {package.name}: {str(e)}')

        messages.success(request, f'تم تحديث {updated_count} حزمة بنجاح')

    @admin.action(description="تفعيل الحزم المحددة")
    def activate_packages(self, request, queryset):
        updated = queryset.update(is_active=True)
        messages.success(request, f'تم تفعيل {updated} حزمة')

    @admin.action(description="إلغاء تفعيل الحزم المحددة")
    def deactivate_packages(self, request, queryset):
        updated = queryset.update(is_active=False)
        messages.success(request, f'تم إلغاء تفعيل {updated} حزمة')


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
        # Add help text for properties field
        if 'properties' in form.base_fields:
            form.base_fields['properties'].help_text = '''
            أدخل الخصائص بصيغة JSON، مثال:
            {"text": "مرحباً", "fontSize": 20, "color": "blue"}
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

    file_size_mb.short_description = 'حجم الملف'

    def download_link(self, obj):
        if obj.download_url:
            return format_html(
                '<a href="{}" class="button">📱 تحميل</a>',
                obj.download_url
            )
        return '-'

    download_link.short_description = 'تحميل'


# Customize admin site headers
admin.site.site_header = "Flutter Code Generator"
admin.site.site_title = "Flutter Generator"
admin.site.index_title = "إدارة مولد تطبيقات Flutter"