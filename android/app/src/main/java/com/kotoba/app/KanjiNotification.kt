package com.kotoba.app

import android.Manifest
import android.app.AlarmManager
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.drawable.Icon
import android.os.Build
import android.provider.Settings
import android.webkit.JavascriptInterface
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import org.json.JSONArray
import org.json.JSONObject

/** Offline notification study; no Flask server or foreground service needs to run. */
object KanjiNotifications {
    const val CHANNEL = "kanji_study"
    const val NOTICE_ID = 2002
    const val EXTRA_ID = "kotoba_kanji_id"
    const val EXTRA_LEVEL = "kotoba_kanji_level"
    const val TICK = "com.kotoba.app.KANJI_TICK"
    const val NEXT = "com.kotoba.app.KANJI_NEXT"
    const val STOP = "com.kotoba.app.KANJI_STOP"
    private const val PREFS = "kotoba_kanji_notification"
    private var cachedCards: List<KanjiCard>? = null
    private fun prefs(c: Context) = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    @Synchronized fun cards(c: Context): List<KanjiCard> {
        cachedCards?.let { return it }
        val data = JSONArray(c.assets.open("kanji-notification.json").bufferedReader().use { it.readText() })
        return (0 until data.length()).map { i ->
            val x = data.getJSONObject(i)
            KanjiCard(x.getInt("id"), x.getString("kanji"), x.getString("meaning"),
                x.optString("on"), x.optString("kun"), x.getString("level"))
        }.also { cachedCards = it }
    }
    fun parse(c: Context, raw: String): KanjiNoticeConfig {
        require(raw.length <= 80_000) { "Too many selected kanji." }
        val x = JSONObject(raw); val selected = x.optJSONArray("selected") ?: JSONArray()
        return KanjiNoticeConfig(x.optString("level", "N5"),
            (0 until selected.length()).map { selected.getString(it) },
            x.optString("mode", "rotate"), x.optInt("minutes", 60),
            x.optBoolean("meaning", true), x.optBoolean("readings", true)).validate(cards(c))
    }
    private fun config(c: Context): KanjiNoticeConfig = try {
        parse(c, prefs(c).getString("config", "{}") ?: "{}")
    } catch (_: Exception) {
        prefs(c).edit().clear().apply(); cancelAlarm(c)
        c.getSystemService(NotificationManager::class.java).cancel(NOTICE_ID)
        KanjiNoticeConfig()
    }
    private fun json(config: KanjiNoticeConfig) = JSONObject().put("level", config.level)
        .put("selected", JSONArray(config.selected)).put("mode", config.mode).put("minutes", config.minutes)
        .put("meaning", config.meaning).put("readings", config.readings)
    fun ensureChannel(c: Context) {
        if (Build.VERSION.SDK_INT < 26) return
        val manager = c.getSystemService(NotificationManager::class.java)
        if (manager.getNotificationChannel(CHANNEL) != null) return
        manager.createNotificationChannel(NotificationChannel(CHANNEL, "Kanji study", NotificationManager.IMPORTANCE_LOW).apply {
            description = "Your chosen offline kanji on the notification shade and lock screen."
            setSound(null, null); enableVibration(false); setShowBadge(false)
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
        })
    }
    fun canPost(c: Context): Boolean {
        if (Build.VERSION.SDK_INT >= 33 && ContextCompat.checkSelfPermission(c, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return false
        if (!NotificationManagerCompat.from(c).areNotificationsEnabled()) return false
        return Build.VERSION.SDK_INT < 26 || c.getSystemService(NotificationManager::class.java).getNotificationChannel(CHANNEL)?.importance != NotificationManager.IMPORTANCE_NONE
    }
    private fun action(c: Context, name: String, code: Int) = PendingIntent.getBroadcast(c, code,
        Intent(c, KanjiNotificationReceiver::class.java).setAction(name), PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
    private fun cancelAlarm(c: Context) = (c.getSystemService(Context.ALARM_SERVICE) as AlarmManager).cancel(action(c, TICK, 1102))
    private fun schedule(c: Context, deadline: Long) {
        cancelAlarm(c)
        if (deadline > 0) {
            // Study cards tolerate batching/Doze delays; no exact-alarm or battery exemption is requested.
            (c.getSystemService(Context.ALARM_SERVICE) as AlarmManager).setWindow(
                AlarmManager.RTC, deadline.coerceAtLeast(System.currentTimeMillis() + 1000), 10 * 60_000L, action(c, TICK, 1102))
        }
    }
    @Synchronized fun apply(c: Context, value: KanjiNoticeConfig): Boolean {
        val valid = value.validate(cards(c)); ensureChannel(c)
        prefs(c).edit().putString("config", json(valid).toString()).putInt("index", 0)
            .putBoolean("enabled", canPost(c)).putLong("deadline", valid.nextAt(System.currentTimeMillis())).apply()
        cancelAlarm(c)
        if (!canPost(c)) { c.getSystemService(NotificationManager::class.java).cancel(NOTICE_ID); return false }
        show(c); schedule(c, prefs(c).getLong("deadline", 0)); return true
    }
    @Synchronized fun stop(c: Context) {
        prefs(c).edit().putBoolean("enabled", false).putLong("deadline", 0).apply()
        cancelAlarm(c); c.getSystemService(NotificationManager::class.java).cancel(NOTICE_ID)
    }
    @Synchronized fun advance(c: Context, automatic: Boolean) {
        if (!prefs(c).getBoolean("enabled", false)) return
        val cfg = config(c)
        // A queued old alarm must not advance newly applied settings early.
        if (automatic && prefs(c).getLong("deadline", 0) > System.currentTimeMillis()) return
        if (automatic && cfg.mode == "single") { stop(c); return }
        if (automatic && cfg.mode == "hold") return
        val pool = cfg.deck(cards(c)); if (pool.isEmpty()) { stop(c); return }
        prefs(c).edit().putInt("index", cfg.nextIndex(prefs(c).getInt("index", 0), pool.size))
            .putLong("deadline", cfg.nextAt(System.currentTimeMillis())).apply()
        show(c); schedule(c, prefs(c).getLong("deadline", 0))
    }
    @Synchronized fun restore(c: Context) {
        if (!prefs(c).getBoolean("enabled", false)) return
        val cfg = config(c); val deadline = prefs(c).getLong("deadline", 0)
        if (cfg.expired(System.currentTimeMillis(), deadline)) { stop(c); return }
        if (cfg.mode == "rotate" && deadline > 0 && deadline <= System.currentTimeMillis()) { advance(c, true); return }
        ensureChannel(c)
        if (c.getSystemService(NotificationManager::class.java).activeNotifications.none { it.id == NOTICE_ID }) show(c)
        schedule(c, deadline)
    }
    fun state(c: Context): String {
        val cfg = config(c); val p = prefs(c)
        val enabled = p.getBoolean("enabled", false) && !cfg.expired(System.currentTimeMillis(), p.getLong("deadline", 0))
        val deck = cfg.deck(cards(c)); val card = deck.getOrNull(p.getInt("index", 0).coerceIn(0, (deck.size - 1).coerceAtLeast(0)))
        return json(cfg).put("enabled", enabled).put("allowed", canPost(c)).put("current", card?.kanji ?: "")
            .put("deadline", p.getLong("deadline", 0)).toString()
    }
    private fun glyph(char: String, size: Int, color: Int): Bitmap {
        val image = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { this.color = color; textSize = size * .8f; textAlign = Paint.Align.CENTER; typeface = Typeface.create("sans-serif", Typeface.NORMAL) }
        val canvas = Canvas(image)
        if (size > 96) canvas.drawCircle(size / 2f, size / 2f, size / 2f, Paint(Paint.ANTI_ALIAS_FLAG).apply { this.color = Color.rgb(245, 239, 229) })
        canvas.drawText(char, size / 2f, size / 2f - (paint.ascent() + paint.descent()) / 2f, paint)
        return image
    }
    private fun show(c: Context) {
        if (!canPost(c) || !prefs(c).getBoolean("enabled", false)) return
        val cfg = config(c); val pool = cfg.deck(cards(c)); if (pool.isEmpty()) return
        val card = pool[prefs(c).getInt("index", 0).coerceIn(0, pool.lastIndex)]
        val open = PendingIntent.getActivity(c, 1103, Intent(c, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra(EXTRA_ID, card.id); putExtra(EXTRA_LEVEL, card.level)
        }, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val lines = mutableListOf<String>()
        if (cfg.meaning) lines += card.meaning
        if (cfg.readings) {
            if (card.on.isNotBlank()) lines += "On: ${card.on}"
            if (card.kun.isNotBlank()) lines += "Kun: ${card.kun}"
        }
        val text = if (lines.isEmpty()) "Recall the meaning, then tap to check." else lines.joinToString(" · ")
        @Suppress("DEPRECATION")
        val builder = if (Build.VERSION.SDK_INT >= 26) Notification.Builder(c, CHANNEL) else Notification.Builder(c)
        builder.setSmallIcon(Icon.createWithBitmap(glyph(card.kanji, 96, Color.WHITE)))
            .setLargeIcon(glyph(card.kanji, 192, Color.rgb(27, 44, 71)))
            .setContentTitle("${card.kanji} · JLPT ${card.level}").setContentText(text)
            .setStyle(Notification.BigTextStyle().bigText(lines.ifEmpty { listOf(text) }.joinToString("\n")))
            .setVisibility(Notification.VISIBILITY_PUBLIC).setOngoing(true).setOnlyAlertOnce(true)
            .setShowWhen(false).setContentIntent(open).setDeleteIntent(action(c, STOP, 1105))
            .addAction(Notification.Action.Builder(null as Icon?, "Next", action(c, NEXT, 1104)).build())
            .addAction(Notification.Action.Builder(null as Icon?, "Stop", action(c, STOP, 1105)).build())
        if (cfg.mode == "single" && Build.VERSION.SDK_INT >= 26) builder.setTimeoutAfter((prefs(c).getLong("deadline", 0) - System.currentTimeMillis()).coerceAtLeast(1))
        try { c.getSystemService(NotificationManager::class.java).notify(NOTICE_ID, builder.build()) }
        catch (_: SecurityException) { /* Notification permission can change between the check and post. */ }
    }
}

class KanjiNotificationReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        when (intent.action) {
            KanjiNotifications.TICK -> KanjiNotifications.advance(context, true)
            KanjiNotifications.NEXT -> KanjiNotifications.advance(context, false)
            KanjiNotifications.STOP -> KanjiNotifications.stop(context)
        }
    }
}

class KanjiNotificationBridge(private val activity: MainActivity) {
    private var generation = 0
    @JavascriptInterface fun getState(): String = KanjiNotifications.state(activity)
    @JavascriptInterface fun apply(raw: String, requestId: String) {
        activity.runOnUiThread {
            val token = ++generation
            try {
                val cfg = KanjiNotifications.parse(activity, raw)
                activity.requestNotificationPermissionThen {
                    if (generation == token) {
                        val allowed = KanjiNotifications.apply(activity, cfg)
                        reply(requestId, if (allowed) "" else "Allow Kotoba notifications in Android settings to show your kanji.")
                    }
                }
            } catch (e: IllegalArgumentException) { reply(requestId, e.message ?: "Check your selection.") }
              catch (_: org.json.JSONException) { reply(requestId, "Check your selection.") }
        }
    }
    @JavascriptInterface fun stop() { activity.runOnUiThread { generation++; KanjiNotifications.stop(activity); reply("", "") } }
    @JavascriptInterface fun next() { activity.runOnUiThread { KanjiNotifications.advance(activity, false); reply("", "") } }
    @JavascriptInterface fun openSettings() {
        activity.runOnUiThread {
            KanjiNotifications.ensureChannel(activity)
            val intent = if (Build.VERSION.SDK_INT >= 26) Intent(Settings.ACTION_CHANNEL_NOTIFICATION_SETTINGS)
                .putExtra(Settings.EXTRA_APP_PACKAGE, activity.packageName).putExtra(Settings.EXTRA_CHANNEL_ID, KanjiNotifications.CHANNEL)
                else Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, android.net.Uri.parse("package:" + activity.packageName))
            try { activity.startActivity(intent) } catch (_: android.content.ActivityNotFoundException) { }
        }
    }
    @JavascriptInterface fun openPhoneSettings() {
        activity.runOnUiThread {
            try { activity.startActivity(Intent(Settings.ACTION_SETTINGS)) }
            catch (_: android.content.ActivityNotFoundException) { }
        }
    }
    private fun reply(id: String, error: String) {
        activity.sendKanjiNotificationResult(id, KanjiNotifications.state(activity), error)
    }
}
