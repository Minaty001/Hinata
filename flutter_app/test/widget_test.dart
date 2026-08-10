import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hinata_ai/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('App loads with splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(const HinataApp());
    expect(find.text('Hinata AI'), findsOneWidget);
    // The splash schedules an 800ms navigation timer. Dispose the tree and
    // advance the clock so that timer fires harmlessly (its callback checks
    // `mounted`); otherwise the test framework fails with '!timersPending'.
    await tester.pumpWidget(const SizedBox());
    await tester.pump(const Duration(milliseconds: 900));
  });

  group('Device Control MethodChannel Tests', () {
    const channel = MethodChannel('hinata/device_control');
    final log = <MethodCall>[];

    setUp(() {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall methodCall) async {
        log.add(methodCall);
        if (methodCall.method == 'getBatteryStatus') {
          return 85;
        }
        return true;
      });
      log.clear();
    });

    tearDown(() {
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, null);
    });

    test('Mock MethodChannel receives correct calls', () async {
      // Direct invoke call simulation
      final battery = await channel.invokeMethod<int>('getBatteryStatus');
      expect(battery, 85);
      expect(log.first.method, 'getBatteryStatus');

      await channel.invokeMethod('toggleFlashlight', {'state': true});
      expect(log.last.method, 'toggleFlashlight');
      expect(log.last.arguments['state'], true);
    });
  });

  group('BackendConfig', () {
    test('default URL points to the Render production backend', () {
      expect(BackendConfig.defaultUrl, 'https://hinata-m93w.onrender.com');
    });
  });
}
