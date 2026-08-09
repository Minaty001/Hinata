package com.hinata.ai

import android.os.Bundle
import androidx.multidex.MultiDex
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import android.content.Context
import android.content.Intent
import android.hardware.camera2.CameraManager
import android.media.AudioManager
import android.os.BatteryManager
import android.os.Build
import android.view.KeyEvent

class MainActivity : FlutterActivity() {
    private val CHANNEL = "hinata/device_control"

    override fun onCreate(savedInstanceState: Bundle?) {
        MultiDex.install(this)
        super.onCreate(savedInstanceState)
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "toggleFlashlight" -> {
                    val state = call.argument<Boolean>("state") ?: false
                    val success = toggleFlashlight(state)
                    if (success) {
                        result.success(true)
                    } else {
                        result.error("FLASHLIGHT_ERROR", "Could not toggle flashlight", null)
                    }
                }
                "adjustVolume" -> {
                    val direction = call.argument<String>("direction") ?: "up"
                    val success = adjustVolume(direction)
                    if (success) {
                        result.success(true)
                    } else {
                        result.error("VOLUME_ERROR", "Could not adjust volume", null)
                    }
                }
                "getBatteryStatus" -> {
                    val level = getBatteryStatus()
                    result.success(level)
                }
                "mediaControl" -> {
                    val action = call.argument<String>("action") ?: "play"
                    val success = mediaControl(action)
                    if (success) {
                        result.success(true)
                    } else {
                        result.error("MEDIA_ERROR", "Could not perform media command", null)
                    }
                }
                "openApp" -> {
                    val packageName = call.argument<String>("packageName") ?: ""
                    val success = openApp(packageName)
                    if (success) {
                        result.success(true)
                    } else {
                        result.error("LAUNCH_ERROR", "Could not launch package: $packageName", null)
                    }
                }
                else -> {
                    result.notImplemented()
                }
            }
        }
    }

    private fun toggleFlashlight(state: Boolean): Boolean {
        return try {
            val cameraManager = getSystemService(Context.CAMERA_SERVICE) as CameraManager
            val cameraId = cameraManager.cameraIdList[0]
            cameraManager.setTorchMode(cameraId, state)
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    private fun adjustVolume(direction: String): Boolean {
        return try {
            val audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
            val flags = AudioManager.FLAG_SHOW_UI or AudioManager.FLAG_PLAY_SOUND
            if (direction == "up") {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_RAISE, flags)
            } else {
                audioManager.adjustStreamVolume(AudioManager.STREAM_MUSIC, AudioManager.ADJUST_LOWER, flags)
            }
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    private fun getBatteryStatus(): Int {
        return try {
            val bm = getSystemService(Context.BATTERY_SERVICE) as BatteryManager
            bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        } catch (e: Exception) {
            -1
        }
    }

    private fun mediaControl(action: String): Boolean {
        return try {
            val audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
            val keyCode = when (action) {
                "play" -> KeyEvent.KEYCODE_MEDIA_PLAY
                "pause" -> KeyEvent.KEYCODE_MEDIA_PAUSE
                "next" -> KeyEvent.KEYCODE_MEDIA_NEXT
                else -> return false
            }
            val keyEventDown = KeyEvent(KeyEvent.ACTION_DOWN, keyCode)
            audioManager.dispatchMediaKeyEvent(keyEventDown)
            val keyEventUp = KeyEvent(KeyEvent.ACTION_UP, keyCode)
            audioManager.dispatchMediaKeyEvent(keyEventUp)
            true
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    private fun openApp(packageName: String): Boolean {
        if (packageName.isEmpty()) return false
        return try {
            val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
            if (launchIntent != null) {
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(launchIntent)
                true
            } else {
                false
            }
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }
}
