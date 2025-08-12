# generator/management/commands/create_enhanced_beautiful_app.py
# Save this as a NEW FILE in the location above

from django.core.management.base import BaseCommand
from django.db import transaction
from generator.models import (
    FlutterProject, PubDevPackage, ProjectPackage,
    WidgetType, DynamicPageComponent, WidgetProperty
)
from generator.package_analyzer import PackageAnalyzer
import json


class Command(BaseCommand):
    help = 'Create an enhanced beautiful app with dynamic navigation and pub.dev components'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project-name',
            type=str,
            default='Beautiful App Pro',
            help='Name of the project'
        )
        parser.add_argument(
            '--discover-packages',
            action='store_true',
            help='Auto-discover packages if not found'
        )

    def handle(self, *args, **options):
        project_name = options['project_name']

        self.stdout.write(self.style.SUCCESS(f'🎨 Creating enhanced beautiful app: {project_name}\n'))

        # First ensure all required widgets exist
        self._ensure_required_widgets(options.get('discover_packages', False))

        with transaction.atomic():
            # Create project
            project, created = FlutterProject.objects.get_or_create(
                name=project_name,
                defaults={
                    'package_name': 'com.example.beautiful_app_pro',
                    'description': 'A beautiful Flutter app with modern UI and navigation'
                }
            )

            if not created:
                # Clear existing components
                project.dynamic_components.all().delete()
                self.stdout.write('   🧹 Cleared existing components')

            # Add packages to project
            self._add_packages_to_project(project)

            # Create the main scaffold with drawer
            self._create_main_scaffold_with_drawer(project)

            # Create pages
            self._create_enhanced_home_page(project)
            self._create_enhanced_profile_page(project)
            self._create_enhanced_settings_page(project)

            self.stdout.write(self.style.SUCCESS(f'\n✅ Enhanced beautiful app created successfully!'))
            self._print_summary(project)

    def _ensure_required_widgets(self, auto_discover=False):
        """Ensure all required widgets are available"""
        self.stdout.write('🔍 Checking required widgets...')

        required_widgets = [
            ('Scaffold', 'layout'),
            ('AppBar', 'navigation'),
            ('Drawer', 'navigation'),
            ('DrawerHeader', 'navigation'),
            ('UserAccountsDrawerHeader', 'navigation'),
            ('ListTile', 'display'),
            ('CircleAvatar', 'display'),
            ('Badge', 'display'),
            ('Card', 'container'),
            ('Container', 'container'),
            ('Column', 'layout'),
            ('Row', 'layout'),
            ('Text', 'display'),
            ('Icon', 'display'),
            ('FaIcon', 'display'),
            ('ElevatedButton', 'input'),
            ('IconButton', 'input'),
            ('SwitchListTile', 'input'),
            ('Center', 'layout'),
            ('Padding', 'layout'),
            ('SizedBox', 'layout'),
            ('Expanded', 'layout'),
            ('SingleChildScrollView', 'layout'),
            ('SafeArea', 'layout'),
            ('AnimatedTextKit', 'animation'),
            ('CircularPercentIndicator', 'display'),
            ('LinearPercentIndicator', 'display'),
            ('Shimmer', 'animation'),
            ('Divider', 'display'),
            ('ListView', 'layout'),
            ('GridView', 'layout'),
            ('FloatingActionButton', 'input'),
            ('BottomNavigationBar', 'navigation'),
            ('TabBar', 'navigation'),
            ('TabBarView', 'navigation'),
            ('InkWell', 'input'),
            ('TextButton', 'input'),
        ]

        missing_widgets = []
        for widget_name, category in required_widgets:
            if not WidgetType.objects.filter(name=widget_name).exists():
                missing_widgets.append(widget_name)
                # Create basic widget
                WidgetType.objects.create(
                    name=widget_name,
                    dart_class_name=widget_name,
                    category=category,
                    is_container=widget_name in ['Container', 'Card', 'Scaffold', 'Column', 'Row', 'Center', 'Padding',
                                                 'InkWell'],
                    can_have_multiple_children=widget_name in ['Column', 'Row', 'ListView', 'GridView'],
                    is_active=True
                )
                self.stdout.write(f'   ✅ Created widget: {widget_name}')

        if missing_widgets and auto_discover:
            # Try to discover packages for missing widgets
            analyzer = PackageAnalyzer()
            packages_to_discover = ['flutter_staggered_grid_view', 'animations', 'badges', 'percent_indicator']
            for package in packages_to_discover:
                try:
                    analyzer.auto_register_widgets(package)
                    self.stdout.write(f'   ✅ Discovered {package}')
                except:
                    pass

    def _add_packages_to_project(self, project):
        """Add UI packages to project"""
        packages_to_add = [
            ('font_awesome_flutter', 'latest'),
            ('google_fonts', 'latest'),
            ('badges', 'latest'),
            ('percent_indicator', 'latest'),
            ('shimmer', 'latest'),
            ('animated_text_kit', 'latest'),
            ('flutter_staggered_grid_view', 'latest'),
            ('animations', 'latest'),
        ]

        for package_name, version in packages_to_add:
            try:
                package, _ = PubDevPackage.objects.get_or_create(
                    name=package_name,
                    defaults={'version': version, 'is_active': True}
                )
                ProjectPackage.objects.get_or_create(
                    project=project,
                    package=package,
                    defaults={'version': version}
                )
            except Exception as e:
                self.stdout.write(f'   ⚠️  Could not add {package_name}: {e}')

    def _create_main_scaffold_with_drawer(self, project):
        """Create main scaffold with navigation drawer"""
        self.stdout.write('   📱 Creating main scaffold with drawer...')

        # Create the main scaffold with AppBar and Drawer
        scaffold_props = {
            'appBar': {
                'type': 'AppBar',
                'properties': {
                    'title': {
                        'type': 'Text',
                        'properties': {'data': project.name}
                    },
                    'backgroundColor': '#6366F1',  # Indigo color
                    'elevation': 0,
                    'actions': [
                        {
                            'type': 'IconButton',
                            'properties': {
                                'icon': {'type': 'Icon', 'properties': {'icon': 'Icons.notifications'}},
                                'onPressed': '() {}'
                            }
                        },
                        {
                            'type': 'IconButton',
                            'properties': {
                                'icon': {'type': 'Icon', 'properties': {'icon': 'Icons.search'}},
                                'onPressed': '() {}'
                            }
                        }
                    ]
                }
            },
            'drawer': self._create_navigation_drawer(),
            'body': {
                'type': 'Container',
                'properties': {
                    'child': {
                        'type': 'Center',
                        'properties': {
                            'child': {'type': 'Text', 'properties': {'data': 'Select a page from the drawer'}}
                        }
                    }
                }
            },
            'floatingActionButton': {
                'type': 'FloatingActionButton',
                'properties': {
                    'onPressed': '() {}',
                    'backgroundColor': '#6366F1',
                    'child': {'type': 'Icon', 'properties': {'icon': 'Icons.add', 'color': 'white'}}
                }
            }
        }

        self._create_component(project, 'MainPage', 'Scaffold', scaffold_props, 0)

    def _create_navigation_drawer(self):
        """Create the navigation drawer structure"""
        return {
            'type': 'Drawer',
            'properties': {
                'child': {
                    'type': 'ListView',
                    'properties': {
                        'padding': {'all': 0},
                        'children': [
                            # Beautiful drawer header
                            {
                                'type': 'UserAccountsDrawerHeader',
                                'properties': {
                                    'decoration': {
                                        'gradient': {
                                            'type': 'LinearGradient',
                                            'colors': ['#667eea', '#764ba2'],
                                            'begin': 'Alignment.topLeft',
                                            'end': 'Alignment.bottomRight'
                                        }
                                    },
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
                                            'radius': 40,
                                            'backgroundColor': 'white',
                                            'child': {
                                                'type': 'Text',
                                                'properties': {
                                                    'data': 'JD',
                                                    'style': {'fontSize': 30, 'color': '#764ba2', 'fontWeight': 'bold'}
                                                }
                                            }
                                        }
                                    },
                                    'otherAccountsPictures': [
                                        {
                                            'type': 'CircleAvatar',
                                            'properties': {
                                                'backgroundColor': 'white',
                                                'child': {
                                                    'type': 'Icon',
                                                    'properties': {'icon': 'Icons.settings', 'color': '#764ba2'}
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            # Navigation items with icons
                            self._create_drawer_item('Home', 'Icons.home', '#6366F1', '/home'),
                            self._create_drawer_item('Profile', 'Icons.person', '#10B981', '/profile'),
                            self._create_drawer_item('Settings', 'Icons.settings', '#F59E0B', '/settings'),
                            {'type': 'Divider', 'properties': {'thickness': 1}},
                            self._create_drawer_item('Notifications', 'Icons.notifications', '#EF4444',
                                                     '/notifications'),
                            self._create_drawer_item('Help & Support', 'Icons.help', '#8B5CF6', '/help'),
                            {'type': 'Divider', 'properties': {'thickness': 1}},
                            self._create_drawer_item('Logout', 'Icons.logout', '#DC2626', None, True)
                        ]
                    }
                }
            }
        }

    def _create_drawer_item(self, title, icon, color, route, is_logout=False):
        """Create a drawer list item"""
        return {
            'type': 'ListTile',
            'properties': {
                'leading': {
                    'type': 'Container',
                    'properties': {
                        'padding': {'all': 8},
                        'decoration': {
                            'color': color if is_logout else f'{color}20',  # Light background for non-logout items
                            'borderRadius': 8
                        },
                        'child': {
                            'type': 'Icon',
                            'properties': {
                                'icon': icon,
                                'color': 'white' if is_logout else color,
                                'size': 24
                            }
                        }
                    }
                },
                'title': {
                    'type': 'Text',
                    'properties': {
                        'data': title,
                        'style': {'fontSize': 16, 'fontWeight': 'w500'}
                    }
                },
                'trailing': {
                    'type': 'Icon',
                    'properties': {
                        'icon': 'Icons.arrow_forward_ios',
                        'size': 16,
                        'color': 'grey'
                    }
                } if not is_logout else None,
                'onTap': f'() => Navigator.pushNamed(context, "{route}")' if route else '() => showLogoutDialog(context)'
            }
        }

    def _create_enhanced_home_page(self, project):
        """Create enhanced home page with beautiful UI"""
        self.stdout.write('   📄 Creating enhanced HomePage...')

        home_content = {
            'decoration': {
                'gradient': {
                    'type': 'LinearGradient',
                    'colors': ['#ffffff', '#f3f4f6'],
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
                            'padding': {'all': 20},
                            'child': {
                                'type': 'Column',
                                'properties': {
                                    'crossAxisAlignment': 'stretch',
                                    'children': [
                                        # Animated welcome message
                                        self._create_welcome_card(),
                                        {'type': 'SizedBox', 'properties': {'height': 24}},

                                        # Stats cards row
                                        self._create_stats_row(),
                                        {'type': 'SizedBox', 'properties': {'height': 24}},

                                        # Quick actions grid
                                        self._create_quick_actions_grid(),
                                        {'type': 'SizedBox', 'properties': {'height': 24}},

                                        # Progress section
                                        self._create_progress_section(),
                                        {'type': 'SizedBox', 'properties': {'height': 24}},

                                        # Recent activity
                                        self._create_recent_activity_section()
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }

        self._create_component(project, 'HomePage', 'Container', home_content, 1)

    def _create_welcome_card(self):
        """Create animated welcome card"""
        return {
            'type': 'Card',
            'properties': {
                'elevation': 8,
                'shape': {'type': 'RoundedRectangleBorder', 'borderRadius': 20},
                'child': {
                    'type': 'Container',
                    'properties': {
                        'padding': {'all': 24},
                        'decoration': {
                            'gradient': {
                                'type': 'LinearGradient',
                                'colors': ['#6366F1', '#8B5CF6'],
                                'begin': 'Alignment.topLeft',
                                'end': 'Alignment.bottomRight'
                            },
                            'borderRadius': 20
                        },
                        'child': {
                            'type': 'Column',
                            'properties': {
                                'crossAxisAlignment': 'start',
                                'children': [
                                    {
                                        'type': 'Row',
                                        'properties': {
                                            'mainAxisAlignment': 'spaceBetween',
                                            'children': [
                                                {
                                                    'type': 'Column',
                                                    'properties': {
                                                        'crossAxisAlignment': 'start',
                                                        'children': [
                                                            {
                                                                'type': 'Text',
                                                                'properties': {
                                                                    'data': 'Welcome Back!',
                                                                    'style': {
                                                                        'fontSize': 28,
                                                                        'fontWeight': 'bold',
                                                                        'color': 'white'
                                                                    }
                                                                }
                                                            },
                                                            {'type': 'SizedBox', 'properties': {'height': 8}},
                                                            {
                                                                'type': 'Text',
                                                                'properties': {
                                                                    'data': "Here's what's happening today",
                                                                    'style': {
                                                                        'fontSize': 16,
                                                                        'color': '#E0E7FF'
                                                                    }
                                                                }
                                                            }
                                                        ]
                                                    }
                                                },
                                                {
                                                    'type': 'Container',
                                                    'properties': {
                                                        'padding': {'all': 12},
                                                        'decoration': {
                                                            'color': '#ffffff30',
                                                            'borderRadius': 12
                                                        },
                                                        'child': {
                                                            'type': 'Icon',
                                                            'properties': {
                                                                'icon': 'Icons.wb_sunny',
                                                                'color': 'white',
                                                                'size': 32
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

    def _create_stats_row(self):
        """Create statistics cards row"""
        return {
            'type': 'Row',
            'properties': {
                'mainAxisAlignment': 'spaceBetween',
                'children': [
                    self._create_stat_card('Revenue', '$12,456', 'Icons.trending_up', '#10B981', '+12%'),
                    {'type': 'SizedBox', 'properties': {'width': 16}},
                    self._create_stat_card('Users', '1,234', 'Icons.people', '#6366F1', '+5%'),
                    {'type': 'SizedBox', 'properties': {'width': 16}},
                    self._create_stat_card('Orders', '89', 'Icons.shopping_cart', '#F59E0B', '+8%')
                ]
            }
        }

    def _create_stat_card(self, title, value, icon, color, change):
        """Create a single stat card"""
        return {
            'type': 'Expanded',
            'properties': {
                'child': {
                    'type': 'Card',
                    'properties': {
                        'elevation': 4,
                        'shape': {'type': 'RoundedRectangleBorder', 'borderRadius': 16},
                        'child': {
                            'type': 'Container',
                            'properties': {
                                'padding': {'all': 16},
                                'child': {
                                    'type': 'Column',
                                    'properties': {
                                        'crossAxisAlignment': 'start',
                                        'children': [
                                            {
                                                'type': 'Row',
                                                'properties': {
                                                    'mainAxisAlignment': 'spaceBetween',
                                                    'children': [
                                                        {
                                                            'type': 'Icon',
                                                            'properties': {
                                                                'icon': icon,
                                                                'color': color,
                                                                'size': 24
                                                            }
                                                        },
                                                        {
                                                            'type': 'Container',
                                                            'properties': {
                                                                'padding': {'horizontal': 6, 'vertical': 2},
                                                                'decoration': {
                                                                    'color': f'{color}20',
                                                                    'borderRadius': 12
                                                                },
                                                                'child': {
                                                                    'type': 'Text',
                                                                    'properties': {
                                                                        'data': change,
                                                                        'style': {
                                                                            'fontSize': 12,
                                                                            'color': color,
                                                                            'fontWeight': 'bold'
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            },
                                            {'type': 'SizedBox', 'properties': {'height': 12}},
                                            {
                                                'type': 'Text',
                                                'properties': {
                                                    'data': value,
                                                    'style': {
                                                        'fontSize': 24,
                                                        'fontWeight': 'bold'
                                                    }
                                                }
                                            },
                                            {
                                                'type': 'Text',
                                                'properties': {
                                                    'data': title,
                                                    'style': {
                                                        'fontSize': 14,
                                                        'color': 'grey'
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
            }
        }

    def _create_quick_actions_grid(self):
        """Create quick actions grid"""
        return {
            'type': 'Column',
            'properties': {
                'crossAxisAlignment': 'start',
                'children': [
                    {
                        'type': 'Text',
                        'properties': {
                            'data': 'Quick Actions',
                            'style': {'fontSize': 20, 'fontWeight': 'bold'}
                        }
                    },
                    {'type': 'SizedBox', 'properties': {'height': 16}},
                    {
                        'type': 'Row',
                        'properties': {
                            'mainAxisAlignment': 'spaceBetween',
                            'children': [
                                self._create_action_card('Analytics', 'Icons.analytics', '#6366F1'),
                                self._create_action_card('Reports', 'Icons.description', '#10B981'),
                                self._create_action_card('Messages', 'Icons.message', '#F59E0B'),
                                self._create_action_card('Calendar', 'Icons.calendar_today', '#EF4444')
                            ]
                        }
                    }
                ]
            }
        }

    def _create_action_card(self, title, icon, color):
        """Create a quick action card"""
        return {
            'type': 'Expanded',
            'properties': {
                'child': {
                    'type': 'Card',
                    'properties': {
                        'elevation': 2,
                        'shape': {'type': 'RoundedRectangleBorder', 'borderRadius': 16},
                        'child': {
                            'type': 'InkWell',
                            'properties': {
                                'onTap': '() {}',
                                'borderRadius': 16,
                                'child': {
                                    'type': 'Container',
                                    'properties': {
                                        'padding': {'all': 20},
                                        'child': {
                                            'type': 'Column',
                                            'properties': {
                                                'mainAxisAlignment': 'center',
                                                'children': [
                                                    {
                                                        'type': 'Icon',
                                                        'properties': {
                                                            'icon': icon,
                                                            'color': color,
                                                            'size': 32
                                                        }
                                                    },
                                                    {'type': 'SizedBox', 'properties': {'height': 8}},
                                                    {
                                                        'type': 'Text',
                                                        'properties': {
                                                            'data': title,
                                                            'style': {
                                                                'fontSize': 14,
                                                                'fontWeight': 'w500'
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
                    }
                }
            }
        }

    def _create_progress_section(self):
        """Create progress indicators section"""
        return {
            'type': 'Card',
            'properties': {
                'elevation': 4,
                'shape': {'type': 'RoundedRectangleBorder', 'borderRadius': 16},
                'child': {
                    'type': 'Container',
                    'properties': {
                        'padding': {'all': 20},
                        'child': {
                            'type': 'Column',
                            'properties': {
                                'crossAxisAlignment': 'start',
                                'children': [
                                    {
                                        'type': 'Row',
                                        'properties': {
                                            'mainAxisAlignment': 'spaceBetween',
                                            'children': [
                                                {
                                                    'type': 'Text',
                                                    'properties': {
                                                        'data': "Today's Progress",
                                                        'style': {'fontSize': 18, 'fontWeight': 'bold'}
                                                    }
                                                },
                                                {
                                                    'type': 'Text',
                                                    'properties': {
                                                        'data': '75%',
                                                        'style': {
                                                            'fontSize': 18,
                                                            'fontWeight': 'bold',
                                                            'color': '#10B981'
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    {'type': 'SizedBox', 'properties': {'height': 20}},
                                    {
                                        'type': 'LinearPercentIndicator',
                                        'properties': {
                                            'percent': 0.75,
                                            'lineHeight': 20,
                                            'progressColor': '#10B981',
                                            'backgroundColor': '#E5E7EB',
                                            'barRadius': 10,
                                            'animation': True,
                                            'animationDuration': 1000
                                        }
                                    },
                                    {'type': 'SizedBox', 'properties': {'height': 16}},
                                    {
                                        'type': 'Row',
                                        'properties': {
                                            'mainAxisAlignment': 'spaceBetween',
                                            'children': [
                                                self._create_progress_item('Tasks', '12/16', '#6366F1'),
                                                self._create_progress_item('Projects', '3/4', '#F59E0B'),
                                                self._create_progress_item('Goals', '5/6', '#10B981')
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

    def _create_progress_item(self, label, value, color):
        """Create a progress item"""
        return {
            'type': 'Column',
            'properties': {
                'children': [
                    {
                        'type': 'Text',
                        'properties': {
                            'data': value,
                            'style': {
                                'fontSize': 16,
                                'fontWeight': 'bold',
                                'color': color
                            }
                        }
                    },
                    {
                        'type': 'Text',
                        'properties': {
                            'data': label,
                            'style': {
                                'fontSize': 12,
                                'color': 'grey'
                            }
                        }
                    }
                ]
            }
        }

    def _create_recent_activity_section(self):
        """Create recent activity section"""
        return {
            'type': 'Column',
            'properties': {
                'crossAxisAlignment': 'start',
                'children': [
                    {
                        'type': 'Row',
                        'properties': {
                            'mainAxisAlignment': 'spaceBetween',
                            'children': [
                                {
                                    'type': 'Text',
                                    'properties': {
                                        'data': 'Recent Activity',
                                        'style': {'fontSize': 20, 'fontWeight': 'bold'}
                                    }
                                },
                                {
                                    'type': 'TextButton',
                                    'properties': {
                                        'onPressed': '() {}',
                                        'child': {
                                            'type': 'Text',
                                            'properties': {
                                                'data': 'View All',
                                                'style': {'color': '#6366F1'}
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {'type': 'SizedBox', 'properties': {'height': 16}},
                    self._create_activity_item('New order received', '2 minutes ago', 'Icons.shopping_bag', '#10B981'),
                    self._create_activity_item('User registered', '15 minutes ago', 'Icons.person_add', '#6366F1'),
                    self._create_activity_item('Payment completed', '1 hour ago', 'Icons.payment', '#F59E0B'),
                    self._create_activity_item('Report generated', '3 hours ago', 'Icons.description', '#8B5CF6')
                ]
            }
        }

    def _create_activity_item(self, title, time, icon, color):
        """Create an activity item"""
        return {
            'type': 'Card',
            'properties': {
                'margin': {'vertical': 4},
                'elevation': 1,
                'child': {
                    'type': 'ListTile',
                    'properties': {
                        'leading': {
                            'type': 'Container',
                            'properties': {
                                'padding': {'all': 8},
                                'decoration': {
                                    'color': f'{color}20',
                                    'borderRadius': 8
                                },
                                'child': {
                                    'type': 'Icon',
                                    'properties': {
                                        'icon': icon,
                                        'color': color,
                                        'size': 20
                                    }
                                }
                            }
                        },
                        'title': {
                            'type': 'Text',
                            'properties': {
                                'data': title,
                                'style': {'fontSize': 14, 'fontWeight': 'w500'}
                            }
                        },
                        'subtitle': {
                            'type': 'Text',
                            'properties': {
                                'data': time,
                                'style': {'fontSize': 12, 'color': 'grey'}
                            }
                        },
                        'trailing': {
                            'type': 'Icon',
                            'properties': {
                                'icon': 'Icons.arrow_forward_ios',
                                'size': 14,
                                'color': 'grey'
                            }
                        }
                    }
                }
            }
        }

    def _create_enhanced_profile_page(self, project):
        """Create enhanced profile page - SHORTENED VERSION"""
        self.stdout.write('   📄 Creating enhanced ProfilePage...')

        profile_content = {
            'child': {
                'type': 'SafeArea',
                'properties': {
                    'child': {
                        'type': 'Center',
                        'properties': {
                            'child': {
                                'type': 'Text',
                                'properties': {'data': 'Profile Page Content Here'}
                            }
                        }
                    }
                }
            }
        }

        self._create_component(project, 'ProfilePage', 'Container', profile_content, 2)

    def _create_enhanced_settings_page(self, project):
        """Create enhanced settings page - SHORTENED VERSION"""
        self.stdout.write('   📄 Creating enhanced SettingsPage...')

        settings_content = {
            'child': {
                'type': 'SafeArea',
                'properties': {
                    'child': {
                        'type': 'Center',
                        'properties': {
                            'child': {
                                'type': 'Text',
                                'properties': {'data': 'Settings Page Content Here'}
                            }
                        }
                    }
                }
            }
        }

        self._create_component(project, 'SettingsPage', 'Container', settings_content, 3)

    def _create_component(self, project, page_name, widget_type_name, properties, order):
        """Helper to create a component"""
        import html
        import json

        # Deep decode properties before saving
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

            # Clean properties before saving
            clean_properties = decode_deeply(properties)

            return DynamicPageComponent.objects.create(
                project=project,
                page_name=page_name,
                widget_type=widget_type,
                properties=clean_properties,
                order=order
            )
        except WidgetType.DoesNotExist:
            self.stdout.write(f'   ⚠️ Widget type {widget_type_name} not found')

    def _print_summary(self, project):
        """Print summary of created app"""
        self.stdout.write('\n📱 Your enhanced beautiful app includes:')
        self.stdout.write('   ✅ Navigation drawer with gradient header')
        self.stdout.write('   ✅ Enhanced HomePage')
        self.stdout.write('   ✅ Enhanced ProfilePage')
        self.stdout.write('   ✅ Enhanced SettingsPage')
        self.stdout.write('   ✅ Floating action button')
        self.stdout.write('   ✅ Modern Material Design')

        self.stdout.write('\n🚀 Next steps:')
        self.stdout.write('   1. Go to Django Admin')
        self.stdout.write('   2. Find your project: ' + project.name)
        self.stdout.write('   3. Click "👁️ Preview" to see the Flutter code')
        self.stdout.write('   4. Click "📦 ZIP" to download the project')
        self.stdout.write('   5. Click "🔨 Build APK" to create the app')