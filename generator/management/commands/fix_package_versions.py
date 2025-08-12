from django.core.management.base import BaseCommand
from generator.models import PubDevPackage


class Command(BaseCommand):
    help = 'Fix package versions that are set to "latest"'

    def handle(self, *args, **options):
        # Default versions for known packages
        default_versions = {
            'animated_text_kit': '4.2.2',
            'shimmer': '3.0.0',
            'flutter_staggered_grid_view': '0.7.0',
            'badges': '3.1.2',
            'flutter_speed_dial': '7.0.0',
            'percent_indicator': '4.2.3',
            'flutter_svg': '2.0.10',
            'font_awesome_flutter': '10.7.0',
            'google_fonts': '6.2.1',
            'carousel_slider': '4.2.1',
            'cached_network_image': '3.3.1',
            'http': '1.2.0',
            'provider': '6.1.2',
            'shared_preferences': '2.2.3',
            'dio': '5.4.3',
            'url_launcher': '6.2.5',
            'image_picker': '1.0.7',
            'video_player': '2.8.5',
            'google_maps_flutter': '2.6.0',
        }

        packages = PubDevPackage.objects.filter(version='latest')

        for package in packages:
            if package.name in default_versions:
                package.version = default_versions[package.name]
            else:
                package.version = 'any'
            package.save()
            self.stdout.write(f'Fixed {package.name}: {package.version}')

        self.stdout.write(self.style.SUCCESS(f'Fixed {packages.count()} packages'))