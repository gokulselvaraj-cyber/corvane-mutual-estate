package com.corvane.claims.domain;

import java.math.BigDecimal;

/** A claim reserve: money set aside for the expected cost of a claim. (Not the mobile app's ReserveSlot.) */
public record Reserve(String lineCode, BigDecimal indemnity, BigDecimal expenses) {
    public BigDecimal total() { return indemnity.add(expenses); }
}
