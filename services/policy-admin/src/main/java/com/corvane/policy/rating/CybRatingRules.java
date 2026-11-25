package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Cyber (CYB) rating rules: Java port of mainframe program RATCYB01.
 * Base rate 6.49 per 1,000 sum insured, minimum premium 350 GBP, maximum sum insured 5,000,000.
 * Generated from the rating workbook RW-CYB-2026Q3; edit the workbook, not this file.
 */
@Component
public class CybRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("6.49");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("350");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("5000000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.19");
    static final int REFER_PRIOR_CLAIMS = 2;

    static final Map<String, BigDecimal> MFA = Map.of("all-users", new BigDecimal("1.0"), "admins-only", new BigDecimal("1.39"), "none", new BigDecimal("1.61"));
    static final Map<String, BigDecimal> BACKUPS = Map.of("offline-tested", new BigDecimal("1.0"), "online-only", new BigDecimal("1.0"), "none", new BigDecimal("1.55"));
    static final Map<String, BigDecimal> RECORDS_HELD = Map.of("<10k", new BigDecimal("1.0"), "10k-100k", new BigDecimal("1.53"), ">100k", new BigDecimal("0.87"));
    static final Map<String, BigDecimal> SECTOR = Map.of("professional", new BigDecimal("1.0"), "retail", new BigDecimal("0.83"), "healthcare", new BigDecimal("0.86"), "education", new BigDecimal("1.03"));
    static final Map<String, BigDecimal> AREA = Map.of("CF", new BigDecimal("1.07"), "EH", new BigDecimal("1.14"), "L", new BigDecimal("1.41"), "SW", new BigDecimal("0.88"), "W", new BigDecimal("1.03"));

    @Override
    public ProductLine line() { return ProductLine.CYB; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(MFA.getOrDefault(in.factors().getOrDefault("mfa", "all-users"), BigDecimal.ONE));
        p = p.multiply(BACKUPS.getOrDefault(in.factors().getOrDefault("backups", "offline-tested"), BigDecimal.ONE));
        p = p.multiply(RECORDS_HELD.getOrDefault(in.factors().getOrDefault("recordsHeld", "<10k"), BigDecimal.ONE));
        p = p.multiply(SECTOR.getOrDefault(in.factors().getOrDefault("sector", "professional"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 24) return new BigDecimal("1.14");
        if (age < 41) return new BigDecimal("1.0");
        if (age < 65) return new BigDecimal("0.86");
        return new BigDecimal("1.04");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Cyber limit of 5,000,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if ("none".equals(in.factors().get("mfa"))) {
            return Optional.of("No multi-factor authentication");
        }
        if ("none".equals(in.factors().get("backups"))) {
            return Optional.of("No backups");
        }
        return Optional.empty();
    }

    static String area(String postcode) {
        String outward = postcode == null ? "" : postcode.trim().split(" ")[0];
        String letters = outward.replaceAll("[0-9].*$", "");
        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? "" : letters.substring(0, 1);
    }
}
