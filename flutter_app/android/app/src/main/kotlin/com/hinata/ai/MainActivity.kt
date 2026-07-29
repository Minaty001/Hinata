package com.hinata.ai

import android.os.Bundle
import androidx.multidex.MultiDex
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        MultiDex.install(this)
        super.onCreate(savedInstanceState)
    }
}
