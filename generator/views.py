import os

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, Http404, FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import APKBuild
from .utils import PubDevSync
import json


@require_http_methods(["GET"])
def search_pub_packages(request):
    """البحث في حزم pub.dev"""
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({
            'success': False,
            'error': 'معامل البحث مطلوب',
            'packages': []
        }, status=400)

    if len(query) < 2:
        return JsonResponse({
            'success': False,
            'error': 'يجب أن يكون البحث أطول من حرفين',
            'packages': []
        }, status=400)

    try:
        syncer = PubDevSync()
        results = syncer.search_packages(query)

        if results and 'packages' in results:
            packages = []
            for package in results['packages'][:20]:  # Limit to 20 results
                packages.append({
                    'name': package.get('package', ''),
                    'description': package.get('description', 'لا يوجد وصف')[:200],
                    'version': package.get('latest', {}).get('version', ''),
                    'popularity': package.get('score', {}).get('popularityScore', 0),
                })

            return JsonResponse({
                'success': True,
                'packages': packages,
                'count': len(packages)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'لم يتم العثور على نتائج',
                'packages': []
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في البحث: {str(e)}',
            'packages': []
        }, status=500)


@require_http_methods(["GET"])
def get_package_info(request, package_name):
    """جلب معلومات حزمة محددة"""
    try:
        syncer = PubDevSync()
        info = syncer.get_package_info(package_name)

        if info:
            return JsonResponse({
                'success': True,
                'package': {
                    'name': info.get('name', package_name),
                    'description': info.get('description', ''),
                    'version': info.get('latest', {}).get('version', ''),
                    'homepage': info.get('latest', {}).get('pubspec', {}).get('homepage', ''),
                    'documentation': info.get('latest', {}).get('pubspec', {}).get('documentation', ''),
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'الحزمة غير موجودة'
            }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطأ في جلب معلومات الحزمة: {str(e)}'
        }, status=500)


@staff_member_required
def download_apk(request, build_id):
    """Download APK file"""
    build = get_object_or_404(APKBuild, id=build_id)

    if not build.apk_file_path or not os.path.exists(build.apk_file_path):
        raise Http404("APK file not found")

    response = FileResponse(
        open(build.apk_file_path, 'rb'),
        content_type='application/vnd.android.package-archive',
        as_attachment=True,
        filename=build.apk_filename
    )
    return response