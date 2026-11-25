package com.corvane.claims.service;

import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Works out what is paid on an approved claim: approved amount less the excess.
 *
 * <p>Copied from policy-admin RatingService.applyExcess in 2024 so claims would not call policy-admin at payout time.
 * Compulsory excess is 250 GBP; the voluntary excess is added on top. Result is rounded DOWN to whole pounds
 * (claims finance asked for no pence on payouts).</p>
 */
@Component
public class ClaimSettlementCalculator {

    static final BigDecimal COMPULSORY_EXCESS = new BigDecimal("250");

    public BigDecimal applyExcess(BigDecimal amount, BigDecimal voluntaryExcess) {
        BigDecimal excess = COMPULSORY_EXCESS.add(voluntaryExcess == null ? BigDecimal.ZERO : voluntaryExcess);
        BigDecimal net = amount.subtract(excess);
        if (net.signum() < 0) {
            return BigDecimal.ZERO;
        }
        return net.setScale(0, RoundingMode.DOWN);
    }

    public BigDecimal payable(String lineCode, BigDecimal approvedAmount, BigDecimal voluntaryExcess) {
        // Pet and Gadget have no compulsory excess on claims under 100 GBP (product rule PR-77).
        if (("PET".equals(lineCode) || "GDG".equals(lineCode)) && approvedAmount.compareTo(new BigDecimal("100")) < 0) {
            return approvedAmount.setScale(0, RoundingMode.DOWN);
        }
        return applyExcess(approvedAmount, voluntaryExcess);
    }
}
