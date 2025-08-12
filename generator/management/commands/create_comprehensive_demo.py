# generator/management/commands/create_comprehensive_demo.py
# Save this as a NEW FILE in generator/management/commands/

from django.core.management.base import BaseCommand
from django.db import transaction
from generator.models import (
    FlutterProject, PubDevPackage, ProjectPackage,
    WidgetType, DynamicPageComponent
)
import json


class Command(BaseCommand):
    help = 'Create a comprehensive demo app showcasing all widget capabilities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Super Demo App',
            help='Name of the demo project'
        )

    def handle(self, *args, **options):
        project_name = options['name']

        self.stdout.write(self.style.SUCCESS(f'🚀 Creating Comprehensive Demo App: {project_name}\n'))

        with transaction.atomic():
            # Create project
            project = self._create_project(project_name)

            # Add required packages
            self._add_packages(project)

            # Ensure all required widgets exist
            self._ensure_widgets()

            # Create pages
            self._create_main_scaffold(project)
            self._create_home_page(project)
            self._create_gallery_page(project)
            self._create_camera_page(project)
            self._create_maps_page(project)
            self._create_forms_page(project)
            self._create_charts_page(project)
            self._create_profile_page(project)
            self._create_settings_page(project)
            self._create_about_page(project)

            self.stdout.write(self.style.SUCCESS(f'\n✅ Demo app created successfully!'))
            self._print_summary(project)

    def _create_project(self, name):
        """Create the main project"""
        project, created = FlutterProject.objects.get_or_create(
            name=name,
            defaults={
                'package_name': 'com.example.super_demo',
                'description': 'A comprehensive demo showcasing all Flutter widgets and capabilities'
            }
        )

        if not created:
            # Clear existing components
            project.dynamic_components.all().delete()
            self.stdout.write('   🧹 Cleared existing components')

        return project

    def _add_packages(self, project):
        """Add all necessary packages"""
        packages = [
            ('image_picker', '^1.0.0'),  # Camera functionality
            ('google_maps_flutter', '^2.5.0'),  # Maps
            ('cached_network_image', '^3.3.0'),  # Image caching
            ('url_launcher', '^6.2.0'),  # Open URLs
            ('shared_preferences', '^2.2.0'),  # Local storage
            ('http', '^1.1.0'),  # API calls
            # ('charts_flutter', '^0.12.0'),  # Charts
            ('flutter_speed_dial', '^7.0.0'),  # FAB with options
            ('carousel_slider', '^4.2.0'),  # Image carousel
            ('percent_indicator', '^4.2.0'),  # Progress indicators
            ('flutter_rating_bar', '^4.0.0'),  # Rating stars
            ('flutter_staggered_grid_view', '^0.7.0'),  # Grid layouts
            ('shimmer', '^3.0.0'),  # Loading effects
            ('badges', '^3.1.0'),  # Notification badges
        ]

        for package_name, version in packages:
            package, _ = PubDevPackage.objects.get_or_create(
                name=package_name,
                defaults={'version': version, 'is_active': True}
            )
            ProjectPackage.objects.get_or_create(
                project=project,
                package=package,
                defaults={'version': version}
            )

        self.stdout.write(f'   ✅ Added {len(packages)} packages')

    def _ensure_widgets(self):
        """Ensure all required widgets exist"""
        widgets = [
            'Scaffold', 'AppBar', 'Drawer', 'ListTile', 'Container', 'Text', 'Icon',
            'Column', 'Row', 'Card', 'ElevatedButton', 'TextField', 'Image',
            'CircleAvatar', 'Divider', 'Center', 'Padding', 'SizedBox',
            'GridView', 'ListView', 'Stack', 'Positioned', 'FloatingActionButton',
            'BottomNavigationBar', 'TabBar', 'Switch', 'Checkbox', 'Radio',
            'Slider', 'LinearProgressIndicator', 'CircularProgressIndicator',
            'ExpansionTile', 'Chip', 'Badge', 'SpeedDial'
        ]

        for widget_name in widgets:
            WidgetType.objects.get_or_create(
                name=widget_name,
                defaults={
                    'dart_class_name': widget_name,
                    'category': 'display',
                    'is_active': True
                }
            )

    def _create_main_scaffold(self, project):
        """Create main scaffold with navigation drawer"""
        self.stdout.write('   📱 Creating main scaffold with drawer...')

        scaffold_props = {
            'appBar': {
                'type': 'AppBar',
                'properties': {
                    'title': {'type': 'Text', 'properties': {'data': 'Super Demo App'}},
                    'backgroundColor': '#2196F3',
                    'actions': [
                        {
                            'type': 'IconButton',
                            'properties': {
                                'icon': {'type': 'Icon', 'properties': {'icon': 'Icons.notifications'}},
                                'onPressed': '() {}'
                            }
                        },
                        {
                            'type': 'Badge',
                            'properties': {
                                'badgeContent': {'type': 'Text', 'properties': {'data': '3'}},
                                'child': {
                                    'type': 'IconButton',
                                    'properties': {
                                        'icon': {'type': 'Icon', 'properties': {'icon': 'Icons.shopping_cart'}},
                                        'onPressed': '() {}'
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            'drawer': self._create_navigation_drawer(),
            'body': {'type': 'Container', 'properties': {}},
            'floatingActionButton': {
                'type': 'SpeedDial',
                'properties': {
                    'icon': 'Icons.add',
                    'activeIcon': 'Icons.close',
                    'backgroundColor': '#2196F3',
                    'children': [
                        {
                            'icon': 'Icons.camera',
                            'label': 'Camera',
                            'onTap': '() => Navigator.pushNamed(context, "/camera")'
                        },
                        {
                            'icon': 'Icons.image',
                            'label': 'Gallery',
                            'onTap': '() => Navigator.pushNamed(context, "/gallery")'
                        },
                        {
                            'icon': 'Icons.share',
                            'label': 'Share',
                            'onTap': '() {}'
                        }
                    ]
                }
            }
        }

        self._create_component(project, 'MainPage', 'Scaffold', scaffold_props, 0)

    def _create_navigation_drawer(self):
        """Create comprehensive navigation drawer"""
        return {
            'type': 'Drawer',
            'properties': {
                'child': {
                    'type': 'ListView',
                    'properties': {
                        'padding': {'all': 0},
                        'children': [
                            # Header with user info
                            {
                                'type': 'UserAccountsDrawerHeader',
                                'properties': {
                                    'accountName': {'type': 'Text', 'properties': {'data': 'Demo User'}},
                                    'accountEmail': {'type': 'Text', 'properties': {'data': 'demo@example.com'}},
                                    'currentAccountPicture': {
                                        'type': 'CircleAvatar',
                                        'properties': {
                                            'backgroundColor': 'white',
                                            'child': {'type': 'Text', 'properties': {'data': 'DU'}}
                                        }
                                    },
                                    'decoration': {
                                        'gradient': {
                                            'type': 'LinearGradient',
                                            'colors': ['#2196F3', '#1976D2']
                                        }
                                    }
                                }
                            },
                            # Navigation items
                            self._create_drawer_item('Home', 'Icons.home', '/home'),
                            self._create_drawer_item('Gallery', 'Icons.photo_library', '/gallery'),
                            self._create_drawer_item('Camera', 'Icons.camera_alt', '/camera'),
                            self._create_drawer_item('Maps', 'Icons.map', '/maps'),
                            self._create_drawer_item('Forms', 'Icons.edit', '/forms'),
                            self._create_drawer_item('Charts', 'Icons.bar_chart', '/charts'),
                            {'type': 'Divider', 'properties': {}},
                            # Expansion tile with sub-items
                            {
                                'type': 'ExpansionTile',
                                'properties': {
                                    'title': {'type': 'Text', 'properties': {'data': 'More Options'}},
                                    'leading': {'type': 'Icon', 'properties': {'icon': 'Icons.more_horiz'}},
                                    'children': [
                                        self._create_drawer_item('Profile', 'Icons.person', '/profile'),
                                        self._create_drawer_item('Settings', 'Icons.settings', '/settings'),
                                        self._create_drawer_item('Help', 'Icons.help', '/help'),
                                        self._create_drawer_item('About', 'Icons.info', '/about'),
                                    ]
                                }
                            },
                            {'type': 'Divider', 'properties': {}},
                            self._create_drawer_item('Share App', 'Icons.share', None, 'share'),
                            self._create_drawer_item('Rate Us', 'Icons.star', None, 'rate'),
                            self._create_drawer_item('Logout', 'Icons.exit_to_app', None, 'logout'),
                        ]
                    }
                }
            }
        }

    def _create_drawer_item(self, title, icon, route=None, action=None):
        """Create a drawer list item"""
        onTap = '() {}'
        if route:
            onTap = f'() => Navigator.pushNamed(context, "{route}")'
        elif action == 'share':
            onTap = '() => share()'
        elif action == 'rate':
            onTap = '() => rateApp()'
        elif action == 'logout':
            onTap = '() => logout()'

        return {
            'type': 'ListTile',
            'properties': {
                'leading': {'type': 'Icon', 'properties': {'icon': icon}},
                'title': {'type': 'Text', 'properties': {'data': title}},
                'onTap': onTap
            }
        }

    def _create_home_page(self, project):
        """Create home page with various widgets"""
        self.stdout.write('   📄 Creating HomePage...')

        home_content = {
            'child': {
                'type': 'SingleChildScrollView',
                'properties': {
                    'padding': {'all': 16},
                    'child': {
                        'type': 'Column',
                        'properties': {
                            'crossAxisAlignment': 'stretch',
                            'children': [
                                # Welcome card
                                {
                                    'type': 'Card',
                                    'properties': {
                                        'elevation': 4,
                                        'child': {
                                            'type': 'Container',
                                            'properties': {
                                                'padding': {'all': 16},
                                                'child': {
                                                    'type': 'Column',
                                                    'properties': {
                                                        'children': [
                                                            {'type': 'Text',
                                                             'properties': {'data': 'Welcome to Demo App!',
                                                                            'style': {'fontSize': 24,
                                                                                      'fontWeight': 'bold'}}},
                                                            {'type': 'SizedBox', 'properties': {'height': 8}},
                                                            {'type': 'Text',
                                                             'properties': {'data': 'Explore all features below'}}
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 16}},

                                # Feature grid
                                {
                                    'type': 'GridView',
                                    'properties': {
                                        'shrinkWrap': True,
                                        'physics': 'NeverScrollableScrollPhysics()',
                                        'crossAxisCount': 2,
                                        'children': [
                                            self._create_feature_card('Camera', 'Icons.camera', '#4CAF50'),
                                            self._create_feature_card('Gallery', 'Icons.photo', '#2196F3'),
                                            self._create_feature_card('Maps', 'Icons.map', '#FF9800'),
                                            self._create_feature_card('Charts', 'Icons.bar_chart', '#9C27B0'),
                                            self._create_feature_card('Forms', 'Icons.edit', '#F44336'),
                                            self._create_feature_card('Settings', 'Icons.settings', '#607D8B'),
                                        ]
                                    }
                                },

                                {'type': 'SizedBox', 'properties': {'height': 16}},

                                # Progress indicators section
                                {
                                    'type': 'Card',
                                    'properties': {
                                        'child': {
                                            'type': 'Container',
                                            'properties': {
                                                'padding': {'all': 16},
                                                'child': {
                                                    'type': 'Column',
                                                    'properties': {
                                                        'children': [
                                                            {'type': 'Text',
                                                             'properties': {'data': 'Progress Indicators',
                                                                            'style': {'fontSize': 18,
                                                                                      'fontWeight': 'bold'}}},
                                                            {'type': 'SizedBox', 'properties': {'height': 16}},
                                                            {'type': 'LinearProgressIndicator',
                                                             'properties': {'value': 0.7}},
                                                            {'type': 'SizedBox', 'properties': {'height': 16}},
                                                            {
                                                                'type': 'Row',
                                                                'properties': {
                                                                    'mainAxisAlignment': 'spaceEvenly',
                                                                    'children': [
                                                                        {
                                                                            'type': 'CircularPercentIndicator',
                                                                            'properties': {
                                                                                'radius': 60,
                                                                                'percent': 0.75,
                                                                                'center': {'type': 'Text',
                                                                                           'properties': {
                                                                                               'data': '75%'}},
                                                                                'progressColor': '#4CAF50'
                                                                            }
                                                                        },
                                                                        {
                                                                            'type': 'CircularPercentIndicator',
                                                                            'properties': {
                                                                                'radius': 60,
                                                                                'percent': 0.45,
                                                                                'center': {'type': 'Text',
                                                                                           'properties': {
                                                                                               'data': '45%'}},
                                                                                'progressColor': '#FF9800'
                                                                            }
                                                                        }
                                                                    ]
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }

        self._create_component(project, 'HomePage', 'Container', home_content, 1)

    def _create_feature_card(self, title, icon, color):
        """Create a feature card widget"""
        return {
            'type': 'Card',
            'properties': {
                'elevation': 2,
                'child': {
                    'type': 'InkWell',
                    'properties': {
                        'onTap': '() {}',
                        'child': {
                            'type': 'Container',
                            'properties': {
                                'padding': {'all': 16},
                                'child': {
                                    'type': 'Column',
                                    'properties': {
                                        'mainAxisAlignment': 'center',
                                        'children': [
                                            {
                                                'type': 'Icon',
                                                'properties': {
                                                    'icon': icon,
                                                    'size': 48,
                                                    'color': color
                                                }
                                            },
                                            {'type': 'SizedBox', 'properties': {'height': 8}},
                                            {'type': 'Text', 'properties': {'data': title}}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    def _create_gallery_page(self, project):
        """Create gallery page with image carousel"""
        self.stdout.write('   📄 Creating GalleryPage...')

        gallery_content = {
            'child': {
                'type': 'Column',
                'properties': {
                    'children': [
                        # Title
                        {
                            'type': 'Container',
                            'properties': {
                                'padding': {'all': 16},
                                'child': {'type': 'Text', 'properties': {'data': 'Image Gallery',
                                                                         'style': {'fontSize': 24,
                                                                                   'fontWeight': 'bold'}}}
                            }
                        },

                        # Carousel
                        {
                            'type': 'CarouselSlider',
                            'properties': {
                                'options': {
                                    'height': 200,
                                    'autoPlay': True,
                                    'autoPlayInterval': 3000,
                                    'enlargeCenterPage': True
                                },
                                'items': [
                                    {'type': 'Container', 'properties': {'color': '#FF5722', 'child': {'type': 'Center',
                                                                                                       'properties': {
                                                                                                           'child': {
                                                                                                               'type': 'Text',
                                                                                                               'properties': {
                                                                                                                   'data': 'Image 1'}}}}}},
                                    {'type': 'Container', 'properties': {'color': '#4CAF50', 'child': {'type': 'Center',
                                                                                                       'properties': {
                                                                                                           'child': {
                                                                                                               'type': 'Text',
                                                                                                               'properties': {
                                                                                                                   'data': 'Image 2'}}}}}},
                                    {'type': 'Container', 'properties': {'color': '#2196F3', 'child': {'type': 'Center',
                                                                                                       'properties': {
                                                                                                           'child': {
                                                                                                               'type': 'Text',
                                                                                                               'properties': {
                                                                                                                   'data': 'Image 3'}}}}}},
                                ]
                            }
                        },

                        {'type': 'SizedBox', 'properties': {'height': 16}},

                        # Grid of images
                        {
                            'type': 'Expanded',
                            'properties': {
                                'child': {
                                    'type': 'GridView',
                                    'properties': {
                                        'crossAxisCount': 3,
                                        'children': [
                                            {'type': 'Container',
                                             'properties': {'margin': {'all': 4}, 'color': '#E91E63'}},
                                            {'type': 'Container',
                                             'properties': {'margin': {'all': 4}, 'color': '#9C27B0'}},
                                            {'type': 'Container',
                                             'properties': {'margin': {'all': 4}, 'color': '#673AB7'}},
                                            {'type': 'Container',
                                             'properties': {'margin': {'all': 4}, 'color': '#3F51B5'}},
                                            {'type': 'Container',
                                             'properties': {'margin': {'all': 4}, 'color': '#2196F3'}},
                                            {'type': 'Container',
                                             'properties': {'margin': {'all': 4}, 'color': '#00BCD4'}},
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }

        self._create_component(project, 'GalleryPage', 'Container', gallery_content, 2)

    def _create_camera_page(self, project):
        """Create camera page"""
        self.stdout.write('   📄 Creating CameraPage...')

        camera_content = {
            'child': {
                'type': 'Center',
                'properties': {
                    'child': {
                        'type': 'Column',
                        'properties': {
                            'mainAxisAlignment': 'center',
                            'children': [
                                {
                                    'type': 'Icon',
                                    'properties': {
                                        'icon': 'Icons.camera_alt',
                                        'size': 100,
                                        'color': 'grey'
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 24}},
                                {'type': 'Text', 'properties': {'data': 'Camera Preview', 'style': {'fontSize': 24}}},
                                {'type': 'SizedBox', 'properties': {'height': 16}},
                                {
                                    'type': 'Row',
                                    'properties': {
                                        'mainAxisAlignment': 'center',
                                        'children': [
                                            {
                                                'type': 'ElevatedButton',
                                                'properties': {
                                                    'onPressed': '() => pickImage(ImageSource.camera)',
                                                    'child': {'type': 'Text', 'properties': {'data': 'Take Photo'}}
                                                }
                                            },
                                            {'type': 'SizedBox', 'properties': {'width': 16}},
                                            {
                                                'type': 'ElevatedButton',
                                                'properties': {
                                                    'onPressed': '() => pickImage(ImageSource.gallery)',
                                                    'child': {'type': 'Text', 'properties': {'data': 'From Gallery'}}
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }

        self._create_component(project, 'CameraPage', 'Container', camera_content, 3)

    def _create_maps_page(self, project):
        """Create maps page"""
        self.stdout.write('   📄 Creating MapsPage...')

        maps_content = {
            'child': {
                'type': 'Stack',
                'properties': {
                    'children': [
                        # Map placeholder
                        {
                            'type': 'Container',
                            'properties': {
                                'color': '#E0E0E0',
                                'child': {
                                    'type': 'Center',
                                    'properties': {
                                        'child': {'type': 'Text', 'properties': {'data': 'Google Maps Placeholder'}}
                                    }
                                }
                            }
                        },
                        # Search bar at top
                        {
                            'type': 'Positioned',
                            'properties': {
                                'top': 16,
                                'left': 16,
                                'right': 16,
                                'child': {
                                    'type': 'Card',
                                    'properties': {
                                        'child': {
                                            'type': 'TextField',
                                            'properties': {
                                                'decoration': {
                                                    'hintText': 'Search location...',
                                                    'prefixIcon': {'type': 'Icon',
                                                                   'properties': {'icon': 'Icons.search'}},
                                                    'border': 'InputBorder.none',
                                                    'contentPadding': {'all': 16}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }

        self._create_component(project, 'MapsPage', 'Container', maps_content, 4)

    def _create_forms_page(self, project):
        """Create forms page with various input widgets"""
        self.stdout.write('   📄 Creating FormsPage...')

        forms_content = {
            'child': {
                'type': 'SingleChildScrollView',
                'properties': {
                    'padding': {'all': 16},
                    'child': {
                        'type': 'Column',
                        'properties': {
                            'crossAxisAlignment': 'stretch',
                            'children': [
                                {'type': 'Text', 'properties': {'data': 'Form Examples',
                                                                'style': {'fontSize': 24, 'fontWeight': 'bold'}}},
                                {'type': 'SizedBox', 'properties': {'height': 24}},

                                # Text fields
                                {
                                    'type': 'TextField',
                                    'properties': {
                                        'decoration': {
                                            'labelText': 'Name',
                                            'border': 'OutlineInputBorder()'
                                        }
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 16}},

                                {
                                    'type': 'TextField',
                                    'properties': {
                                        'decoration': {
                                            'labelText': 'Email',
                                            'border': 'OutlineInputBorder()',
                                            'prefixIcon': {'type': 'Icon', 'properties': {'icon': 'Icons.email'}}
                                        }
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 16}},

                                {
                                    'type': 'TextField',
                                    'properties': {
                                        'obscureText': True,
                                        'decoration': {
                                            'labelText': 'Password',
                                            'border': 'OutlineInputBorder()',
                                            'prefixIcon': {'type': 'Icon', 'properties': {'icon': 'Icons.lock'}}
                                        }
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 24}},

                                # Switches and checkboxes
                                {
                                    'type': 'Card',
                                    'properties': {
                                        'child': {
                                            'type': 'Column',
                                            'properties': {
                                                'children': [
                                                    {
                                                        'type': 'SwitchListTile',
                                                        'properties': {
                                                            'title': {'type': 'Text',
                                                                      'properties': {'data': 'Enable Notifications'}},
                                                            'value': True,
                                                            'onChanged': '(val) {}'
                                                        }
                                                    },
                                                    {'type': 'Divider', 'properties': {}},
                                                    {
                                                        'type': 'CheckboxListTile',
                                                        'properties': {
                                                            'title': {'type': 'Text',
                                                                      'properties': {'data': 'I agree to terms'}},
                                                            'value': False,
                                                            'onChanged': '(val) {}'
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 16}},

                                # Slider
                                {
                                    'type': 'Card',
                                    'properties': {
                                        'child': {
                                            'type': 'Container',
                                            'properties': {
                                                'padding': {'all': 16},
                                                'child': {
                                                    'type': 'Column',
                                                    'properties': {
                                                        'children': [
                                                            {'type': 'Text', 'properties': {'data': 'Volume: 50%'}},
                                                            {
                                                                'type': 'Slider',
                                                                'properties': {
                                                                    'value': 0.5,
                                                                    'onChanged': '(val) {}'
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 24}},

                                # Submit button
                                {
                                    'type': 'ElevatedButton',
                                    'properties': {
                                        'onPressed': '() {}',
                                        'child': {
                                            'type': 'Container',
                                            'properties': {
                                                'padding': {'symmetric': {'vertical': 16}},
                                                'child': {'type': 'Text', 'properties': {'data': 'Submit Form'}}
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }

        self._create_component(project, 'FormsPage', 'Container', forms_content, 5)

    def _create_charts_page(self, project):
        """Create charts page without charts_flutter"""
        self.stdout.write('   📄 Creating ChartsPage...')

        charts_content = {
            'child': {
                'type': 'ListView',
                'properties': {
                    'padding': {'all': 16},
                    'children': [
                        {'type': 'Text',
                         'properties': {'data': 'Data Visualization', 'style': {'fontSize': 24, 'fontWeight': 'bold'}}},
                        {'type': 'SizedBox', 'properties': {'height': 24}},

                        # Simple bar chart using containers
                        {
                            'type': 'Card',
                            'properties': {
                                'child': {
                                    'type': 'Container',
                                    'properties': {
                                        'height': 200,
                                        'padding': {'all': 16},
                                        'child': {
                                            'type': 'Row',
                                            'properties': {
                                                'mainAxisAlignment': 'spaceEvenly',
                                                'crossAxisAlignment': 'end',
                                                'children': [
                                                    self._create_bar(0.3, '#4CAF50'),
                                                    self._create_bar(0.6, '#2196F3'),
                                                    self._create_bar(0.8, '#FF9800'),
                                                    self._create_bar(0.4, '#9C27B0'),
                                                    self._create_bar(0.7, '#F44336'),
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        {'type': 'SizedBox', 'properties': {'height': 16}},

                        # Stats cards
                        {
                            'type': 'Row',
                            'properties': {
                                'children': [
                                    self._create_stat_card('Sales', '$12.5K', '#4CAF50'),
                                    {'type': 'SizedBox', 'properties': {'width': 16}},
                                    self._create_stat_card('Users', '1,234', '#2196F3')
                                ]
                            }
                        }
                    ]
                }
            }
        }

        self._create_component(project, 'ChartsPage', 'Container', charts_content, 6)

    def _create_bar(self, height_fraction, color):
        """Create a simple bar for chart"""
        return {
            'type': 'Expanded',
            'properties': {
                'child': {
                    'type': 'Container',
                    'properties': {
                        'height': 150 * height_fraction,
                        'margin': {'horizontal': 4},
                        'decoration': {
                            'color': color,
                            'borderRadius': {'top': 8}
                        }
                    }
                }
            }
        }

    def _create_stat_card(self, title, value, color):
        """Create a statistics card"""
        return {
            'type': 'Expanded',
            'properties': {
                'child': {
                    'type': 'Card',
                    'properties': {
                        'child': {
                            'type': 'Container',
                            'properties': {
                                'padding': {'all': 16},
                                'child': {
                                    'type': 'Column',
                                    'properties': {
                                        'children': [
                                            {'type': 'Text', 'properties': {'data': title, 'style': {'color': 'grey'}}},
                                            {'type': 'SizedBox', 'properties': {'height': 8}},
                                            {'type': 'Text', 'properties': {'data': value, 'style': {'fontSize': 24,
                                                                                                     'fontWeight': 'bold',
                                                                                                     'color': color}}}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    def _create_profile_page(self, project):
        """Create profile page"""
        self.stdout.write('   📄 Creating ProfilePage...')

        profile_content = {
            'child': {
                'type': 'SingleChildScrollView',
                'properties': {
                    'child': {
                        'type': 'Column',
                        'properties': {
                            'children': [
                                            # Profile header
                                            {
                                                'type': 'Container',
                                                'properties': {
                                                    'color': '#2196F3',
                                                    'padding': {'all': 32},
                                                    'child': {
                                                        'type': 'Column',
                                                        'properties': {
                                                            'children': [
                                                                {
                                                                    'type': 'CircleAvatar',
                                                                    'properties': {
                                                                        'radius': 50,
                                                                        'backgroundColor': 'white',
                                                                        'child': {'type': 'Text',
                                                                                  'properties': {'data': 'DU',
                                                                                                 'style': {
                                                                                                     'fontSize': 36}}}
                                                                    }
                                                                },
                                                                {'type': 'SizedBox', 'properties': {'height': 16}},
                                                                {'type': 'Text', 'properties': {'data': 'Demo User',
                                                                                                'style': {
                                                                                                    'fontSize': 24,
                                                                                                    'color': 'white',
                                                                                                    'fontWeight': 'bold'}}},
                                                                {'type': 'Text',
                                                                 'properties': {'data': 'demo@example.com',
                                                                                'style': {'color': 'white'}}}
                                                            ]
                                                        }
                                                    }
                                                }
                                            },

                                {
                                    'type': 'ListView',
                                    'properties': {
                                        'shrinkWrap': True,
                                        'physics': 'NeverScrollableScrollPhysics()',
                                        'children': [
                                            self._create_profile_item('Edit Profile', 'Icons.edit'),
                                            self._create_profile_item('Change Password', 'Icons.lock'),
                                            self._create_profile_item('Payment Methods', 'Icons.credit_card'),
                                            self._create_profile_item('Order History', 'Icons.history'),
                                            self._create_profile_item('Notifications', 'Icons.notifications'),
                                            self._create_profile_item('Privacy', 'Icons.privacy_tip'),
                                        ]
                                    }
                                }
        ]
        }
        }
        }
        }
        }

        self._create_component(project, 'ProfilePage', 'Container', profile_content, 7)

    def _create_profile_item(self, title, icon):
        """Create profile list item"""
        return {
            'type': 'ListTile',
            'properties': {
                'leading': {'type': 'Icon', 'properties': {'icon': icon}},
                'title': {'type': 'Text', 'properties': {'data': title}},
                'trailing': {'type': 'Icon', 'properties': {'icon': 'Icons.arrow_forward_ios', 'size': 16}},
                'onTap': '() {}'
            }
        }

    def _create_settings_page(self, project):
        """Create settings page"""
        self.stdout.write('   📄 Creating SettingsPage...')

        settings_content = {
            'child': {
                'type': 'ListView',
                'properties': {
                    'children': [
                        {
                            'type': 'Container',
                            'properties': {
                                'padding': {'all': 16},
                                'child': {'type': 'Text', 'properties': {'data': 'Settings', 'style': {'fontSize': 24,
                                                                                                       'fontWeight': 'bold'}}}
                            }
                        },

                        # General settings
                        {
                            'type': 'Card',
                            'properties': {
                                'margin': {'horizontal': 16, 'vertical': 8},
                                'child': {
                                    'type': 'Column',
                                    'properties': {
                                        'children': [
                                            {
                                                'type': 'ListTile',
                                                'properties': {
                                                    'title': {'type': 'Text', 'properties': {'data': 'General',
                                                                                             'style': {
                                                                                                 'fontWeight': 'bold'}}}
                                                }
                                            },
                                            {'type': 'Divider', 'properties': {}},
                                            {
                                                'type': 'SwitchListTile',
                                                'properties': {
                                                    'title': {'type': 'Text', 'properties': {'data': 'Dark Mode'}},
                                                    'subtitle': {'type': 'Text',
                                                                 'properties': {'data': 'Use dark theme'}},
                                                    'value': False,
                                                    'onChanged': '(val) {}'
                                                }
                                            },
                                            {
                                                'type': 'ListTile',
                                                'properties': {
                                                    'title': {'type': 'Text', 'properties': {'data': 'Language'}},
                                                    'subtitle': {'type': 'Text', 'properties': {'data': 'English'}},
                                                    'trailing': {'type': 'Icon',
                                                                 'properties': {'icon': 'Icons.arrow_forward_ios',
                                                                                'size': 16}},
                                                    'onTap': '() {}'
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }

        self._create_component(project, 'SettingsPage', 'Container', settings_content, 8)

    def _create_about_page(self, project):
        """Create about page"""
        self.stdout.write('   📄 Creating AboutPage...')

        about_content = {
            'child': {
                'type': 'Center',
                'properties': {
                    'child': {
                        'type': 'Padding',
                        'properties': {
                            'padding': {'all': 32},
                            'child': {
                                'type': 'Column',
                                'properties': {
                                    'mainAxisAlignment': 'center',
                                    'children': [
                                        {
                                            'type': 'Icon',
                                            'properties': {
                                                'icon': 'Icons.flutter_dash',
                                                'size': 100,
                                                'color': '#2196F3'
                                            }
                                        },
                                        {'type': 'SizedBox', 'properties': {'height': 24}},
                                        {'type': 'Text', 'properties': {'data': 'Super Demo App',
                                                                        'style': {'fontSize': 28,
                                                                                  'fontWeight': 'bold'}}},
                                        {'type': 'SizedBox', 'properties': {'height': 8}},
                                        {'type': 'Text', 'properties': {'data': 'Version 1.0.0'}},
                                        {'type': 'SizedBox', 'properties': {'height': 32}},
                                        {'type': 'Text', 'properties': {'data': 'Built with Flutter Dynamic Generator',
                                                                        'style': {'fontSize': 16}}},
                                        {'type': 'SizedBox', 'properties': {'height': 8}},
                                        {'type': 'Text', 'properties': {'data': 'Showcasing all widget capabilities'}}
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }

        self._create_component(project, 'AboutPage', 'Container', about_content, 9)

    def _create_component(self, project, page_name, widget_type_name, properties, order):
        """Helper to create a component with proper HTML decoding"""
        import html

        def decode_deeply(obj):
            if isinstance(obj, str):
                decoded = obj
                for _ in range(5):
                    prev = decoded
                    decoded = html.unescape(decoded)
                    if decoded == prev:
                        break
                return decoded
            elif isinstance(obj, dict):
                return {decode_deeply(k): decode_deeply(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [decode_deeply(item) for item in obj]
            else:
                return obj

        try:
            widget_type = WidgetType.objects.get(name=widget_type_name)
            clean_properties = decode_deeply(properties)

            return DynamicPageComponent.objects.create(
                project=project,
                page_name=page_name,
                widget_type=widget_type,
                properties=clean_properties,
                order=order
            )
        except WidgetType.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'   ⚠️ Widget type {widget_type_name} not found'))

    def _print_summary(self, project):
        """Print summary of created app"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📱 COMPREHENSIVE DEMO APP CREATED')
        self.stdout.write('=' * 60)

        self.stdout.write(f'\n🏗️ Project: {project.name}')
        self.stdout.write(f'📦 Package: {project.package_name}')

        pages = project.dynamic_components.values_list('page_name', flat=True).distinct()
        self.stdout.write(f'\n📄 Pages ({pages.count()}):')
        for page in pages:
            component_count = project.dynamic_components.filter(page_name=page).count()
            self.stdout.write(f'   • {page}: {component_count} components')

        self.stdout.write('\n✨ Features:')
        self.stdout.write('   • Navigation drawer with multiple sections')
        self.stdout.write('   • Camera integration ready')
        self.stdout.write('   • Image gallery with carousel')
        self.stdout.write('   • Maps placeholder')
        self.stdout.write('   • Forms with various input types')
        self.stdout.write('   • Charts and data visualization')
        self.stdout.write('   • Profile and settings pages')
        self.stdout.write('   • Speed dial FAB with actions')
        self.stdout.write('   • Progress indicators')
        self.stdout.write('   • Grid and list layouts')

        self.stdout.write('\n🚀 Next Steps:')
        self.stdout.write('   1. Go to Django Admin')
        self.stdout.write('   2. Find your project: ' + project.name)
        self.stdout.write('   3. Click "👁️ Preview" to see the Flutter code')
        self.stdout.write('   4. Click "📦 ZIP" to download')
        self.stdout.write('   5. Click "🔨 Build APK" to create the app')

        self.stdout.write('\n' + '=' * 60)