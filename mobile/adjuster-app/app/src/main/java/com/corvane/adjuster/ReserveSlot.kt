package com.corvane.adjuster

import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/**
 * An inspection appointment slot the adjuster reserves with the claimant. Nothing to do with a claim reserve
 * (money set aside, com.corvane.claims.domain.Reserve in claims-service).
 */
data class ReserveSlot(val claimId: String, val start: LocalDateTime, val minutes: Int) {
    fun label(): String = start.format(DateTimeFormatter.ofPattern("EEE d MMM HH:mm")) + " ($minutes min)"

    companion object {
        fun nextFree(claimId: String): ReserveSlot {
            val now = LocalDateTime.now().plusDays(1).withHour(9).withMinute(0)
            return ReserveSlot(claimId, now, 45)
        }
    }
}
