import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';

/// Manages backend URL configuration.
/// The URL is persisted in SharedPreferences and can be changed in Settings.
/// IMPORTANT: Never hardcode emulator-only addresses here.
class BackendConfig {
  static const String _prefKey = 'backend_url';
  // Default is the production backend hosted on Render.
  static const String defaultUrl = 'https://hinata-m93w.onrender.com';

  static Future<String> getUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_prefKey) ?? defaultUrl;
  }

  static Future<void> setUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKey, url.trim().replaceAll(RegExp(r'/+$'), ''));
  }
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const HinataApp());
}

class HinataApp extends StatelessWidget {
  const HinataApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Hinata AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF69B4),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF69B4),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      themeMode: ThemeMode.system,
      home: const SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Future.delayed(const Duration(milliseconds: 800), () {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const WebViewApp()),
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFF69B4),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              '🌸',
              style: TextStyle(fontSize: 80),
            ),
            const SizedBox(height: 24),
            Text(
              'Hinata AI',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              'AI Companion & Deep Search',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Colors.white70,
                  ),
            ),
            const SizedBox(height: 48),
            const CircularProgressIndicator(color: Colors.white),
          ],
        ),
      ),
    );
  }
}

class WebViewApp extends StatefulWidget {
  const WebViewApp({super.key});

  @override
  State<WebViewApp> createState() => _WebViewAppState();
}

class _WebViewAppState extends State<WebViewApp> {
  late final WebViewController _controller;
  bool _isLoading = true;
  bool _hasError = false;
  double _loadingProgress = 0;
  int _selectedIndex = 0;
  final TextEditingController _urlController = TextEditingController();
  String _currentUrl = '';

  // Backend URL is loaded from SharedPreferences — NOT hardcoded.
  // Configure it in app Settings > Backend URL.
  String _backendUrl = BackendConfig.defaultUrl;

  @override
  void initState() {
    super.initState();
    _loadBackendUrlThenInit();
  }

  Future<void> _loadBackendUrlThenInit() async {
    final url = await BackendConfig.getUrl();
    setState(() => _backendUrl = url);
    _initWebView();
  }

  Future<void> _initWebView() async {
    final controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..addJavaScriptChannel(
        'HinataDeviceBridge',
        onMessageReceived: (JavaScriptMessage message) {
          _handleNativeCommand(message.message);
        },
      )
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (url) {
            setState(() {
              _isLoading = true;
              _hasError = false;
              _currentUrl = url;
            });
          },
          onPageFinished: (url) {
            setState(() {
              _isLoading = false;
              _currentUrl = url;
            });
          },
          onWebResourceError: (error) {
            setState(() => _hasError = true);
          },
          onProgress: (progress) {
            setState(() => _loadingProgress = progress / 100.0);
          },
        ),
      )
      ..loadRequest(Uri.parse(_backendUrl));

    // Enable hybrid composition for Android 9-16 compatibility
    if (controller.platform is AndroidWebViewController) {
      AndroidWebViewController.enableDebugging(true);
      await (controller.platform as AndroidWebViewController)
          .setMediaPlaybackRequiresUserGesture(false);
    }

    if (mounted) {
      setState(() => _controller = controller);
    }
  }

  static const _deviceChannel = MethodChannel('hinata/device_control');

  Future<void> _handleNativeCommand(String messageStr) async {
    try {
      final data = jsonDecode(messageStr);
      final command = data['command'] as String?;
      final args = data['arguments'] as Map<String, dynamic>? ?? {};

      switch (command) {
        case 'android.flashlight':
          final state = args['state'] == 'on';
          await _deviceChannel.invokeMethod('toggleFlashlight', {'state': state});
          break;
        case 'android.volume_up':
          await _deviceChannel.invokeMethod('adjustVolume', {'direction': 'up'});
          break;
        case 'android.volume_down':
          await _deviceChannel.invokeMethod('adjustVolume', {'direction': 'down'});
          break;
        case 'android.media_play':
          await _deviceChannel.invokeMethod('mediaControl', {'action': 'play'});
          break;
        case 'android.media_pause':
          await _deviceChannel.invokeMethod('mediaControl', {'action': 'pause'});
          break;
        case 'android.open_app':
          final pkg = args['package'] as String? ?? args['app_name'] as String? ?? '';
          await _deviceChannel.invokeMethod('openApp', {'packageName': pkg});
          break;
        case 'android.battery_status':
          final int level = await _deviceChannel.invokeMethod('getBatteryStatus');
          await _controller.runJavaScript('if (window.onBatteryStatus) window.onBatteryStatus($level);');
          break;
      }
    } catch (e) {
      debugPrint('Error executing native command: $e');
    }
  }

  Future<bool> _onWillPop() async {
    if (await _controller.canGoBack()) {
      _controller.goBack();
      return false;
    }
    return true;
  }

  void _reload() {
    setState(() => _hasError = false);
    _controller.reload();
  }

  void _onNavTap(int index) {
    setState(() => _selectedIndex = index);
    switch (index) {
      case 0:
        _controller.loadRequest(Uri.parse(_backendUrl));
        break;
      case 1:
        _controller.loadRequest(Uri.parse('$_backendUrl#search'));
        break;
      case 2:
        _controller.loadRequest(Uri.parse('$_backendUrl#memories'));
        break;
    }
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        if (await _controller.canGoBack()) {
          _controller.goBack();
        } else {
          if (context.mounted) Navigator.of(context).pop();
        }
      },
      child: Scaffold(
        body: Stack(
          children: [
            // Main WebView
            if (_controller != WebViewController()) ...[
              WebViewWidget(controller: _controller),
            ],
            // Error state
            if (_hasError)
              Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.cloud_off, size: 64, color: Colors.grey),
                    const SizedBox(height: 16),
                    Text(
                      'Cannot connect',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: 8),
                    const Text('Please check your connection'),
                    const SizedBox(height: 24),
                    FilledButton.icon(
                      onPressed: _reload,
                      icon: const Icon(Icons.refresh),
                      label: const Text('Retry'),
                    ),
                  ],
                ),
              ),
            // Loading progress bar
            if (_isLoading)
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                child: LinearProgressIndicator(
                  value: _loadingProgress,
                  backgroundColor: Colors.transparent,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    Color(0xFFFF69B4),
                  ),
                ),
              ),
          ],
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _selectedIndex,
          onDestinationSelected: _onNavTap,
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.chat_bubble_outline),
              selectedIcon: Icon(Icons.chat_bubble),
              label: 'Chat',
            ),
            NavigationDestination(
              icon: Icon(Icons.search_outlined),
              selectedIcon: Icon(Icons.search),
              label: 'Search',
            ),
            NavigationDestination(
              icon: Icon(Icons.auto_stories_outlined),
              selectedIcon: Icon(Icons.auto_stories),
              label: 'Memories',
            ),
          ],
        ),
      ),
    );
  }
}
