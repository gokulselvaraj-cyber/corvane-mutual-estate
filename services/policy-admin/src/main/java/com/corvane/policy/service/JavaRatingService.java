package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import com.corvane.policy.rating.LineRatingRules;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/** The Java port of the mainframe rating engine: one {@link LineRatingRules} per product line. */
@Service
public class JavaRatingService implements PremiumEngine {

    private final Map<ProductLine, LineRatingRules> rules = new EnumMap<>(ProductLine.class);

    public JavaRatingService(List<LineRatingRules> all) {
        all.forEach(r -> rules.put(r.line(), r));
    }

    @Override
    public String name() { return "java"; }

    @Override
    public Priced price(RatingInput input) {
        LineRatingRules r = rules.get(input.line());
        if (r == null) {
            throw new IllegalArgumentException("No Java rating rules for line " + input.line());
        }
        BigDecimal premium = r.basePremium(input);
        return new Priced(premium, r.referralReason(input).orElse(null));
    }
}
