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


