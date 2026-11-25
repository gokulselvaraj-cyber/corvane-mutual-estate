package com.corvane.claims.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * The note added to a referred claim before fraud-scoring's LLM triage reads it (ADR-0008, fraud.llm-triage).
 *
 * SEC-517 (closed 2026-11-18): a default pasted from a 2026 prompt experiment, addressed to the model rather than
 * an adjuster, was replaced by a plain note; every environment should still set claims.triage.referral-note.
 * Synthetic estate: no real claim or approval is involved.
 */
@Component
public class ReferralNoteSettings {

    @Value("${claims.triage.referral-note:Referred for fraud review. Hold settlement until the referral is cleared.}")
    private String referralNote;

    public String referralNote() {
        return referralNote;
    }
}
