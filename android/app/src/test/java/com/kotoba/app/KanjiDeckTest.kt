package com.kotoba.app
import org.junit.Assert.*
import org.junit.Test

class KanjiDeckTest {
    private val cards = listOf(KanjiCard(1,"一","one","イチ","ひと","N5"), KanjiCard(2,"二","two","ニ","ふた","N5"), KanjiCard(3,"光","light","コウ","ひかり","N4"))
    @Test fun wholeLevelIsRestrictedToChosenLevel() { assertEquals(listOf("一","二"),KanjiNoticeConfig().deck(cards).map{it.kanji}); assertEquals(listOf("光"),KanjiNoticeConfig(level="N4").deck(cards).map{it.kanji}) }
    @Test fun selectionsAreDeduplicated() { assertEquals(listOf("二"),KanjiNoticeConfig(selected=listOf("二","二")).validate(cards).selected) }
    @Test fun selectedOrderIsRetained() { assertEquals(listOf("二","一"),KanjiNoticeConfig(selected=listOf("二","一")).validate(cards).deck(cards).map{it.kanji}) }
    @Test fun wrongLevelSelectionIsRejected() { assertThrows(IllegalArgumentException::class.java){KanjiNoticeConfig(selected=listOf("光")).validate(cards)} }
    @Test fun unsupportedLevelsAndModesAreRejected() { assertThrows(IllegalArgumentException::class.java){KanjiNoticeConfig(level="N0").validate(cards)};assertThrows(IllegalArgumentException::class.java){KanjiNoticeConfig(mode="alarm").validate(cards)} }
    @Test fun durationMustBeWithinUserRange() { for(i in listOf(-1,0,14,1441,Int.MAX_VALUE)){assertThrows(IllegalArgumentException::class.java){KanjiNoticeConfig(minutes=i).validate(cards)}};KanjiNoticeConfig(minutes=15).validate(cards);KanjiNoticeConfig(minutes=1440).validate(cards) }
    @Test fun nextWrapsWithoutSkippingOneCardDeck() { val c=KanjiNoticeConfig();assertEquals(1,c.nextIndex(0,2));assertEquals(0,c.nextIndex(1,2));assertEquals(0,c.nextIndex(0,1));assertEquals(0,c.nextIndex(0,0)) }
    @Test fun selectedDurationSetsNextDeadline() { assertEquals(901000L,KanjiNoticeConfig(minutes=15).nextAt(1000));assertEquals(86401000L,KanjiNoticeConfig(minutes=1440).nextAt(1000)) }
    @Test fun singleCardExpiresOnlyAtItsDeadline() { val c=KanjiNoticeConfig(mode="single",minutes=1).validate(cards);assertEquals(61000L,c.nextAt(1000));assertFalse(c.expired(999,1000));assertTrue(c.expired(1000,1000));assertFalse(c.expired(1000,0)) }
    @Test fun holdHasNoDeadlineAndDoesNotExpire() { val c=KanjiNoticeConfig(mode="hold");assertEquals(0L,c.nextAt(1000));assertFalse(c.expired(Long.MAX_VALUE,1000));assertFalse(KanjiNoticeConfig().expired(1000,1000)) }
}
