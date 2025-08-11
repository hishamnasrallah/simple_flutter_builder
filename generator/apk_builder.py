# ===========================================
# File: generator/apk_builder.py (WINDOWS UPDATES)
# ===========================================

import os
import subprocess
import tempfile
import shutil
import time
import json
import platform
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


class FlutterAPKBuilder:
    def __init__(self):
        self.flutter_sdk_path = getattr(settings, 'FLUTTER_SDK_PATH', None)
        self.android_sdk_path = getattr(settings, 'ANDROID_SDK_PATH', None)
        self.builds_dir = getattr(settings, 'APK_BUILDS_DIR', 'apk_builds')
        self.is_windows = platform.system() == 'Windows'

        # Ensure builds directory exists
        os.makedirs(self.builds_dir, exist_ok=True)

    def setup_java21_environment(self):
        """Setup environment variables for Java 21 compatibility"""
        # More comprehensive Gradle JVM options for Java 21
        # Java 21 options optimized for Gradle 8.4
        gradle_opts = [
            "-Xmx4096m",
            "-XX:MaxMetaspaceSize=1024m",
            "-Dfile.encoding=UTF-8",
            "-Djava.awt.headless=true",
            "--add-opens=java.base/java.lang=ALL-UNNAMED",
            "--add-opens=java.base/java.util=ALL-UNNAMED",
            "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED",
            "--add-opens=java.prefs/java.util.prefs=ALL-UNNAMED",
            "--add-opens=java.base/java.nio.file=ALL-UNNAMED"
        ]

        os.environ['GRADLE_OPTS'] = ' '.join(gradle_opts)

        # Clear conflicting environment variables
        for var in ['JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS']:
            if var in os.environ:
                del os.environ[var]

        # Set Kotlin daemon JVM options
        kotlin_opts = [
            "-Xmx2048M",
            "--add-opens=java.base/java.util=ALL-UNNAMED",
            "--add-opens=java.base/java.lang=ALL-UNNAMED",
            "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED"
        ]

        os.environ['KOTLIN_DAEMON_JVM_OPTIONS'] = ' '.join(kotlin_opts)

        return True

    def create_gradle_wrapper_files(self, project_dir):
        """Create Gradle wrapper files with working download URLs"""
        android_dir = os.path.join(project_dir, 'android')
        gradle_dir = os.path.join(android_dir, 'gradle', 'wrapper')
        os.makedirs(gradle_dir, exist_ok=True)

        # Create gradle-wrapper.properties with Gradle 8.4 (full Java 21 support)
        wrapper_properties = '''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-8.5-all.zip
networkTimeout=60000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
'''

        with open(os.path.join(gradle_dir, 'gradle-wrapper.properties'), 'w') as f:
            f.write(wrapper_properties)

    def get_flutter_command(self):
        """Get the correct Flutter command for the platform"""
        if self.is_windows:
            return 'flutter.bat'
        else:
            return 'flutter'

    def check_flutter_installation(self):
        """Check if Flutter SDK is properly installed"""
        try:
            flutter_cmd = self.get_flutter_command()

            result = subprocess.run(
                [flutter_cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=30,
                shell=self.is_windows  # Use shell=True on Windows
            )
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except FileNotFoundError:
            return False, "Flutter command not found. Please install Flutter SDK."
        except subprocess.TimeoutExpired:
            return False, "Flutter command timed out."
        except Exception as e:
            return False, f"Error checking Flutter: {str(e)}"

    def check_android_setup(self):
        """Check if Android SDK and build tools are available"""
        try:
            flutter_cmd = self.get_flutter_command()

            # Check doctor output
            doctor_result = subprocess.run(
                [flutter_cmd, 'doctor'],
                capture_output=True,
                text=True,
                timeout=60,
                shell=self.is_windows
            )

            return True, doctor_result.stdout
        except Exception as e:
            return False, f"Android setup check failed: {str(e)}"

    def create_flutter_project_files(self, project, temp_dir):
        """Create complete Flutter project structure"""
        from .utils import FlutterCodeGenerator

        generator = FlutterCodeGenerator(project)
        project_name = project.name.replace(' ', '_').replace('-', '_').lower()

        # Remove any non-alphanumeric characters except underscore
        import re
        project_name = re.sub(r'[^a-zA-Z0-9_]', '', project_name)

        project_dir = os.path.join(temp_dir, project_name)

        # Create project structure
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'lib'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'android'), exist_ok=True)
        os.makedirs(os.path.join(project_dir, 'android', 'app'), exist_ok=True)

        # Generate pubspec.yaml
        pubspec_content = generator.generate_pubspec_yaml()
        with open(os.path.join(project_dir, 'pubspec.yaml'), 'w', encoding='utf-8') as f:
            f.write(pubspec_content)

        # Generate main.dart
        main_dart_content = generator.generate_main_dart()
        with open(os.path.join(project_dir, 'lib', 'main.dart'), 'w', encoding='utf-8') as f:
            f.write(main_dart_content)

        # Generate Android configuration
        self.generate_android_config(project, project_dir)

        # Create local.properties file
        self.create_local_properties(project_dir)

        # Create Gradle wrapper files with stable download URL
        self.create_gradle_wrapper_files(project_dir)

        return project_dir

    def generate_android_config(self, project, project_dir):
        """Generate Android-specific configuration files"""
        android_dir = os.path.join(project_dir, 'android')
        app_dir = os.path.join(android_dir, 'app')

        # Create build.gradle (app level) - Compatible versions
        app_build_gradle = f'''plugins {{
        id "com.android.application"
        id "org.jetbrains.kotlin.android"
        id "dev.flutter.flutter-gradle-plugin"
    }}

    def localProperties = new Properties()
    def localPropertiesFile = rootProject.file('local.properties')
    if (localPropertiesFile.exists()) {{
        localPropertiesFile.withReader('UTF-8') {{ reader ->
            localProperties.load(reader)
        }}
    }}

    def flutterVersionCode = localProperties.getProperty('flutter.versionCode')
    if (flutterVersionCode == null) {{
        flutterVersionCode = '1'
    }}

    def flutterVersionName = localProperties.getProperty('flutter.versionName')
    if (flutterVersionName == null) {{
        flutterVersionName = '1.0'
    }}

    android {{
        namespace "{project.package_name}"
        compileSdk 34

        compileOptions {{
            sourceCompatibility JavaVersion.VERSION_17
            targetCompatibility JavaVersion.VERSION_17
        }}

        kotlinOptions {{
            jvmTarget = '17'
        }}

        sourceSets {{
            main.java.srcDirs += 'src/main/kotlin'
        }}

        defaultConfig {{
            applicationId "{project.package_name}"
            minSdkVersion 21
            targetSdkVersion 34
            versionCode flutterVersionCode.toInteger()
            versionName flutterVersionName
        }}

        buildTypes {{
            release {{
                signingConfig signingConfigs.debug
            }}
        }}
    }}

    flutter {{
        source '../..'
    }}

    dependencies {{
        implementation "org.jetbrains.kotlin:kotlin-stdlib:1.9.20"
    }}
    '''

        with open(os.path.join(app_dir, 'build.gradle'), 'w', encoding='utf-8') as f:
            f.write(app_build_gradle)

        # Create AndroidManifest.xml with proper v2 embedding (FIXED)
        manifest_content = f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android"
        package="{project.package_name}">

        <uses-permission android:name="android.permission.INTERNET" />

        <application
            android:label="{project.name}"
            android:icon="@mipmap/ic_launcher">
            <activity
                android:name=".MainActivity"
                android:exported="true"
                android:launchMode="singleTop"
                android:theme="@style/LaunchTheme"
                android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
                android:hardwareAccelerated="true"
                android:windowSoftInputMode="adjustResize">
                <meta-data
                  android:name="io.flutter.embedding.android.NormalTheme"
                  android:resource="@style/NormalTheme"
                  />
                <intent-filter>
                    <action android:name="android.intent.action.MAIN"/>
                    <category android:name="android.intent.category.LAUNCHER"/>
                </intent-filter>
            </activity>
            <meta-data
                android:name="flutterEmbedding"
                android:value="2" />
        </application>
    </manifest>
    '''

        manifest_dir = os.path.join(app_dir, 'src', 'main')
        os.makedirs(manifest_dir, exist_ok=True)
        with open(os.path.join(manifest_dir, 'AndroidManifest.xml'), 'w', encoding='utf-8') as f:
            f.write(manifest_content)

        # Create MainActivity.kt
        kotlin_dir = os.path.join(manifest_dir, 'kotlin')
        package_dirs = project.package_name.split('.')
        for package_dir in package_dirs:
            kotlin_dir = os.path.join(kotlin_dir, package_dir)
        os.makedirs(kotlin_dir, exist_ok=True)

        main_activity = f'''package {project.package_name}

    import io.flutter.embedding.android.FlutterActivity

    class MainActivity: FlutterActivity() {{
    }}
    '''

        with open(os.path.join(kotlin_dir, 'MainActivity.kt'), 'w', encoding='utf-8') as f:
            f.write(main_activity)

        # Create project-level build.gradle with compatible versions
        project_build_gradle = '''buildscript {
        ext.kotlin_version = '1.9.20'
        repositories {
            google()
            mavenCentral()
        }

        dependencies {
            classpath 'com.android.tools.build:gradle:8.2.0'
            classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
        }
    }

    allprojects {
        repositories {
            google()
            mavenCentral()
        }
    }

    rootProject.buildDir = '../build'
    subprojects {
        project.buildDir = "${rootProject.buildDir}/${project.name}"
    }
    subprojects {
        project.evaluationDependsOn(':app')
    }

    tasks.register("clean", Delete) {
        delete rootProject.buildDir
    }
    '''

        with open(os.path.join(android_dir, 'build.gradle'), 'w', encoding='utf-8') as f:
            f.write(project_build_gradle)

        # Create gradle.properties (clean formatting)
        gradle_properties = '''org.gradle.jvmargs=-Xmx4096M -XX:MaxMetaspaceSize=1024m -Dfile.encoding=UTF-8 --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED --add-opens=java.prefs/java.util.prefs=ALL-UNNAMED
    android.useAndroidX=true
    android.enableJetifier=true
    org.gradle.daemon=false
    org.gradle.parallel=false
    kotlin.daemon.jvm.options=-Xmx2048M --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.lang=ALL-UNNAMED
    '''

        with open(os.path.join(android_dir, 'gradle.properties'), 'w', encoding='utf-8') as f:
            f.write(gradle_properties)

        # Create settings.gradle with version declarations
        settings_gradle = '''pluginManagement {
        def flutterSdkPath = {
            def properties = new Properties()
            file("local.properties").withInputStream { properties.load(it) }
            def flutterSdkPath = properties.getProperty("flutter.sdk")
            assert flutterSdkPath != null, "flutter.sdk not set in local.properties"
            return flutterSdkPath
        }()

        includeBuild("$flutterSdkPath/packages/flutter_tools/gradle")

        repositories {
            google()
            mavenCentral()
            gradlePluginPortal()
        }
    }

    plugins {
    id "dev.flutter.flutter-gradle-plugin" version "1.0.0" apply false
    id "org.jetbrains.kotlin.android" version "1.9.20" apply false
    }

    include ":app"
    '''

        with open(os.path.join(android_dir, 'settings.gradle'), 'w', encoding='utf-8') as f:
            f.write(settings_gradle)

    def build_apk(self, project, progress_callback=None):
        """Build APK for the Flutter project"""
        try:
            # Check prerequisites
            # Clear Gradle cache first
            cache_cleared, cache_msg = self.clear_gradle_cache()
            if progress_callback:
                progress_callback(f'Cleared Gradle cache: {cache_msg}', 5)

            # Setup Java 21 environment
            self.setup_java21_environment()

            # Check prerequisites
            flutter_ok, flutter_msg = self.check_flutter_installation()
            if not flutter_ok:
                return {
                    'success': False,
                    'error': f'Flutter SDK not available: {flutter_msg}',
                    'apk_path': None
                }

            if progress_callback:
                progress_callback('Checking Flutter installation...', 10)

            # Create temporary directory for build
            with tempfile.TemporaryDirectory() as temp_dir:
                if progress_callback:
                    progress_callback('Creating project files...', 20)

                # Create Flutter project
                project_dir = self.create_flutter_project_files(project, temp_dir)
                flutter_cmd = self.get_flutter_command()

                if progress_callback:
                    progress_callback('Running flutter pub get...', 30)

                # Run flutter pub get
                pub_result = subprocess.run(
                    [flutter_cmd, 'pub', 'get'],
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    shell=self.is_windows
                )

                if pub_result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'Flutter pub get failed: {pub_result.stderr}',
                        'apk_path': None
                    }

                if progress_callback:
                    progress_callback('Building APK...', 50)

                # Build APK with extended timeout for Windows
                build_timeout = getattr(settings, 'BUILD_TIMEOUT', 1200)  # 20 minutes default

                # Create local environment with Java 21 settings
                build_env = os.environ.copy()
                build_env.update({
                    'GRADLE_OPTS': os.environ.get('GRADLE_OPTS', ''),
                    'KOTLIN_DAEMON_JVM_OPTIONS': os.environ.get('KOTLIN_DAEMON_JVM_OPTIONS', ''),
                })

                # Try building APK with retry for network issues
                build_success = False
                last_error = ""

                for attempt in range(3):  # Try up to 3 times
                    if progress_callback:
                        progress_callback(f'Building APK (attempt {attempt + 1})...', 50 + attempt * 15)

                    build_result = subprocess.run(
                        [flutter_cmd, 'build', 'apk', '--release'],
                        cwd=project_dir,
                        capture_output=True,
                        text=True,
                        timeout=build_timeout,
                        shell=self.is_windows,
                        env=build_env
                    )

                    if build_result.returncode == 0:
                        build_success = True
                        break
                    else:
                        last_error = build_result.stderr
                        # If it's a network error, wait and retry
                        if "503" in last_error or "IOException" in last_error:
                            if progress_callback:
                                progress_callback(f'Network error, retrying in 10 seconds...', 60)
                            time.sleep(10)  # Wait 10 seconds before retry
                        else:
                            break  # Non-network error, don't retry

                if not build_success:
                    return {
                        'success': False,
                        'error': f'APK build failed: {last_error}',
                        'apk_path': None
                    }

                if progress_callback:
                    progress_callback('Copying APK file...', 80)

                # Find the built APK
                apk_source = os.path.join(project_dir, 'build', 'app', 'outputs', 'flutter-apk', 'app-release.apk')

                if not os.path.exists(apk_source):
                    return {
                        'success': False,
                        'error': 'APK file not found after build',
                        'apk_path': None
                    }

                # Copy APK to builds directory
                project_name = project.name.replace(' ', '_').replace('-', '_').lower()
                import re
                project_name = re.sub(r'[^a-zA-Z0-9_]', '', project_name)
                timestamp = int(time.time())
                apk_filename = f'{project_name}_{timestamp}.apk'
                apk_destination = os.path.join(self.builds_dir, apk_filename)

                shutil.copy2(apk_source, apk_destination)

                if progress_callback:
                    progress_callback('APK build completed!', 100)

                return {
                    'success': True,
                    'error': None,
                    'apk_path': apk_destination,
                    'apk_filename': apk_filename,
                    'build_output': build_result.stdout
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Build process timed out. Please try again or increase BUILD_TIMEOUT in settings.',
                'apk_path': None
            }
        except Exception as e:
            logger.exception("APK build failed")
            return {
                'success': False,
                'error': f'Unexpected error during build: {str(e)}',
                'apk_path': None
            }

    def clear_gradle_cache(self):
        """Clear Gradle cache completely to avoid Java version conflicts"""
        try:
            gradle_home = os.path.join(os.path.expanduser('~'), '.gradle')

            # Clear caches directory
            caches_dir = os.path.join(gradle_home, 'caches')
            if os.path.exists(caches_dir):
                shutil.rmtree(caches_dir)

            # Clear wrapper directory to force re-download
            wrapper_dir = os.path.join(gradle_home, 'wrapper')
            if os.path.exists(wrapper_dir):
                shutil.rmtree(wrapper_dir)

            # Clear daemon directory
            daemon_dir = os.path.join(gradle_home, 'daemon')
            if os.path.exists(daemon_dir):
                shutil.rmtree(daemon_dir)

            return True, "Gradle cache, wrapper, and daemon cleared completely"
        except Exception as e:
            return False, f"Failed to clear Gradle cache: {str(e)}"

    def create_local_properties(self, project_dir):
        """Create local.properties file with Flutter SDK path"""
        android_dir = os.path.join(project_dir, 'android')

        # Get Flutter SDK path from settings
        flutter_sdk_path = getattr(settings, 'FLUTTER_SDK_PATH', None)
        if not flutter_sdk_path:
            flutter_sdk_path = os.environ.get('FLUTTER_ROOT', 'C:\\flutter')

        # Convert Windows path to use forward slashes for Gradle
        flutter_sdk_path = flutter_sdk_path.replace('\\', '/')

        local_properties = f'''sdk.dir={self.android_sdk_path.replace(chr(92), '/')}
flutter.sdk={flutter_sdk_path}
flutter.buildMode=release
flutter.versionName=1.0.0
flutter.versionCode=1
'''

        with open(os.path.join(android_dir, 'local.properties'), 'w') as f:
            f.write(local_properties)