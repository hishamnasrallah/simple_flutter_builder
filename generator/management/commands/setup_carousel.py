# generator/management/commands/setup_carousel.py
# Command to properly setup carousel_slider widget

from django.core.management.base import BaseCommand
from django.db import transaction
from generator.models import (
    PubDevPackage, WidgetType, WidgetProperty, WidgetTemplate
)


class Command(BaseCommand):
    help = 'Properly setup carousel_slider widget to avoid conflicts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎠 Setting up CarouselSlider...'))

        with transaction.atomic():
            # Create or get package
            package, _ = PubDevPackage.objects.get_or_create(
                name='carousel_slider',
                defaults={
                    'version': '4.2.1',
                    'description': 'A carousel slider widget'
                }
            )

            # Create or update CarouselSlider widget
            carousel, created = WidgetType.objects.update_or_create(
                name='CarouselSlider',
                defaults={
                    'package': package,
                    'dart_class_name': 'CarouselSlider',
                    'category': 'media',
                    'is_container': True,
                    'can_have_multiple_children': True,
                    'import_path': 'package:carousel_slider/carousel_slider.dart',
                    'documentation': 'A carousel slider widget for displaying multiple items',
                    'is_active': True
                }
            )

            if created:
                self.stdout.write('   ✅ Created CarouselSlider widget')
            else:
                self.stdout.write('   ✅ Updated CarouselSlider widget')

            # Clear existing properties
            carousel.properties.all().delete()

            # Create proper properties - NO items property as it will be handled specially
            WidgetProperty.objects.create(
                widget_type=carousel,
                name='options',
                property_type='map',
                dart_type='CarouselOptions',
                is_required=True,
                documentation='Carousel configuration options (height, autoPlay, etc.)'
            )

            # Create a special template for CarouselSlider
            WidgetTemplate.objects.update_or_create(
                widget_type=carousel,
                template_name='default',
                defaults={
                    'template_code': '''CarouselSlider(
  options: CarouselOptions(
    height: 200.0,
    autoPlay: true,
    autoPlayInterval: Duration(seconds: 3),
    viewportFraction: 0.8,
    enlargeCenterPage: true,
  ),
  items: [
    Container(
      margin: EdgeInsets.all(5.0),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10.0),
        color: Colors.blue,
      ),
      child: Center(child: Text('Slide 1', style: TextStyle(color: Colors.white, fontSize: 20))),
    ),
    Container(
      margin: EdgeInsets.all(5.0),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10.0),
        color: Colors.red,
      ),
      child: Center(child: Text('Slide 2', style: TextStyle(color: Colors.white, fontSize: 20))),
    ),
    Container(
      margin: EdgeInsets.all(5.0),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10.0),
        color: Colors.green,
      ),
      child: Center(child: Text('Slide 3', style: TextStyle(color: Colors.white, fontSize: 20))),
    ),
  ],
)''',
                    'priority': 10,
                    'is_active': True
                }
            )

            self.stdout.write('   ✅ Created CarouselSlider template')

            # Also create CarouselOptions as a helper widget type
            carousel_options, created = WidgetType.objects.update_or_create(
                name='CarouselOptions',
                defaults={
                    'package': package,
                    'dart_class_name': 'CarouselOptions',
                    'category': 'custom',
                    'is_container': False,
                    'documentation': 'Options for CarouselSlider',
                    'is_active': True
                }
            )

            # Add properties for CarouselOptions
            options_properties = [
                ('height', 'double', 'double', False),
                ('aspectRatio', 'double', 'double', False),
                ('viewportFraction', 'double', 'double', False),
                ('initialPage', 'int', 'int', False),
                ('enableInfiniteScroll', 'bool', 'bool', False),
                ('reverse', 'bool', 'bool', False),
                ('autoPlay', 'bool', 'bool', False),
                ('autoPlayInterval', 'duration', 'Duration', False),
                ('autoPlayAnimationDuration', 'duration', 'Duration', False),
                ('autoPlayCurve', 'enum', 'Curve', False),
                ('enlargeCenterPage', 'bool', 'bool', False),
                ('enlargeFactor', 'double', 'double', False),
                ('enlargeStrategy', 'enum', 'CenterPageEnlargeStrategy', False),
                ('onPageChanged', 'custom', 'Function', False),
                ('scrollDirection', 'enum', 'Axis', False),
                ('pauseAutoPlayOnTouch', 'bool', 'bool', False),
                ('pauseAutoPlayOnManualNavigate', 'bool', 'bool', False),
                ('pauseAutoPlayInFiniteScroll', 'bool', 'bool', False),
                ('pageSnapping', 'bool', 'bool', False),
                ('disableCenter', 'bool', 'bool', False),
            ]

            # Clear existing properties
            carousel_options.properties.all().delete()

            for prop_name, prop_type, dart_type, required in options_properties:
                WidgetProperty.objects.create(
                    widget_type=carousel_options,
                    name=prop_name,
                    property_type=prop_type,
                    dart_type=dart_type,
                    is_required=required
                )

            self.stdout.write('   ✅ Created CarouselOptions properties')

            self.stdout.write(self.style.SUCCESS('\n✅ CarouselSlider setup complete!'))
            self.stdout.write('\n📝 Usage example:')
            self.stdout.write('''
{
  "type": "CarouselSlider",
  "properties": {
    "items": [
      {"type": "Container", "properties": {"color": "blue", "height": 200}},
      {"type": "Container", "properties": {"color": "red", "height": 200}},
      {"type": "Container", "properties": {"color": "green", "height": 200}}
    ],
    "options": {
      "height": 200,
      "autoPlay": true,
      "autoPlayInterval": 3000,
      "viewportFraction": 0.8,
      "enlargeCenterPage": true
    }
  }
}
            ''')