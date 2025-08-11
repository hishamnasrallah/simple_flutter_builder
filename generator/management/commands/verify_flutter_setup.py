# ===========================================
# File: generator/management/commands/verify_flutter_setup.py
# ===========================================

from django.core.management.base import BaseCommand
from django.conf import settings
import subprocess
import os
import platform


class Command(BaseCommand):
    help = 'Verify Flutter and Android SDK setup for APK building'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Verifying Flutter Setup for APK Building...\n')
        )

        # Platform info
        self.stdout.write(f'💻 Platform: {platform.system()} {platform.release()}')
        self.stdout.write(f'🐍 Python: {platform.python_version()}\n')

        # Check Flutter SDK
        self.check_flutter_sdk()

        # Check Android SDK
        self.check_android_sdk()

        # Check Java
        self.check_java()

        # Test Flutter commands
        self.test_flutter_commands()

        # Test Flutter doctor
        self.test_flutter_doctor()

        # Final recommendation
        self.print_final_status()

    def check_flutter_sdk(self):
        """Verify Flutter SDK installation"""
        self.stdout.write('📱 Checking Flutter SDK...')

        flutter_path = getattr(settings, 'FLUTTER_SDK_PATH', None)
        if not flutter_path:
            self.stdout.write('  ❌ FLUTTER_SDK_PATH not set in settings')
            return False

        self.stdout.write(f'  📁 Flutter path: {flutter_path}')

        if not os.path.exists(flutter_path):
            self.stdout.write('  ❌ Flutter directory does not exist')
            return False

        # Check flutter executable
        if platform.system() == 'Windows':
            flutter_exe = os.path.join(flutter_path, 'bin', 'flutter.bat')
        else:
            flutter_exe = os.path.join(flutter_path, 'bin', 'flutter')

        if os.path.exists(flutter_exe):
            self.stdout.write(f'  ✅ Flutter executable found: {flutter_exe}')
            return True
        else:
            self.stdout.write(f'  ❌ Flutter executable not found: {flutter_exe}')
            return False

    def check_android_sdk(self):
        """Verify Android SDK installation"""
        self.stdout.write('\n🤖 Checking Android SDK...')

        android_path = getattr(settings, 'ANDROID_SDK_PATH', None)
        if not android_path:
            self.stdout.write('  ❌ ANDROID_SDK_PATH not set in settings')
            return False

        self.stdout.write(f'  📁 Android SDK path: {android_path}')

        if not os.path.exists(android_path):
            self.stdout.write('  ❌ Android SDK directory does not exist')
            return False

        # Check command line tools
        cmdline_tools = os.path.join(android_path, 'cmdline-tools', 'latest')
        if os.path.exists(cmdline_tools):
            self.stdout.write(f'  ✅ Command line tools found: {cmdline_tools}')
        else:
            self.stdout.write(f'  ⚠️  Command line tools not found: {cmdline_tools}')

        # Check platform tools
        platform_tools = os.path.join(android_path, 'platform-tools')
        if os.path.exists(platform_tools):
            self.stdout.write(f'  ✅ Platform tools found: {platform_tools}')
        else:
            self.stdout.write(f'  ❌ Platform tools not found: {platform_tools}')

        # Check build tools
        build_tools_dir = os.path.join(android_path, 'build-tools')
        if os.path.exists(build_tools_dir):
            build_tools = os.listdir(build_tools_dir)
            if build_tools:
                self.stdout.write(f'  ✅ Build tools found: {", ".join(build_tools)}')
            else:
                self.stdout.write('  ❌ No build tools versions found')
        else:
            self.stdout.write('  ❌ Build tools directory not found')

        return True

    def check_java(self):
        """Verify Java installation"""
        self.stdout.write('\n☕ Checking Java...')

        java_home = getattr(settings, 'JAVA_HOME', os.environ.get('JAVA_HOME'))
        if java_home:
            self.stdout.write(f'  📁 JAVA_HOME: {java_home}')

            if platform.system() == 'Windows':
                java_exe = os.path.join(java_home, 'bin', 'java.exe')
            else:
                java_exe = os.path.join(java_home, 'bin', 'java')

            if os.path.exists(java_exe):
                self.stdout.write(f'  ✅ Java executable found: {java_exe}')
            else:
                self.stdout.write(f'  ❌ Java executable not found: {java_exe}')
        else:
            self.stdout.write('  ❌ JAVA_HOME not set')

    def test_flutter_commands(self):
        """Test Flutter commands execution"""
        self.stdout.write('\n🧪 Testing Flutter Commands...')

        try:
            # Test flutter --version
            if platform.system() == 'Windows':
                flutter_cmd = 'flutter.bat'
            else:
                flutter_cmd = 'flutter'

            result = subprocess.run(
                [flutter_cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()
            )

            if result.returncode == 0:
                self.stdout.write('  ✅ Flutter --version successful')
                # Extract version info
                version_lines = result.stdout.strip().split('\n')
                for line in version_lines[:3]:  # Show first 3 lines
                    self.stdout.write(f'    {line}')
            else:
                self.stdout.write('  ❌ Flutter --version failed')
                self.stdout.write(f'    Error: {result.stderr}')

        except FileNotFoundError:
            self.stdout.write('  ❌ Flutter command not found in PATH')
        except subprocess.TimeoutExpired:
            self.stdout.write('  ❌ Flutter command timed out')
        except Exception as e:
            self.stdout.write(f'  ❌ Flutter command error: {str(e)}')

    def test_flutter_doctor(self):
        """Test Flutter doctor"""
        self.stdout.write('\n🏥 Running Flutter Doctor...')

        try:
            if platform.system() == 'Windows':
                flutter_cmd = 'flutter.bat'
            else:
                flutter_cmd = 'flutter'

            result = subprocess.run(
                [flutter_cmd, 'doctor', '-v'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                self.stdout.write('  ✅ Flutter doctor completed successfully')
            else:
                self.stdout.write('  ⚠️  Flutter doctor completed with warnings')

            # Show doctor output
            self.stdout.write('  📋 Flutter Doctor Output:')
            for line in result.stdout.split('\n')[:20]:  # Show first 20 lines
                if line.strip():
                    self.stdout.write(f'    {line}')

            if len(result.stdout.split('\n')) > 20:
                self.stdout.write('    ... (output truncated)')

        except Exception as e:
            self.stdout.write(f'  ❌ Flutter doctor error: {str(e)}')

    def print_final_status(self):
        """Print final setup status"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 SETUP STATUS SUMMARY')
        self.stdout.write('=' * 60)

        # Check if everything looks good
        flutter_ok = self.check_flutter_sdk()

        if flutter_ok:
            self.stdout.write('✅ Flutter SDK: Ready')
        else:
            self.stdout.write('❌ Flutter SDK: Not Ready')

        self.stdout.write('\n🚀 Next Steps:')

        if flutter_ok:
            self.stdout.write('1. ✅ Flutter setup looks good!')
            self.stdout.write('2. 🧪 Test APK building: python manage.py setup_test_data')
            self.stdout.write('3. 🔨 Go to Django admin and try building an APK')
            self.stdout.write('4. 📱 If successful, you can download and install APK files!')
        else:
            self.stdout.write('1. ❌ Fix Flutter SDK installation issues above')
            self.stdout.write('2. 🔄 Run this command again to verify')
            self.stdout.write('3. 📚 Check Flutter installation guide: https://flutter.dev/docs/get-started/install')
