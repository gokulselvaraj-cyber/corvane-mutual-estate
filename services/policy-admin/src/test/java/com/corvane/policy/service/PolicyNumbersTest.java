package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.*;

class PolicyNumbersTest {
    @Test
    void twelveCharacters() {
        assertThat(PolicyNumbers.format(ProductLine.CYB, 42)).isEqualTo("CYB000000042").hasSize(12);
    }

    @Test
    void rejectsOverflow() {
        assertThatThrownBy(() -> PolicyNumbers.format(ProductLine.MTR, 1_000_000_000L)).isInstanceOf(IllegalArgumentException.class);
    }
}
