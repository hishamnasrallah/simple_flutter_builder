# generator/management/commands/create_beautiful_app.py
# Create a beautiful app with Home, Profile, Settings pages and navigation drawer

from django.core.management.base import BaseCommand
from django.db import transaction
from generator.models import (
    FlutterProject, PubDevPackage, ProjectPackage,
    WidgetType, DynamicPageComponent
)
import json


class Command(BaseCommand):
    help = 'Create a beautiful app with navigation drawer and multiple pages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-name',
            type=str,
            default='Beautiful App',
            help='Name of the project'
        )

    def handle(self, *args, **options):
        project_name = options['project_name']

        self.stdout.write(self.style.SUCCESS(f'🎨 Creating beautiful app: {project_name}\n'))

        with transaction.atomic():
            # Create project
            project, created = FlutterProject.objects.get_or_create(
                name=project_name,
                defaults={
                    'package_name': 'com.example.beautiful_app',
                    'description': 'A beautiful Flutter app with modern UI'
                }
            )

            if not created:
                # Clear existing components
                project.dynamic_components.all().delete()
                self.stdout.write('   🧹 Cleared existing components')

            # Add packages to project
            self._add_packages_to_project(project)

            # Create pages
            self._create_home_page(project)
            self._create_profile_page(project)
            self._create_settings_page(project)
            self._create_main_scaffold(project)

            self.stdout.write(self.style.SUCCESS(f'\n✅ Beautiful app created successfully!'))
            self.stdout.write('\n📱 Your app includes:')
            self.stdout.write('   • Modern HomePage with cards and animations')
            self.stdout.write('   • Profile page with user info')
            self.stdout.write('   • Settings page with switches')
            self.stdout.write('   • Navigation drawer with all pages')
            self.stdout.write('   • Beautiful Material Design')
            self.stdout.write('\n🚀 Next steps:')
            self.stdout.write('   1. Go to Django Admin')
            self.stdout.write('   2. Find your project')
            self.stdout.write('   3. Click "Preview" to see the code')
            self.stdout.write('   4. Click "Build APK" to create the app')

    def _add_packages_to_project(self, project):
        """Add UI packages to project"""
        packages_to_add = [
            'font_awesome_flutter',
            'google_fonts',
            'badges',
            'percent_indicator',
            'shimmer',
            'animated_text_kit',
        ]

        for package_name in packages_to_add:
            try:
                package = PubDevPackage.objects.get(name=package_name)
                ProjectPackage.objects.get_or_create(
                    project=project,
                    package=package,
                    defaults={'version': package.version}
                )
            except PubDevPackage.DoesNotExist:
                pass

    def _create_main_scaffold(self, project):
        """Create main scaffold with drawer"""
        order = 0

        # Scaffold with Drawer
        scaffold = self._create_component(project, 'MainPage', 'Scaffold', {
            'drawer': {
                'type': 'Drawer',
                'properties': {
                    'child': {
                        'type': 'ListView',
                        'properties': {
                            'padding': {'all': 0},
                            'children': [
                                # Drawer Header
                                {
                                    'type': 'UserAccountsDrawerHeader',
                                    'properties': {
                                        'accountName': {
                                            'type': 'Text',
                                            'properties': {
                                                'data': 'John Doe',
                                                'style': {'fontSize': 18, 'fontWeight': 'bold', 'color': 'white'}
                                            }
                                        },
                                        'accountEmail': {
                                            'type': 'Text',
                                            'properties': {
                                                'data': 'john.doe@example.com',
                                                'style': {'color': 'white'}
                                            }
                                        },
                                        'currentAccountPicture': {
                                            'type': 'CircleAvatar',
                                            'properties': {
                                                'backgroundColor': 'white',
                                                'child': {
                                                    'type': 'Text',
                                                    'properties': {
                                                        'data': 'JD',
                                                        'style': {'fontSize': 40, 'color': '#2196F3'}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                # Home Item
                                {
                                    'type': 'ListTile',
                                    'properties': {
                                        'leading': {
                                            'type': 'Icon',
                                            'properties': {'icon': 'Icons.home', 'color': '#2196F3'}
                                        },
                                        'title': {
                                            'type': 'Text',
                                            'properties': {'data': 'Home'}
                                        },
                                        'onTap': '() => Navigator.pushNamed(context, "/home")'
                                    }
                                },
                                # Profile Item
                                {
                                    'type': 'ListTile',
                                    'properties': {
                                        'leading': {
                                            'type': 'Icon',
                                            'properties': {'icon': 'Icons.person', 'color': '#4CAF50'}
                                        },
                                        'title': {
                                            'type': 'Text',
                                            'properties': {'data': 'Profile'}
                                        },
                                        'onTap': '() => Navigator.pushNamed(context, "/profile")'
                                    }
                                },
                                # Settings Item
                                {
                                    'type': 'ListTile',
                                    'properties': {
                                        'leading': {
                                            'type': 'Icon',
                                            'properties': {'icon': 'Icons.settings', 'color': '#FF9800'}
                                        },
                                        'title': {
                                            'type': 'Text',
                                            'properties': {'data': 'Settings'}
                                        },
                                        'onTap': '() => Navigator.pushNamed(context, "/settings")'
                                    }
                                },
                                # Divider
                                {'type': 'Divider', 'properties': {}},
                                # Logout
                                {
                                    'type': 'ListTile',
                                    'properties': {
                                        'leading': {
                                            'type': 'Icon',
                                            'properties': {'icon': 'Icons.logout', 'color': '#F44336'}
                                        },
                                        'title': {
                                            'type': 'Text',
                                            'properties': {'data': 'Logout'}
                                        },
                                        'onTap': '() {}'
                                    }
                                }
                            ]
                        }
                    }
                }
            },
            'appBar': {
                'type': 'AppBar',
                'properties': {
                    'title': {
                        'type': 'Text',
                        'properties': {'data': 'Beautiful App'}
                    },
                    'backgroundColor': '#2196F3'
                }
            },
            'body': {
                'type': 'Container',
                'properties': {
                    'child': {
                        'type': 'Center',
                        'properties': {
                            'child': {
                                'type': 'Text',
                                'properties': {'data': 'Welcome to Beautiful App'}
                            }
                        }
                    }
                }
            }
        }, order)

    def _create_home_page(self, project):
        """Create beautiful home page"""
        self.stdout.write('   📄 Creating HomePage...')
        order = 0

        # Main container with gradient
        self._create_component(project, 'HomePage', 'Container', {
            'decoration': {
                'gradient': {
                    'type': 'LinearGradient',
                    'colors': ['#667eea', '#764ba2'],
                    'begin': 'Alignment.topLeft',
                    'end': 'Alignment.bottomRight'
                }
            },
            'child': {
                'type': 'SafeArea',
                'properties': {
                    'child': {
                        'type': 'SingleChildScrollView',
                        'properties': {
                            'padding': {'all': 20},
                            'child': {
                                'type': 'Column',
                                'properties': {
                                    'crossAxisAlignment': 'stretch',
                                    'children': [
                                        # Welcome Card with Animation
                                        {
                                            'type': 'Card',
                                            'properties': {
                                                'elevation': 8,
                                                'shape': {
                                                    'type': 'RoundedRectangleBorder',
                                                    'borderRadius': 16
                                                },
                                                'child': {
                                                    'type': 'Container',
                                                    'properties': {
                                                        'padding': {'all': 24},
                                                        'child': {
                                                            'type': 'Column',
                                                            'properties': {
                                                                'children': [
                                                                    {
                                                                        'type': 'AnimatedTextKit',
                                                                        'properties': {
                                                                            'animatedTexts': [
                                                                                {'type': 'TypewriterAnimatedText',
                                                                                 'text': 'Welcome Back!', 'speed': 100}
                                                                            ],
                                                                            'totalRepeatCount': 1
                                                                        }
                                                                    },
                                                                    {'type': 'SizedBox', 'properties': {'height': 16}},
                                                                    {
                                                                        'type': 'Text',
                                                                        'properties': {
                                                                            'data': 'Your dashboard is ready',
                                                                            'style': {'fontSize': 16, 'color': 'grey'}
                                                                        }
                                                                    }
                                                                ]
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        {'type': 'SizedBox', 'properties': {'height': 20}},

                                        # Stats Row
                                        {
                                            'type': 'Row',
                                            'properties': {
                                                'mainAxisAlignment': 'spaceBetween',
                                                'children': [
                                                    # Stat Card 1
                                                    {
                                                        'type': 'Expanded',
                                                        'properties': {
                                                            'child': {
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
                                                                                        {
                                                                                            'type': 'FaIcon',
                                                                                            'properties': {
                                                                                                'icon': 'FontAwesomeIcons.chartLine',
                                                                                                'color': '#4CAF50',
                                                                                                'size': 30
                                                                                            }
                                                                                        },
                                                                                        {'type': 'SizedBox',
                                                                                         'properties': {'height': 8}},
                                                                                        {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': '2,345',
                                                                                                'style': {
                                                                                                    'fontSize': 24,
                                                                                                    'fontWeight': 'bold'}
                                                                                            }
                                                                                        },
                                                                                        {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': 'Sales',
                                                                                                'style': {
                                                                                                    'fontSize': 14,
                                                                                                    'color': 'grey'}
                                                                                            }
                                                                                        }
                                                                                    ]
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    },
                                                    {'type': 'SizedBox', 'properties': {'width': 16}},
                                                    # Stat Card 2
                                                    {
                                                        'type': 'Expanded',
                                                        'properties': {
                                                            'child': {
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
                                                                                        {
                                                                                            'type': 'FaIcon',
                                                                                            'properties': {
                                                                                                'icon': 'FontAwesomeIcons.users',
                                                                                                'color': '#2196F3',
                                                                                                'size': 30
                                                                                            }
                                                                                        },
                                                                                        {'type': 'SizedBox',
                                                                                         'properties': {'height': 8}},
                                                                                        {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': '1,234',
                                                                                                'style': {
                                                                                                    'fontSize': 24,
                                                                                                    'fontWeight': 'bold'}
                                                                                            }
                                                                                        },
                                                                                        {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': 'Users',
                                                                                                'style': {
                                                                                                    'fontSize': 14,
                                                                                                    'color': 'grey'}
                                                                                            }
                                                                                        }
                                                                                    ]
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        },
                                        {'type': 'SizedBox', 'properties': {'height': 20}},

                                        # Progress Section
                                        {
                                            'type': 'Card',
                                            'properties': {
                                                'elevation': 4,
                                                'child': {
                                                    'type': 'Container',
                                                    'properties': {
                                                        'padding': {'all': 20},
                                                        'child': {
                                                            'type': 'Column',
                                                            'properties': {
                                                                'children': [
                                                                    {
                                                                        'type': 'Text',
                                                                        'properties': {
                                                                            'data': 'Today\'s Progress',
                                                                            'style': {'fontSize': 20,
                                                                                      'fontWeight': 'bold'}
                                                                        }
                                                                    },
                                                                    {'type': 'SizedBox', 'properties': {'height': 20}},
                                                                    {
                                                                        'type': 'CircularPercentIndicator',
                                                                        'properties': {
                                                                            'radius': 100,
                                                                            'percent': 0.75,
                                                                            'center': {
                                                                                'type': 'Text',
                                                                                'properties': {
                                                                                    'data': '75%',
                                                                                    'style': {'fontSize': 24,
                                                                                              'fontWeight': 'bold'}
                                                                                }
                                                                            },
                                                                            'progressColor': '#4CAF50'
                                                                        }
                                                                    }
                                                                ]
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        },
                                        {'type': 'SizedBox', 'properties': {'height': 20}},

                                        # Action Buttons
                                        {
                                            'type': 'Row',
                                            'properties': {
                                                'mainAxisAlignment': 'spaceEvenly',
                                                'children': [
                                                    {
                                                        'type': 'ElevatedButton',
                                                        'properties': {
                                                            'onPressed': '() {}',
                                                            'style': {
                                                                'backgroundColor': '#FF5722',
                                                                'padding': {'horizontal': 24, 'vertical': 12}
                                                            },
                                                            'child': {
                                                                'type': 'Row',
                                                                'properties': {
                                                                    'children': [
                                                                        {
                                                                            'type': 'FaIcon',
                                                                            'properties': {
                                                                                'icon': 'FontAwesomeIcons.plus',
                                                                                'size': 16,
                                                                                'color': 'white'
                                                                            }
                                                                        },
                                                                        {'type': 'SizedBox',
                                                                         'properties': {'width': 8}},
                                                                        {
                                                                            'type': 'Text',
                                                                            'properties': {'data': 'Add New'}
                                                                        }
                                                                    ]
                                                                }
                                                            }
                                                        }
                                                    },
                                                    {
                                                        'type': 'ElevatedButton',
                                                        'properties': {
                                                            'onPressed': '() {}',
                                                            'style': {
                                                                'backgroundColor': '#2196F3',
                                                                'padding': {'horizontal': 24, 'vertical': 12}
                                                            },
                                                            'child': {
                                                                'type': 'Row',
                                                                'properties': {
                                                                    'children': [
                                                                        {
                                                                            'type': 'FaIcon',
                                                                            'properties': {
                                                                                'icon': 'FontAwesomeIcons.download',
                                                                                'size': 16,
                                                                                'color': 'white'
                                                                            }
                                                                        },
                                                                        {'type': 'SizedBox',
                                                                         'properties': {'width': 8}},
                                                                        {
                                                                            'type': 'Text',
                                                                            'properties': {'data': 'Download'}
                                                                        }
                                                                    ]
                                                                }
                                                            }
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
        }, order)

    def _create_profile_page(self, project):
        """Create profile page"""
        self.stdout.write('   📄 Creating ProfilePage...')
        order = 0

        self._create_component(project, 'ProfilePage', 'Container', {
            'decoration': {
                'gradient': {
                    'type': 'LinearGradient',
                    'colors': ['#667eea', '#764ba2'],
                    'begin': 'Alignment.topCenter',
                    'end': 'Alignment.bottomCenter'
                }
            },
            'child': {
                'type': 'SafeArea',
                'properties': {
                    'child': {
                        'type': 'SingleChildScrollView',
                        'properties': {
                            'child': {
                                'type': 'Column',
                                'properties': {
                                    'children': [
                                        # Profile Header
                                        {
                                            'type': 'Container',
                                            'properties': {
                                                'padding': {'all': 32},
                                                'child': {
                                                    'type': 'Column',
                                                    'properties': {
                                                        'children': [
                                                            {
                                                                'type': 'CircleAvatar',
                                                                'properties': {
                                                                    'radius': 60,
                                                                    'backgroundColor': 'white',
                                                                    'child': {
                                                                        'type': 'Text',
                                                                        'properties': {
                                                                            'data': 'JD',
                                                                            'style': {'fontSize': 48,
                                                                                      'color': '#764ba2'}
                                                                        }
                                                                    }
                                                                }
                                                            },
                                                            {'type': 'SizedBox', 'properties': {'height': 16}},
                                                            {
                                                                'type': 'Text',
                                                                'properties': {
                                                                    'data': 'John Doe',
                                                                    'style': {'fontSize': 28, 'fontWeight': 'bold',
                                                                              'color': 'white'}
                                                                }
                                                            },
                                                            {
                                                                'type': 'Text',
                                                                'properties': {
                                                                    'data': 'john.doe@example.com',
                                                                    'style': {'fontSize': 16, 'color': 'white'}
                                                                }
                                                            },
                                                            {'type': 'SizedBox', 'properties': {'height': 8}},
                                                            {
                                                                'type': 'Badge',
                                                                'properties': {
                                                                    'badgeContent': {
                                                                        'type': 'Text',
                                                                        'properties': {
                                                                            'data': 'PRO',
                                                                            'style': {'color': 'white', 'fontSize': 10}
                                                                        }
                                                                    },
                                                                    'badgeColor': '#4CAF50',
                                                                    'child': {
                                                                        'type': 'Text',
                                                                        'properties': {
                                                                            'data': 'Premium Member',
                                                                            'style': {'color': 'white'}
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        ]
                                                    }
                                                }
                                            }
                                        },

                                        # Profile Info Cards
                                        {
                                            'type': 'Container',
                                            'properties': {
                                                'padding': {'horizontal': 20},
                                                'child': {
                                                    'type': 'Column',
                                                    'properties': {
                                                        'children': [
                                                            # Stats Card
                                                            {
                                                                'type': 'Card',
                                                                'properties': {
                                                                    'elevation': 4,
                                                                    'child': {
                                                                        'type': 'Container',
                                                                        'properties': {
                                                                            'padding': {'all': 16},
                                                                            'child': {
                                                                                'type': 'Row',
                                                                                'properties': {
                                                                                    'mainAxisAlignment': 'spaceAround',
                                                                                    'children': [
                                                                                        {
                                                                                            'type': 'Column',
                                                                                            'properties': {
                                                                                                'children': [
                                                                                                    {
                                                                                                        'type': 'Text',
                                                                                                        'properties': {
                                                                                                            'data': '152',
                                                                                                            'style': {
                                                                                                                'fontSize': 24,
                                                                                                                'fontWeight': 'bold',
                                                                                                                'color': '#2196F3'}
                                                                                                        }
                                                                                                    },
                                                                                                    {
                                                                                                        'type': 'Text',
                                                                                                        'properties': {
                                                                                                            'data': 'Posts',
                                                                                                            'style': {
                                                                                                                'color': 'grey'}
                                                                                                        }
                                                                                                    }
                                                                                                ]
                                                                                            }
                                                                                        },
                                                                                        {
                                                                                            'type': 'Column',
                                                                                            'properties': {
                                                                                                'children': [
                                                                                                    {
                                                                                                        'type': 'Text',
                                                                                                        'properties': {
                                                                                                            'data': '2.5k',
                                                                                                            'style': {
                                                                                                                'fontSize': 24,
                                                                                                                'fontWeight': 'bold',
                                                                                                                'color': '#4CAF50'}
                                                                                                        }
                                                                                                    },
                                                                                                    {
                                                                                                        'type': 'Text',
                                                                                                        'properties': {
                                                                                                            'data': 'Followers',
                                                                                                            'style': {
                                                                                                                'color': 'grey'}
                                                                                                        }
                                                                                                    }
                                                                                                ]
                                                                                            }
                                                                                        },
                                                                                        {
                                                                                            'type': 'Column',
                                                                                            'properties': {
                                                                                                'children': [
                                                                                                    {
                                                                                                        'type': 'Text',
                                                                                                        'properties': {
                                                                                                            'data': '486',
                                                                                                            'style': {
                                                                                                                'fontSize': 24,
                                                                                                                'fontWeight': 'bold',
                                                                                                                'color': '#FF9800'}
                                                                                                        }
                                                                                                    },
                                                                                                    {
                                                                                                        'type': 'Text',
                                                                                                        'properties': {
                                                                                                            'data': 'Following',
                                                                                                            'style': {
                                                                                                                'color': 'grey'}
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
                                                            },
                                                            {'type': 'SizedBox', 'properties': {'height': 16}},

                                                            # Info List
                                                            {
                                                                'type': 'Card',
                                                                'properties': {
                                                                    'elevation': 4,
                                                                    'child': {
                                                                        'type': 'Column',
                                                                        'properties': {
                                                                            'children': [
                                                                                {
                                                                                    'type': 'ListTile',
                                                                                    'properties': {
                                                                                        'leading': {
                                                                                            'type': 'FaIcon',
                                                                                            'properties': {
                                                                                                'icon': 'FontAwesomeIcons.phone',
                                                                                                'color': '#2196F3',
                                                                                                'size': 20
                                                                                            }
                                                                                        },
                                                                                        'title': {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': 'Phone'}
                                                                                        },
                                                                                        'subtitle': {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': '+1 234 567 8900'}
                                                                                        }
                                                                                    }
                                                                                },
                                                                                {'type': 'Divider', 'properties': {}},
                                                                                {
                                                                                    'type': 'ListTile',
                                                                                    'properties': {
                                                                                        'leading': {
                                                                                            'type': 'FaIcon',
                                                                                            'properties': {
                                                                                                'icon': 'FontAwesomeIcons.locationDot',
                                                                                                'color': '#FF5722',
                                                                                                'size': 20
                                                                                            }
                                                                                        },
                                                                                        'title': {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': 'Location'}
                                                                                        },
                                                                                        'subtitle': {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': 'New York, USA'}
                                                                                        }
                                                                                    }
                                                                                },
                                                                                {'type': 'Divider', 'properties': {}},
                                                                                {
                                                                                    'type': 'ListTile',
                                                                                    'properties': {
                                                                                        'leading': {
                                                                                            'type': 'FaIcon',
                                                                                            'properties': {
                                                                                                'icon': 'FontAwesomeIcons.briefcase',
                                                                                                'color': '#9C27B0',
                                                                                                'size': 20
                                                                                            }
                                                                                        },
                                                                                        'title': {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': 'Work'}
                                                                                        },
                                                                                        'subtitle': {
                                                                                            'type': 'Text',
                                                                                            'properties': {
                                                                                                'data': 'Software Developer'}
                                                                                        }
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
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }, order)

    def _create_settings_page(self, project):
        """Create settings page"""
        self.stdout.write('   📄 Creating SettingsPage...')
        order = 0

        self._create_component(project, 'SettingsPage', 'Container', {
            'color': '#F5F5F5',
            'child': {
                'type': 'SafeArea',
                'properties': {
                    'child': {
                        'type': 'ListView',
                        'properties': {
                            'padding': {'all': 16},
                            'children': [
                                # Settings Header
                                {
                                    'type': 'Text',
                                    'properties': {
                                        'data': 'Settings',
                                        'style': {'fontSize': 32, 'fontWeight': 'bold'}
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 24}},

                                # Account Section
                                {
                                    'type': 'Text',
                                    'properties': {
                                        'data': 'ACCOUNT',
                                        'style': {'fontSize': 14, 'color': 'grey', 'fontWeight': 'bold'}
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 8}},
                                {
                                    'type': 'Card',
                                    'properties': {
                                        'child': {
                                            'type': 'Column',
                                            'properties': {
                                                'children': [
                                                    {
                                                        'type': 'ListTile',
                                                        'properties': {
                                                            'leading': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.person',
                                                                               'color': '#2196F3'}
                                                            },
                                                            'title': {
                                                                'type': 'Text',
                                                                'properties': {'data': 'Edit Profile'}
                                                            },
                                                            'trailing': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.arrow_forward_ios',
                                                                               'size': 16}
                                                            }
                                                        }
                                                    },
                                                    {'type': 'Divider', 'properties': {'height': 1}},
                                                    {
                                                        'type': 'ListTile',
                                                        'properties': {
                                                            'leading': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.security',
                                                                               'color': '#4CAF50'}
                                                            },
                                                            'title': {
                                                                'type': 'Text',
                                                                'properties': {'data': 'Privacy'}
                                                            },
                                                            'trailing': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.arrow_forward_ios',
                                                                               'size': 16}
                                                            }
                                                        }
                                                    },
                                                    {'type': 'Divider', 'properties': {'height': 1}},
                                                    {
                                                        'type': 'ListTile',
                                                        'properties': {
                                                            'leading': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.lock', 'color': '#FF9800'}
                                                            },
                                                            'title': {
                                                                'type': 'Text',
                                                                'properties': {'data': 'Change Password'}
                                                            },
                                                            'trailing': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.arrow_forward_ios',
                                                                               'size': 16}
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 24}},

                                # Preferences Section
                                {
                                    'type': 'Text',
                                    'properties': {
                                        'data': 'PREFERENCES',
                                        'style': {'fontSize': 14, 'color': 'grey', 'fontWeight': 'bold'}
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 8}},
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
                                                            'title': {
                                                                'type': 'Text',
                                                                'properties': {'data': 'Push Notifications'}
                                                            },
                                                            'subtitle': {
                                                                'type': 'Text',
                                                                'properties': {
                                                                    'data': 'Receive push notifications',
                                                                    'style': {'fontSize': 12, 'color': 'grey'}
                                                                }
                                                            },
                                                            'value': True,
                                                            'activeColor': '#2196F3',
                                                            'onChanged': '(value) {}'
                                                        }
                                                    },
                                                    {'type': 'Divider', 'properties': {'height': 1}},
                                                    {
                                                        'type': 'SwitchListTile',
                                                        'properties': {
                                                            'title': {
                                                                'type': 'Text',
                                                                'properties': {'data': 'Dark Mode'}
                                                            },
                                                            'subtitle': {
                                                                'type': 'Text',
                                                                'properties': {
                                                                    'data': 'Enable dark theme',
                                                                    'style': {'fontSize': 12, 'color': 'grey'}
                                                                }
                                                            },
                                                            'value': False,
                                                            'activeColor': '#2196F3',
                                                            'onChanged': '(value) {}'
                                                        }
                                                    },
                                                    {'type': 'Divider', 'properties': {'height': 1}},
                                                    {
                                                        'type': 'ListTile',
                                                        'properties': {
                                                            'leading': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.language',
                                                                               'color': '#9C27B0'}
                                                            },
                                                            'title': {
                                                                'type': 'Text',
                                                                'properties': {'data': 'Language'}
                                                            },
                                                            'subtitle': {
                                                                'type': 'Text',
                                                                'properties': {'data': 'English'}
                                                            },
                                                            'trailing': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.arrow_forward_ios',
                                                                               'size': 16}
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 24}},

                                # About Section
                                {
                                    'type': 'Text',
                                    'properties': {
                                        'data': 'ABOUT',
                                        'style': {'fontSize': 14, 'color': 'grey', 'fontWeight': 'bold'}
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 8}},
                                {
                                    'type': 'Card',
                                    'properties': {
                                        'child': {
                                            'type': 'Column',
                                            'properties': {
                                                'children': [
                                                    {
                                                        'type': 'ListTile',
                                                        'properties': {
                                                            'leading': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.info', 'color': '#607D8B'}
                                                            },
                                                            'title': {
                                                                'type': 'Text',
                                                                'properties': {'data': 'About'}
                                                            },
                                                            'trailing': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.arrow_forward_ios',
                                                                               'size': 16}
                                                            }
                                                        }
                                                    },
                                                    {'type': 'Divider', 'properties': {'height': 1}},
                                                    {
                                                        'type': 'ListTile',
                                                        'properties': {
                                                            'leading': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.star', 'color': '#FFC107'}
                                                            },
                                                            'title': {
                                                                'type': 'Text',
                                                                'properties': {'data': 'Rate Us'}
                                                            },
                                                            'trailing': {
                                                                'type': 'Icon',
                                                                'properties': {'icon': 'Icons.arrow_forward_ios',
                                                                               'size': 16}
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                },
                                {'type': 'SizedBox', 'properties': {'height': 32}},

                                # Logout Button
                                {
                                    'type': 'Center',
                                    'properties': {
                                        'child': {
                                            'type': 'ElevatedButton',
                                            'properties': {
                                                'onPressed': '() {}',
                                                'style': {
                                                    'backgroundColor': '#F44336',
                                                    'padding': {'horizontal': 48, 'vertical': 16}
                                                },
                                                'child': {
                                                    'type': 'Text',
                                                    'properties': {
                                                        'data': 'LOGOUT',
                                                        'style': {'fontSize': 16, 'fontWeight': 'bold'}
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
        }, order)

    def _create_component(self, project, page_name, widget_type_name, properties, order):
        """Helper to create a component"""
        try:
            widget_type = WidgetType.objects.get(name=widget_type_name)
            return DynamicPageComponent.objects.create(
                project=project,
                page_name=page_name,
                widget_type=widget_type,
                properties=properties,
                order=order
            )
        except WidgetType.DoesNotExist:
            self.stdout.write(f'   ⚠️ Widget type {widget_type_name} not found')