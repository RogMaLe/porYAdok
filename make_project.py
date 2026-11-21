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
for f in glob.glob("*"):
    if not os.path.isfile(f):
        continue
    try:
        head = open(f, "rb").read(12)
    except Exception:
        continue
    ext = None
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        ext = "png"
    elif head[:3] == b"\xff\xd8\xff":
        ext = "jpg"
    elif head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        ext = "webp"
    if ext:
        shutil.copy(f, "app/src/main/res/drawable/ic_launcher." + ext)
        icon_done = True
        break
if not icon_done:
    w("app/src/main/res/drawable/ic_launcher.xml", '''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="48dp" android:height="48dp"
    android:viewportWidth="100" android:viewportHeight="100">
    <path android:pathData="M36,60 L12,90" android:strokeColor="#111111" android:strokeWidth="13" android:strokeLineCap="round"/>
    <path android:pathData="M56,40 m-30,0 a30,30 0 1,0 60,0 a30,30 0 1,0 -60,0" android:fillColor="#FFFFFF" android:strokeColor="#111111" android:strokeWidth="11"/>
    <path android:pathData="M46,58 L42,66" android:strokeColor="#DD2222" android:strokeWidth="6" android:strokeLineCap="round"/>
    <path android:pathData="M63,58 L67,66" android:strokeColor="#DD2222" android:strokeWidth="6" stroke-linecap="round"/>
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
        versionCode = 2
        versionName = "2.4"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
    implementation("androidx.webkit:webkit:1.10.0")
    implementation("androidx.core:core-ktx:1.12.0")
}
''')

w("app/src/main/AndroidManifest.xml", '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-feature android:name="android.hardware.camera" android:required="false" />
    <application android:label="ПорЯдок" android:icon="@drawable/ic_launcher"
        android:theme="@android:style/Theme.Material.Light.NoActionBar">
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="ru.poryadok.app.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
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

w("app/src/main/res/xml/file_paths.xml", '''<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="http://schemas.android.com/apk/res/android">
    <cache-path name="cam" path="/" />
</paths>
''')

w("app/src/main/java/ru/poryadok/app/MainActivity.kt", '''package ru.poryadok.app

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.webkit.PermissionRequest
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.core.content.FileProvider
import androidx.webkit.WebViewAssetLoader
import java.io.File

class MainActivity : Activity() {
    private var uploadMessage: ValueCallback<Array<Uri>>? = null
    private var web: WebView? = null
    private var camUri: Uri? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val w = WebView(this)
        web = w
        setContentView(w)
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.CAMERA), 100)
        }
        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()
        w.settings.javaScriptEnabled = true
        w.settings.domStorageEnabled = true
        w.settings.mediaPlaybackRequiresUserGesture = false
        w.webViewClient = object : WebViewClient() {
            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
                return assetLoader.shouldInterceptRequest(request.url)
            }
        }
        w.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                request.grant(request.resources)
            }
            override fun onShowFileChooser(webView: WebView, filePathCallback: ValueCallback<Array<Uri>>, fileChooserParams: WebChromeClient.FileChooserParams): Boolean {
                uploadMessage = filePathCallback
                if (fileChooserParams.isCaptureEnabled) {
                    val f = File(cacheDir, "cam_" + System.currentTimeMillis() + ".jpg")
                    camUri = FileProvider.getUriForFile(this@MainActivity, "ru.poryadok.app.fileprovider", f)
                    val i = Intent(MediaStore.ACTION_IMAGE_CAPTURE)
                    i.putExtra(MediaStore.EXTRA_OUTPUT, camUri)
                    startActivityForResult(i, 2)
                } else {
                    val i = Intent(Intent.ACTION_GET_CONTENT)
                    i.addCategory(Intent.CATEGORY_OPENABLE)
                    i.type = "image/*"
                    startActivityForResult(Intent.createChooser(i, "Choose file"), 1)
                }
                return true
            }
        }
        w.loadUrl("https://appassets.androidplatform.net/assets/index.html")
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 1) {
            val res = if (data != null && data.data != null) arrayOf(data.data!!) else null
            uploadMessage?.onReceiveValue(res)
            uploadMessage = null
        } else if (requestCode == 2) {
            val u = camUri
            if (resultCode == RESULT_OK && u != null) {
                uploadMessage?.onReceiveValue(arrayOf(u))
            } else {
                uploadMessage?.onReceiveValue(null)
            }
            uploadMessage = null
            camUri = null
        }
    }
}
''')

print("Project generated")
