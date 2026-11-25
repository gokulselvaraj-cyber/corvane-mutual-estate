package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Public liability (PLB) rating rules: Java port of mainframe program RATPLB01.
 * Base rate 3.308 per 1,000 sum insured, minimum premium 120 GBP, maximum sum insured 10,000,000.
 * Generated from the rating workbook RW-PLB-2026Q3; edit the workbook, not this file.
 */
@Component
public class PlbRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("3.308");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("120");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("10000000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.23");
    static final int REFER_PRIOR_CLAIMS = 3;

    static final Map<String, BigDecimal> TRADE = Map.of("consultant", new BigDecimal("1.0"), "retail", new BigDecimal("1.21"), "hospitality", new BigDecimal("1.24"), "construction", new BigDecimal("1.82"), "events", new BigDecimal("1.88"));
    static final Map<String, BigDecimal> TURNOVER_BAND = Map.of("<250k", new BigDecimal("1.0"), "250k-1m", new BigDecimal("1.56"), "1m-5m", new BigDecimal("0.86"), ">5m", new BigDecimal("1.48"));
    static final Map<String, BigDecimal> WORK_AT_HEIGHT = Map.of("no", new BigDecimal("1.0"), "under-10m", new BigDecimal("1.55"), "over-10m", new BigDecimal("1.18"));
    static final Map<String, BigDecimal> AREA = Map.of("BS", new BigDecimal("1.16"), "E", new BigDecimal("1.35"), "N", new BigDecimal("1.03"), "SE", new BigDecimal("1.25"), "SW", new BigDecimal("1.05"));

    @Override
    public ProductLine line() { return ProductLine.PLB; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(TRADE.getOrDefault(in.factors().getOrDefault("trade", "consultant"), BigDecimal.ONE));
        p = p.multiply(TURNOVER_BAND.getOrDefault(in.factors().getOrDefault("turnoverBand", "<250k"), BigDecimal.ONE));
        p = p.multiply(WORK_AT_HEIGHT.getOrDefault(in.factors().getOrDefault("workAtHeight", "no"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 46) return new BigDecimal("1.46");
        if (age < 47) return new BigDecimal("1.0");
        if (age < 61) return new BigDecimal("0.85");
        return new BigDecimal("1.24");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Public liability limit of 10,000,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if ("over-10m".equals(in.factors().get("workAtHeight"))) {
            return Optional.of("Work at height above 10m");
        }
        return Optional.empty();
    }

    static String area(String postcode) {
        String outward = postcode == null ? "" : postcode.trim().split(" ")[0];
        String letters = outward.replaceAll("[0-9].*$", "");
        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? "" : letters.substring(0, 1);
    }
}
