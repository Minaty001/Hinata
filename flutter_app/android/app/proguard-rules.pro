# Hinata AI Proguard Rules

# Keep WebView
-keep class android.webkit.** { *; }

# Keep Flutter
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Keep Kotlin coroutines
-keepclassmembers class kotlinx.coroutines.** { *; }

# Keep app classes
-keep class com.hinata.ai.** { *; }
