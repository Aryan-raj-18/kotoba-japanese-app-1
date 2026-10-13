package com.kotoba.app

/** Pure selection/timing rules shared by settings, alarms and notification actions. */
data class KanjiCard(val id: Int, val kanji: String, val meaning: String,
                     val on: String, val kun: String, val level: String)

data class KanjiNoticeConfig(
    val level: String = "N5", val selected: List<String> = emptyList(),
    val mode: String = "rotate", val minutes: Int = 60,
    val meaning: Boolean = true, val readings: Boolean = true
) {
    fun validate(cards: List<KanjiCard>): KanjiNoticeConfig {
        require(level in listOf("N5", "N4", "N3", "N2", "N1")) { "Choose a JLPT level." }
        require(mode in listOf("rotate", "single", "hold")) { "Choose a display mode." }
        val minimum = if (mode == "rotate") 15 else 1
        require(minutes in minimum..1440) { "Choose $minimum to 1440 minutes." }
        val valid = cards.filter { it.level == level }.map { it.kanji }.toSet()
        require(valid.isNotEmpty()) { "This JLPT level is unavailable." }
        require(selected.all { it in valid }) { "Choose kanji from the selected level." }
        return copy(selected = selected.distinct())
    }
    fun deck(cards: List<KanjiCard>): List<KanjiCard> {
        val byLevel = cards.filter { it.level == level }
        return if (selected.isEmpty()) byLevel else selected.mapNotNull { char -> byLevel.find { it.kanji == char } }
    }
    fun nextIndex(index: Int, size: Int): Int = if (size <= 0) 0 else (index.coerceAtLeast(0) + 1) % size
    fun nextAt(now: Long): Long = if (mode == "hold") 0 else now + minutes.toLong() * 60_000L
    fun expired(now: Long, deadline: Long): Boolean = mode == "single" && deadline > 0 && now >= deadline
}
