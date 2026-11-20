import os, shutil, glob

def w(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

os.makedirs("app/src/main/assets", exist_ok=True)
htmls = glob.glob("index.html") or glob.glob("*.html")
if not htmls:
    raise SystemExit("ERROR: no html file in repository root")
shutil.copy(htmls[0], "app/src/main/assets/index.html")

os.makedirs("app/src/main/res/drawable", exist_ok=True)
icon_done = False
for ext in ("png", "jpg", "jpeg", "webp"):
    g = glob.glob("*." + ext)
    if g:
        shutil.copy(g[0], "app/src/main/res/drawable/ic_launcher." + ext)
        icon_done = True
        break
if not icon_done:
    w("app/src/main/res/drawable/ic_launcher.xml", '''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="48dp" android:height="48dp"
    android:viewportWidth="100" android:viewportHeight="100">
    <path android:pathData="M36,60 L12,90" android:strokeColor="#111111" android:strokeWidth="13" android:strokeLineCap="round"/>
    <path android:pathData="M56,40 m-30,0 a30,30 0 1,0 60,0 a30,30 0 1,0 -60,0" android:fillColor="#FFFFFF" android:strokeColor="#111111" android:strokeWidth="11"/>
    <path android:pathData="M46,58 L42,66" android:strokeColor="#DD2222" android:strokeWidth="6" android:strokeLineCap="round"/>
    <path android:pathData="M63,58 L67,66" android:strokeColor="#DD2222" android:strokeWidth="6" android:strokeLineCap="round"/>
</vector>
''')

w("settings.gradle.kts", '''pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
}
dependencyResolutionManagement {
    repositories { google(); mavenCentral() }
}
rootProject.name = "Poryadok"
include(":app")
''')

w("build.gradle.kts", '''plugins {
    id("com.android.application") version "8.5.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.24" apply false
}
''')

w("gradle.properties", '''org.gradle.jvmargs=-Xmx2048m
android.useAndroidX=true
''')

w("app/build.gradle.kts", '''plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "ru.poryadok.app"
    compileSdk = 34
    defaultConfig {
        applicationId = "ru.poryadok.app"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "2.1"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("androidx.webkit:webkit:1.10.0")
}
''')

w("app/src/main/AndroidManifest.xml", '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-feature android:name="android.hardware.camera" android:required="false" />
    <application android:label="ПорЯдок" android:icon="@drawable/ic_launcher"
        android:theme="@android:style/Theme.Material.Light.NoActionBar">
        <activity android:name=".MainActivity" android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden|screenLayout|smallestScreenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
''')

w("app/src/main/java/ru/poryadok/app/MainActivity.kt", '''package ru.poryadok.app

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.webkit.PermissionRequest
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.webkit.WebViewAssetLoader

class MainActivity : Activity() {
    private var uploadMessage: ValueCallback<Array<Uri>>? = null
    private lateinit var web: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this)
        setContentView(web)
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.CAMERA), 100)
        }
        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.settings.mediaPlaybackRequiresUserGesture = false
        web.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest) =
                assetLoader.shouldInterceptRequest(request)
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                request.grant(request.resources)
            }
            override fun onShowFileChooser(webView: WebView, filePathCallback: ValueCallback<Array<Uri>>, fileChooserParams: FileChooserParams): Boolean {
                uploadMessage = filePathCallback
                val intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                intent.type = "image/*"
                startActivityForResult(Intent.createChooser(intent, "Выбрать изображение"), 1)
                return true
            }
        }
        web.loadUrl("https://appassets.androidplatform.net/assets/index.html")
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 1) {
            val res = if (data != null && data.data != null) arrayOf(data.data!!) else null
            uploadMessage?.onReceiveValue(res)
            uploadMessage = null
        }
    }
}
''')

print("Project generated")
