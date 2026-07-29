import 'package:flutter_test/flutter_test.dart';

import 'package:hinata_ai/main.dart';

void main() {
  testWidgets('App loads with splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(const HinataApp());
    expect(find.text('Hinata AI'), findsOneWidget);
  });
}
