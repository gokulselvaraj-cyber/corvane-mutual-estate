package com.corvane.policy.api.dto;

import com.corvane.policy.domain.Policy;
import java.math.BigDecimal;
import java.time.LocalDate;

/** What claims-service and the portal see. National ID is never exposed; only the holder's party ref. */
public record PolicyView(String policyNumber, String line, String status, String partyRef, String holderName,
                         String postcode, LocalDate inceptionDate, LocalDate expiryDate, BigDecimal annualPremium,
                         BigDecimal voluntaryExcess, String currency) {

    public static PolicyView from(Policy p) {
        return new PolicyView(p.getPolicyNumber(), p.getLine().name(), p.getStatus().name(),
                p.getHolder().getPartyRef(), p.getHolder().getFullName(), p.getHolder().getPostcode(),
                p.getInceptionDate(), p.getExpiryDate(), p.getAnnualPremium(), p.getVoluntaryExcess(), p.getCurrency());
    }
}
