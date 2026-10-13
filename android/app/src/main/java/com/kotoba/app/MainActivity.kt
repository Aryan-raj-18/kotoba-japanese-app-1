package com.kotoba.app

import android.Manifest
import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.util.Log
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.PermissionRequest
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.RenderProcessGoneDetail
import android.webkit.WebResourceError
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.core.graphics.Insets
import android.graphics.Color
import java.io.File
import java.net.Proxy
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.Lifecycle
import androidx.core.content.ContextCompat
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale
import org.json.JSONObject
import org.json.JSONArray

/**
 * Hosts the whole app as a single full-screen WebView pointed at a
 * Flask server that this same process starts locally via Chaquopy
 * (Python-for-Android). Nothing here talks to the network - the
 * "server" is just Python code running inside this app, listening on
 * the loopback address so the WebView can load it like any other page.
 */
class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "Kotoba"
        private val nativeSessionToken = java.util.UUID.randomUUID().toString()

        // Process-wide, deliberately NOT a per-Activity field. Android can
        // destroy and recreate this Activity while the process (and the
        // Flask server thread inside it) stays alive: back-then-reopen, the
        // reminder notification, fold/unfold, font or locale changes. Each
        // fresh onCreate() used to start a second server on port 5000, which
        // dies with "Address already in use" and - because it happened on a
        // bare Thread - took the whole app down with it.
        @Volatile
        private var serverThread: Thread? = null
        @Volatile private var serverStartupFailed = false
    }

    private lateinit var webView: WebView
    private val serverUrl = "http://127.0.0.1:5000/"
    private val healthUrl = "http://127.0.0.1:5000/__health"
    private val handler = Handler(Looper.getMainLooper())
    @Volatile private var startupGeneration = 0
    @Volatile private var hideStatusBar = false
    private var displayDark = false
    private var displayBackground = "#F4F5FF"
    private var lessonsLoaded = false
    private var rendererGone = false
    private var startupWatchdog: Runnable? = null
    private val startupTimeoutMs = 30_000L
    @Volatile private var introStartedAt = 0L
    @Volatile private var introSkipped = false

    // Bridges the page's <input type="file"> (wallpaper upload) to the
    // system photo picker. A plain WebView never shows a picker on its
    // own for file inputs - that only happens once a WebChromeClient
    // implements onShowFileChooser, below. Must be registered before
    // the activity reaches STARTED, so it's a property, not something
    // created lazily inside the callback.
    private var pendingFileChooserCallback: ValueCallback<Array<Uri>>? = null
    private val fileChooserLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            val callback = pendingFileChooserCallback
            pendingFileChooserCallback = null
            if (callback == null) return@registerForActivityResult

            if (result.resultCode != Activity.RESULT_OK) {
                callback.onReceiveValue(null)
                return@registerForActivityResult
            }
            val data = result.data
            val clip = data?.clipData
            val uris: Array<Uri> = when {
                clip != null -> Array(clip.itemCount) { i -> clip.getItemAt(i).uri }
                data?.data != null -> arrayOf(data.data!!)
                else -> emptyArray()
            }
            callback.onReceiveValue(if (uris.isEmpty()) null else uris)
        }

    // Android 13+ (API 33) requires runtime consent to post notifications
    // at all. Below that this permission is granted automatically at
    // install time, so requesting it there is a harmless no-op.
    // pendingReminderAction runs either right away (permission already
    // granted, or not needed pre-33) or once the user answers the
    // system prompt - either way the alarm still gets scheduled even
    // on "deny", since a silenced notification is a smaller problem
    // than a reminder that silently never got armed.
    private var pendingReminderAction: (() -> Unit)? = null
    private val notificationPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) {
            pendingReminderAction?.invoke()
            pendingReminderAction = null
        }

    // WebRTC microphone requests from the local WebView must pass both
    // Android's runtime permission gate and WebView's PermissionRequest.
    // We never grant camera or other protected WebView resources here.
    private var pendingAudioPermissionRequest: PermissionRequest? = null
    private val microphonePermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            val request = pendingAudioPermissionRequest
            pendingAudioPermissionRequest = null
            if (request == null) return@registerForActivityResult
            if (granted) {
                request.grant(arrayOf(PermissionRequest.RESOURCE_AUDIO_CAPTURE))
            } else {
                request.deny()
            }
        }

    private lateinit var speechBridge: SpeechBridge
    private var voiceRecognizer: SpeechRecognizer? = null
    private var voiceRequestId = ""
    private var voicePermissionInFlight = false
    private var pendingVoiceLanguage: String? = null
    private var pendingVoiceAfterPermission = false
    private val voiceMicrophonePermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            voicePermissionInFlight = false
            val language = pendingVoiceLanguage
            val requestId = voiceRequestId
            val shouldStart = pendingVoiceAfterPermission
            pendingVoiceLanguage = null
            pendingVoiceAfterPermission = false
            if (!shouldStart) return@registerForActivityResult
            if (granted) {
                startVoiceRecognition(language, requestId)
            } else {
                sendVoiceError("Microphone permission is needed for voice search.")
            }
        }

    /** Called from [ReminderBridge] before scheduling/showing anything
     *  notification-related, so the OS prompt (Android 13+ only) has a
     *  chance to appear first. */
    fun requestNotificationPermissionThen(action: () -> Unit) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
            action()
            return
        }
        val granted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED
        if (granted) {
            action()
        } else {
            pendingReminderAction = action
            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        rememberKanjiIntent(intent)
        if (pendingKanjiPath == null) pendingKanjiPath = savedInstanceState?.getString("pendingKanjiPath")
            ?.takeIf { it.matches(Regex("kanji/[0-9]+\\?from=kanji&level=N[1-5]")) }
        setContentView(R.layout.activity_main)


        webView = findViewById(R.id.webview)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        val container = findViewById<View>(R.id.content_container)
        ViewCompat.setOnApplyWindowInsetsListener(container) { view, insets ->
            val types = WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout()
            val safe = insets.getInsets(types)
            view.setPadding(safe.left, safe.top, safe.right, safe.bottom)
            // The parent already reserves these pixels. Keep IME updates intact.
            WindowInsetsCompat.Builder(insets).setInsets(types, Insets.NONE).build()
        }
        val displayPrefs = getSharedPreferences("kotoba-display", MODE_PRIVATE)
        hideStatusBar = displayPrefs.getBoolean("hideStatusBar", false)
        displayDark = displayPrefs.getBoolean("dark", isSystemDark())
        val defaultBackground = if (displayDark) "#0D1525" else "#F4F5FF"
        displayBackground = displayPrefs.getString("background", defaultBackground) ?: defaultBackground
        applyDisplayPreferences()
        ViewCompat.requestApplyInsets(container)
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            private var checkingPage = false
            override fun handleOnBackPressed() {
                if (checkingPage) return
                checkingPage = true
                webView.evaluateJavascript("Boolean(window.KotobaNavigation && window.KotobaNavigation.handleBack())") { consumed ->
                    checkingPage = false
                    if (consumed != "true") {
                        if (webView.canGoBack()) webView.goBack()
                        else { isEnabled = false; onBackPressedDispatcher.onBackPressed(); isEnabled = true }
                    }
                }
            }
        })
        configureSmoothRendering()
        webView.settings.javaScriptEnabled = true
        webView.settings.domStorageEnabled = true

        // The page synthesises its own sound effects with the Web Audio
        // API. Android blocks audio until a user gesture by default,
        // which would swallow the first chime of every session.
        webView.settings.mediaPlaybackRequiresUserGesture = false

        // Match the WebView's own backdrop to the system light/dark
        // setting so there's no white flash before the page paints.
        webView.setBackgroundColor(Color.parseColor(displayBackground))

        webView.webViewClient = KotobaWebViewClient()
        webView.webChromeClient = KotobaWebChromeClient()
        // Exposes window.KotobaNative.{scheduleReminder,cancelReminder} to
        // the page's settings panel (see static/js/reminder.js). Only the
        // app-bundled page ever runs in this WebView, so there's no
        // untrusted-page risk in exposing it.
        webView.addJavascriptInterface(ReminderBridge(this), "KotobaNative")
        webView.addJavascriptInterface(KanjiNotificationBridge(this), "KotobaKanjiNotificationNative")

        // Native Japanese TTS gives vocabulary, grammar, story and dialogue
        // playback an offline path inside the APK. The JavaScript layer uses
        // this bridge first and falls back to browser speechSynthesis on web.
        speechBridge = SpeechBridge()
        webView.addJavascriptInterface(speechBridge, "KotobaSpeechNative")

        // Search fields use this native recognizer inside the Android WebView.
        // Browser builds fall back to the Web Speech API in voice-search.js.
        webView.addJavascriptInterface(VoiceRecognitionBridge(), "KotobaVoiceRecognitionNative")

        webView.addJavascriptInterface(BackupBridge(), "KotobaBackupNative")
        webView.addJavascriptInterface(StartupBridge(), "KotobaStartupNative")
        webView.addJavascriptInterface(DisplayBridge(), "KotobaDisplayNative")
        requestHighRefreshRate()

        beginStartup()
    }

    /**
     * Keep WebView compositing on the GPU and treat its renderer as
     * foreground-important while the app is visible. Android normally
     * enables hardware acceleration for modern apps, but making it explicit
     * avoids OEM/theme fallbacks which can turn CSS transforms and scrolling
     * into expensive software paints. The renderer priority is waived when
     * WebView is not visible so this doesn't waste memory in the background.
     */
    private fun configureSmoothRendering() {
        webView.setLayerType(View.LAYER_TYPE_HARDWARE, null)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            webView.setRendererPriorityPolicy(WebView.RENDERER_PRIORITY_IMPORTANT, true)
        }
    }

    /**
     * Asks Android to use the display's fastest available refresh mode so a
     * 60 FPS rendering target is not capped below 60, while 90/120Hz phones
     * can remain smoother than 60. This only *requests* the mode - the
     * OS can still decline (battery saver, an older/60Hz-only
     * panel, etc.), so it's a no-op rather than a crash on those devices.
     * Re-applied in onResume() too: some OEM skins reset window
     * attributes like this when an activity comes back to the foreground.
     */
    private fun requestHighRefreshRate() {
        if (!::webView.isInitialized) return
        val display = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            display
        } else {
            @Suppress("DEPRECATION")
            windowManager.defaultDisplay
        } ?: return

        val supportedModes = display.supportedModes ?: return
        val bestMode = supportedModes.maxByOrNull { it.refreshRate } ?: return
        if (bestMode.refreshRate <= display.refreshRate) return // already on the fastest mode

        window.attributes = window.attributes.apply {
            preferredDisplayModeId = bestMode.modeId
        }
    }

    override fun onResume() {
        super.onResume()
        KanjiNotifications.restore(this)
        requestHighRefreshRate()
        if (::webView.isInitialized) applyDisplayPreferences()
    }

    override fun onPause() {
        if (::speechBridge.isInitialized) speechBridge.stopNow()
        super.onPause()
    }

    override fun onStop() {
        if (::webView.isInitialized && !rendererGone) webView.evaluateJavascript("window.dispatchEvent(new Event(\"kotoba-audio-before-play\"))", null)
        cancelVoiceCapture()
        super.onStop()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        rememberKanjiIntent(intent)
        if (lessonsLoaded) openPendingKanji()
        if (!lessonsLoaded) beginStartup()
    }

    private var pendingKanjiPath: String? = null
    override fun onSaveInstanceState(outState: Bundle) {
        pendingKanjiPath?.let { outState.putString("pendingKanjiPath", it) }
        super.onSaveInstanceState(outState)
    }
    private fun rememberKanjiIntent(intent: Intent?) {
        val id = intent?.getIntExtra(KanjiNotifications.EXTRA_ID, 0) ?: 0
        val level = intent?.getStringExtra(KanjiNotifications.EXTRA_LEVEL) ?: "N5"
        if (id > 0 && level in listOf("N5", "N4", "N3", "N2", "N1")) {
            pendingKanjiPath = "kanji/$id?from=kanji&level=$level"
            intent?.removeExtra(KanjiNotifications.EXTRA_ID)
            intent?.removeExtra(KanjiNotifications.EXTRA_LEVEL)
        }
    }
    private fun openPendingKanji() {
        val path = pendingKanjiPath ?: return
        pendingKanjiPath = null
        if (::webView.isInitialized && !rendererGone) webView.loadUrl(serverUrl + path)
    }
    fun sendKanjiNotificationResult(id: String, state: String, error: String) {
        if (!isDestroyed && ::webView.isInitialized && !rendererGone) {
            webView.evaluateJavascript("window.KotobaKanjiNotification?.receive(" + JSONObject.quote(id) + "," + state + "," + JSONObject.quote(error) + ")", null)
        }
    }

    override fun onDestroy() {
        // Stop the startup poll from touching a dead WebView.
        startupGeneration++
        handler.removeCallbacksAndMessages(null)
        pendingFileChooserCallback?.onReceiveValue(null)
        pendingFileChooserCallback = null
        pendingAudioPermissionRequest?.deny()
        pendingAudioPermissionRequest = null
        if (::speechBridge.isInitialized) speechBridge.shutdown()
        voiceRecognizer?.cancel()
        voiceRecognizer?.destroy()
        voiceRecognizer = null
        if (::webView.isInitialized && !rendererGone) {
            webView.stopLoading()
            webView.destroy()
        }
        super.onDestroy()
    }

    private fun isSystemDark(): Boolean {
        val mode = resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK
        return mode == Configuration.UI_MODE_NIGHT_YES
    }

    /**
     * Everything the app itself serves stays in the WebView. Anything
     * else - in practice the Feedback page's mailto: link - is handed to
     * whichever app on the phone handles it, because a WebView can't
     * open a mail composer and would just show an error page.
     */
    private inner class KotobaWebViewClient : WebViewClient() {
        override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
            if (::speechBridge.isInitialized) speechBridge.stopNow()
            cancelVoiceCapture()
        }
        override fun onPageFinished(view: WebView?, url: String?) {
            if (lessonsLoaded || view == null || url?.startsWith(serverUrl) != true) return
            val generation = startupGeneration
            view.evaluateJavascript("Boolean(document.querySelector('.site-main'))") { ready ->
                if (ready == "true" && generation == startupGeneration && !isDestroyed) {
                    lessonsLoaded = true
                    view.clearHistory()
                    startupWatchdog?.let { handler.removeCallbacks(it) }
                    startupWatchdog = null
                    handler.post { openPendingKanji() }
                }
            }
        }

        override fun onRenderProcessGone(view: WebView?, detail: RenderProcessGoneDetail?): Boolean {
            rendererGone = true
            view?.destroy()
            Toast.makeText(this@MainActivity, "The display restarted. Your saved progress is safe.", Toast.LENGTH_LONG).show()
            recreate()
            return true
        }
        override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
            if (request?.isForMainFrame == true && request.url.host == "127.0.0.1") {
                view?.loadDataWithBaseURL(serverUrl, "<html><body><h2>Kotoba could not open this page</h2><p>Your saved progress is kept on this device.</p><a href='$serverUrl'>Retry</a></body></html>", "text/html", "UTF-8", null)
            }
        }


        override fun shouldOverrideUrlLoading(
            view: WebView?,
            request: WebResourceRequest?
        ): Boolean {
            val url = request?.url ?: return false
            return handleExternal(url)
        }

        @Deprecated("Needed for API < 24, which minSdk still allows")
        override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
            if (url == null) return false
            return handleExternal(Uri.parse(url))
        }

        private fun handleExternal(uri: Uri): Boolean {
            val scheme = uri.scheme?.lowercase() ?: return false
            if (scheme == "http" || scheme == "https") {
                // Local Flask pages load in place; a genuinely remote URL
                // has no business opening inside the app shell.
                return if (uri.scheme == "http" && uri.host == "127.0.0.1" && uri.port == 5000) {
                    false
                } else {
                    launch(Intent(Intent.ACTION_VIEW, uri))
                }
            }
            return launch(Intent(Intent.ACTION_VIEW, uri))
        }

        private fun launch(intent: Intent): Boolean {
            return try {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(intent)
                true
            } catch (e: ActivityNotFoundException) {
                Toast.makeText(
                    this@MainActivity,
                    "No app on this phone can open that.",
                    Toast.LENGTH_SHORT
                ).show()
                true
            }
        }
    }

    /**
     * Handles the wallpaper picker's <input type="file"> in the page.
     * Without this, tapping "Upload image / GIF" fires the input click
     * exactly as expected, but a bare WebView has no built-in file
     * picker to show, so nothing visibly happens.
     */
    private inner class KotobaWebChromeClient : WebChromeClient() {
        override fun onPermissionRequest(request: PermissionRequest?) {
            val req = request ?: return
            runOnUiThread {
                // Only the bundled local Flask origin may request microphone
                // capture, and only the microphone resource is eligible.
                val host = req.origin?.host?.lowercase()
                val localOrigin = host == "127.0.0.1" && req.origin?.port == 5000 && req.origin?.scheme == "http"
                val asksForAudio = req.resources.contains(PermissionRequest.RESOURCE_AUDIO_CAPTURE)
                if (!localOrigin || !asksForAudio) {
                    req.deny()
                    return@runOnUiThread
                }

                val granted = ContextCompat.checkSelfPermission(
                    this@MainActivity, Manifest.permission.RECORD_AUDIO
                ) == PackageManager.PERMISSION_GRANTED
                if (granted) {
                    req.grant(arrayOf(PermissionRequest.RESOURCE_AUDIO_CAPTURE))
                } else {
                    pendingAudioPermissionRequest?.deny()
                    pendingAudioPermissionRequest = req
                    microphonePermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                }
            }
        }

        override fun onPermissionRequestCanceled(request: PermissionRequest?) {
            if (request != null && pendingAudioPermissionRequest === request) {
                pendingAudioPermissionRequest = null
            }
        }

        override fun onShowFileChooser(
            view: WebView?,
            filePathCallback: ValueCallback<Array<Uri>>?,
            fileChooserParams: FileChooserParams?
        ): Boolean {
            // Only one chooser can be in flight at a time; cancel any
            // stale one so its Promise on the JS side doesn't hang.
            pendingFileChooserCallback?.onReceiveValue(null)
            pendingFileChooserCallback = filePathCallback

            val intent = fileChooserParams?.createIntent()
                ?: Intent(Intent.ACTION_GET_CONTENT).apply {
                    type = "image/*"
                    addCategory(Intent.CATEGORY_OPENABLE)
                }

            return try {
                fileChooserLauncher.launch(intent)
                true
            } catch (e: ActivityNotFoundException) {
                pendingFileChooserCallback = null
                Toast.makeText(
                    this@MainActivity,
                    "No app on this phone can pick a photo.",
                    Toast.LENGTH_SHORT
                ).show()
                false
            }
        }
    }

    /** Native speech recognition for global/local search fields. */
    private inner class VoiceRecognitionBridge {
        @JavascriptInterface
        fun start(languageTag: String?) = startSession(languageTag, "")

        @JavascriptInterface
        fun finish() {
            runOnUiThread {
                // stopListening delivers a final phrase; cancel discards it.
                try { voiceRecognizer?.stopListening() }
                catch (t: Throwable) { sendVoiceError("Could not finish recognition. Check the words above.") }
            }
        }

        @JavascriptInterface
        fun startSession(languageTag: String?, requestId: String) {
            runOnUiThread {
                if (::speechBridge.isInitialized) speechBridge.stopNow()
                voiceRequestId = requestId
                val cleanLanguage = languageTag?.trim()?.takeIf { it.isNotEmpty() }
                // Let the speaker's buffered tail finish before opening the mic.
                handler.postDelayed({
                if (voiceRequestId != requestId || isDestroyed || isFinishing) return@postDelayed
                val granted = ContextCompat.checkSelfPermission(
                    this@MainActivity, Manifest.permission.RECORD_AUDIO
                ) == PackageManager.PERMISSION_GRANTED
                if (granted) {
                    startVoiceRecognition(cleanLanguage, requestId)
                } else {
                    pendingVoiceLanguage = cleanLanguage
                    pendingVoiceAfterPermission = true
                    if (!voicePermissionInFlight) {
                        voicePermissionInFlight = true
                        voiceMicrophonePermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    }
                }
                }, 200)
            }
        }

        @JavascriptInterface
        fun stop() {
            runOnUiThread { cancelVoiceCapture() }
        }
    }

    private fun cancelVoiceCapture() {
        voiceRequestId = "cancelled"
        pendingVoiceAfterPermission = false
        pendingVoiceLanguage = null
        val previous = voiceRecognizer
        voiceRecognizer = null
        previous?.cancel()
        previous?.destroy()
    }

    private fun startVoiceRecognition(languageTag: String?, requestId: String) {
        if (voiceRequestId != requestId) return
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            sendVoiceError("Speech recognition is not available on this device.", requestId)
            return
        }
        val previous = voiceRecognizer
        voiceRecognizer = null
        previous?.cancel()
        previous?.destroy()
        val recognizer = SpeechRecognizer.createSpeechRecognizer(this)
        voiceRecognizer = recognizer
        recognizer.setRecognitionListener(object : RecognitionListener {
            private fun isCurrent() = voiceRecognizer === recognizer && voiceRequestId == requestId
            override fun onReadyForSpeech(params: Bundle?) { if (isCurrent()) sendVoiceStatus("listening", requestId) }
            override fun onBeginningOfSpeech() { if (isCurrent()) sendVoiceStatus("listening", requestId) }
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() { if (isCurrent()) sendVoiceStatus("processing", requestId) }
            override fun onEvent(eventType: Int, params: Bundle?) {}
            override fun onPartialResults(partialResults: Bundle?) {
                if (!isCurrent()) return
                val text = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()
                if (!text.isNullOrBlank()) runVoiceJavascript("_nativePartial", text, requestId)
            }
            override fun onResults(results: Bundle?) {
                if (!isCurrent()) return
                val choices = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.filter { it.isNotBlank() }?.distinct()?.take(5) ?: emptyList()
                if (choices.isEmpty()) sendVoiceError("I didn't catch that. Try again or type above.", requestId)
                else runVoiceJavascript("_nativeResults", JSONArray(choices).toString(), requestId)
            }
            override fun onError(error: Int) {
                if (!isCurrent()) return
                val message = when (error) {
                    SpeechRecognizer.ERROR_AUDIO -> "There was a microphone problem."
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission is needed for voice search."
                    SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Speech recognition needs a connection or an offline language pack on this device."
                    SpeechRecognizer.ERROR_NO_MATCH, SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "I didn't catch that. Try again or type above."
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Voice recognition is busy. Try again."
                    else -> "Could not recognize that. Try again or type above."
                }
                sendVoiceError(message, requestId)
            }
        })
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 5)
            if (!languageTag.isNullOrBlank()) {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, languageTag)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, languageTag)
            }
        }
        try { recognizer.startListening(intent) }
        catch (t: Throwable) {
            Log.e(TAG, "Voice recognition failed to start", t)
            sendVoiceError("Could not start voice recognition.", requestId)
        }
    }

    private fun runVoiceJavascript(functionName: String, value: String, requestId: String) {
        if (!::webView.isInitialized) return
        val quoted = JSONObject.quote(value)
        val token = JSONObject.quote(requestId)
        runOnUiThread {
            if (voiceRequestId != requestId) return@runOnUiThread
            webView.evaluateJavascript(
                "(window[" + JSONObject.quote(if (requestId.startsWith("speaking:")) "KotobaSpeakingNative" else "KotobaVoiceSearch") + "]||{}).$functionName?.($quoted, $token);", null
            )
        }
    }

    private fun sendVoiceStatus(status: String, requestId: String) = runVoiceJavascript("_nativeStatus", status, requestId)
    private fun sendVoiceError(message: String, requestId: String = voiceRequestId) = runVoiceJavascript("_nativeError", message, requestId)

    /** Native offline Japanese text-to-speech exposed as
     *  window.KotobaSpeechNative to the app's bundled pages. */
    private inner class SpeechBridge : TextToSpeech.OnInitListener {
        private var tts: TextToSpeech? = TextToSpeech(this@MainActivity, this)
        @Volatile private var ready = false

        override fun onInit(status: Int) {
            if (status != TextToSpeech.SUCCESS) return
            val engine = tts ?: return
            val result = engine.setLanguage(Locale.JAPAN)
            ready = result != TextToSpeech.LANG_MISSING_DATA &&
                result != TextToSpeech.LANG_NOT_SUPPORTED
        }

        @JavascriptInterface
        fun speak(text: String?, rate: Double) {
            val clean = text?.trim().orEmpty()
            if (clean.isEmpty()) return
            runOnUiThread {
                if (isDestroyed || isFinishing || !lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) return@runOnUiThread
                cancelVoiceCapture()
                val engine = tts ?: return@runOnUiThread
                if (!ready) {
                    Toast.makeText(
                        this@MainActivity,
                        "Japanese speech data is not ready on this device.",
                        Toast.LENGTH_SHORT
                    ).show()
                    return@runOnUiThread
                }
                engine.setSpeechRate(rate.coerceIn(0.55, 1.35).toFloat())
                engine.speak(clean, TextToSpeech.QUEUE_FLUSH, null, "kotoba-${System.nanoTime()}")
            }
        }

        @JavascriptInterface
        fun stop() {
            runOnUiThread { stopNow() }
        }

        fun stopNow() { tts?.stop() }

        fun shutdown() {
            tts?.stop()
            tts?.shutdown()
            tts = null
            ready = false
        }
    }

    private var pendingBackup: String? = null
    private val backupPicker = registerForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        val payload = pendingBackup; pendingBackup = null
        if (uri == null || payload == null) { notifyBackup("Save cancelled."); return@registerForActivityResult }
        Thread {
            try {
                contentResolver.openOutputStream(uri)?.use { it.write(payload.toByteArray(Charsets.UTF_8)) } ?: throw java.io.IOException("Could not open file")
                notifyBackup("Backup saved.")
            } catch (_: Exception) { notifyBackup("Could not save the backup. Try another location.") }
        }.start()
    }
    private fun notifyBackup(message: String) {
        runOnUiThread { if (!isDestroyed) webView.evaluateJavascript("window.dispatchEvent(new CustomEvent('kotoba-backup-status',{detail:" + JSONObject.quote(message) + "}));", null) }
    }
    private inner class BackupBridge {
        @JavascriptInterface fun saveBackup(filename: String, payload: String) {
            if (payload.length > 20*1024*1024) { notifyBackup("Backup is too large."); return }
            runOnUiThread {
                if (pendingBackup != null) return@runOnUiThread
                pendingBackup = payload
                backupPicker.launch(filename.replace(Regex("[^a-zA-Z0-9._-]"), "_").take(100))
            }
        }
    }

    private fun startFlaskServer() {
        // Reuse the live process-wide worker, never a stale running flag.
        synchronized(MainActivity::class.java) {
            if (serverThread?.isAlive == true) return
            serverStartupFailed = false
            val context = applicationContext
            val privateFiles = context.filesDir
            val worker = Thread {
                try {
                    val durable = File(privateFiles, "learner-data").apply { mkdirs() }
                    val legacy = File(privateFiles, "chaquopy/AssetFinder/app/kotoba_app/data")
                    val runtime = setOf("streak.json", "feedback.json", "users.json", "user_streaks.json", "progress.json", "user_progress.json", "secret_key.txt", "roadmap_progress.json", "user_roadmap_progress.json", "roadmap_start.json", "user_roadmap_start.json", "learner_state.json", "user_learner_state.json", "device_learner.json")
                    for (name in runtime) {
                        val old = File(legacy,name); val dest = File(durable,name)
                        if (old.isFile && !dest.exists()) old.copyTo(dest)
                    }
                    android.system.Os.setenv("KOTOBA_DATA_DIR",durable.absolutePath,true)
                    android.system.Os.setenv("KOTOBA_NATIVE_TOKEN",nativeSessionToken,true)
                    if (!Python.isStarted()) Python.start(AndroidPlatform(context))
                    Python.getInstance().getModule("kotoba_app.app").callAttr("run_server")
                } catch (t: Throwable) {
                    Log.e(TAG, "Flask server thread failed", t)
                    serverStartupFailed = true
                } finally {
                    synchronized(MainActivity::class.java) {
                        if (serverThread === Thread.currentThread()) serverThread = null
                    }
                }
            }
            worker.name = "KotobaLessonServer"
            serverThread = worker
            worker.start()
        }
    }

    private fun applyDisplayPreferences() {
        val controller = WindowCompat.getInsetsController(window, window.decorView)
        controller.systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        if (hideStatusBar) controller.hide(WindowInsetsCompat.Type.statusBars())
        else controller.show(WindowInsetsCompat.Type.statusBars())
        controller.isAppearanceLightStatusBars = !displayDark
        controller.isAppearanceLightNavigationBars = !displayDark
        val color = Color.parseColor(displayBackground)
        findViewById<View>(R.id.content_container).setBackgroundColor(color)
        webView.setBackgroundColor(color)
        ViewCompat.requestApplyInsets(findViewById<View>(R.id.content_container))
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus && ::webView.isInitialized) applyDisplayPreferences()
    }

    private inner class DisplayBridge {
        @JavascriptInterface fun getHideStatusBar(): Boolean = hideStatusBar
        @JavascriptInterface fun setHideStatusBar(hidden: Boolean) {
            runOnUiThread {
                if (isDestroyed) return@runOnUiThread
                hideStatusBar = hidden
                getSharedPreferences("kotoba-display", MODE_PRIVATE).edit().putBoolean("hideStatusBar", hidden).apply()
                applyDisplayPreferences()
            }
        }
        @JavascriptInterface fun setTheme(background: String, dark: Boolean) {
            if (!Regex("^#[0-9a-fA-F]{6}$").matches(background)) return
            runOnUiThread {
                if (isDestroyed) return@runOnUiThread
                displayBackground = background; displayDark = dark
                getSharedPreferences("kotoba-display", MODE_PRIVATE).edit().putString("background", background).putBoolean("dark", dark).apply()
                applyDisplayPreferences()
            }
        }
    }

    private inner class StartupBridge {
        @JavascriptInterface fun retry() { runOnUiThread { beginStartup() } }
        @JavascriptInterface fun introElapsedMs(): Long =
            if (introSkipped) 3_000L else (SystemClock.elapsedRealtime() - introStartedAt).coerceAtLeast(0L)
        @JavascriptInterface fun skipIntro() { introSkipped = true }
    }

    private fun showOpeningIntro() {
        introStartedAt = SystemClock.elapsedRealtime()
        introSkipped = false
        val html = assets.open("kotoba-opening.html").bufferedReader().use { it.readText() }
        webView.loadDataWithBaseURL(serverUrl, html, "text/html", "UTF-8", null)
    }

    private fun startupPage(message: String, retry: Boolean) {
        val bg = displayBackground
        val ink = if (displayDark) "#ECF4FF" else "#29304D"
        val button = if (retry) "<button type='button' onclick='KotobaStartupNative.retry()' style='font:inherit;padding:12px 20px;border-radius:12px;margin-top:16px;background:transparent;color:inherit;border:1px solid currentColor'>Retry</button>" else ""
        webView.loadDataWithBaseURL(serverUrl, "<html><head><meta name='viewport' content='width=device-width, initial-scale=1'><title>Starting Kotoba</title></head><body style='background:$bg;color:$ink;padding:32px;font-family:sans-serif;line-height:1.6'><h1>Kotoba</h1><p>$message</p><p>Works with or without internet.</p><p>Your progress saves on this device in both modes. Cloud sync, when enabled, retries when internet returns.</p>$button</body></html>", "text/html", "UTF-8", null)
    }

    private fun showStartupFailure(generation: Int) {
        if (generation != startupGeneration || lessonsLoaded || isFinishing || isDestroyed) return
        startupGeneration++
        startupWatchdog?.let { handler.removeCallbacks(it) }
        startupWatchdog = null
        webView.stopLoading()
        startupPage("Lessons could not open on this device. Internet is not required. Tap Retry to try again.", true)
    }

    private fun beginStartup() {
        if (isFinishing || isDestroyed || lessonsLoaded) return
        val generation = ++startupGeneration
        startupWatchdog?.let { handler.removeCallbacks(it) }
        showOpeningIntro()
        val watchdog = Runnable { showStartupFailure(generation) }
        startupWatchdog = watchdog
        // UI deadline covers both a stuck probe and a stalled bootstrap page.
        handler.postDelayed(watchdog, startupTimeoutMs)
        startFlaskServer()
        Thread {
            val deadline = SystemClock.elapsedRealtime() + startupTimeoutMs
            while (generation == startupGeneration && SystemClock.elapsedRealtime() < deadline) {
                if (isServerRespondingNow()) {
                    handler.post {
                        if (generation == startupGeneration && !isFinishing && !isDestroyed) {
                            webView.loadUrl(serverUrl + "__bootstrap?token=" + nativeSessionToken)
                        }
                    }
                    return@Thread
                }
                if (serverStartupFailed) break
                try { Thread.sleep(250) } catch (_: InterruptedException) { return@Thread }
            }
            handler.post { showStartupFailure(generation) }
        }.apply { name = "KotobaStartupProbe"; start() }
    }

    private fun isServerRespondingNow(): Boolean {
        var conn: HttpURLConnection? = null
        return try {
            conn = URL(healthUrl).openConnection(Proxy.NO_PROXY) as HttpURLConnection
            conn.connectTimeout = 800
            conn.readTimeout = 800
            conn.requestMethod = "GET"
            conn.setRequestProperty("Cache-Control", "no-cache")
            conn.responseCode == 200 && conn.inputStream.bufferedReader().use {
                JSONObject(it.readLine().orEmpty()).optString("app") == "Kotoba"
            }
        } catch (_: Exception) { false }
        finally { conn?.disconnect() }
    }
}
