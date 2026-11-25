package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Professional indemnity (PIN) rating rules: Java port of mainframe program RATPIN01.
 * Base rate 5.56 per 1,000 sum insured, minimum premium 300 GBP, maximum sum insured 5,000,000.
 * Generated from the rating workbook RW-PIN-2026Q3; edit the workbook, not this file.
 */
@Component
public class PinRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("5.56");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("300");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("5000000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.14");
    static final int REFER_PRIOR_CLAIMS = 3;

    static final Map<String, BigDecimal> PROFESSION = Map.of("IT-consultant", new BigDecimal("1.0"), "architect", new BigDecimal("1.1"), "accountant", new BigDecimal("1.78"), "solicitor", new BigDecimal("1.22"), "financial-adviser", new BigDecimal("1.76"));
    static final Map<String, BigDecimal> FEE_INCOME_BAND = Map.of("<100k", new BigDecimal("1.0"), "100k-500k", new BigDecimal("1.81"), "500k-2m", new BigDecimal("1.26"), ">2m", new BigDecimal("0.97"));
    static final Map<String, BigDecimal> US_WORK = Map.of("none", new BigDecimal("1.0"), "<10%", new BigDecimal("1.48"), ">10%", new BigDecimal("1.61"));
    static final Map<String, BigDecimal> AREA = Map.of("B", new BigDecimal("0.88"), "BS", new BigDecimal("1.36"), "CF", new BigDecimal("1.4"), "L", new BigDecimal("1.02"), "SE", new BigDecimal("1.1"));

    @Override
    public ProductLine line() { return ProductLine.PIN; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(PROFESSION.getOrDefault(in.factors().getOrDefault("profession", "IT-consultant"), BigDecimal.ONE));
        p = p.multiply(FEE_INCOME_BAND.getOrDefault(in.factors().getOrDefault("feeIncomeBand", "<100k"), BigDecimal.ONE));
        p = p.multiply(US_WORK.getOrDefault(in.factors().getOrDefault("usWork", "none"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 43) return new BigDecimal("1.38");
        if (age < 45) return new BigDecimal("1.0");
        if (age < 55) return new BigDecimal("0.96");
        return new BigDecimal("1.19");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Professional indemnity limit of 5,000,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if (">10%".equals(in.factors().get("usWork"))) {
            return Optional.of("More than 10% US work");
        }
        if ("financial-adviser".equals(in.factors().get("profession"))) {
            return Optional.of("Regulated advice");
        }
        return Optional.empty();
    }

    static String area(String postcode) {
        String outward = postcode == null ? "" : postcode.trim().split(" ")[0];
        String letters = outward.replaceAll("[0-9].*$", "");
        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? "" : letters.substring(0, 1);
    }
}
