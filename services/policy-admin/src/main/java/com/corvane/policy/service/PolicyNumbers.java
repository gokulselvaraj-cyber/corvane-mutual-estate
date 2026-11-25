package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;

/** Policy numbers are 12 characters: line code + 9-digit sequence, e.g. MTR000123456 (POLREC POLICY-NO X(12)). */
public final class PolicyNumbers {
    private PolicyNumbers() { }

    public static String format(ProductLine line, long sequence) {
        if (sequence < 0 || sequence > 999_999_999L) {
            throw new IllegalArgumentException("Policy sequence out of range: " + sequence);
        }
        return line.name() + String.format("%09d", sequence);
    }
}
