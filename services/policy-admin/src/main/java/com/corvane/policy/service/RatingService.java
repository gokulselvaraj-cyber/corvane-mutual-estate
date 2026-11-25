package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import com.corvane.policy.domain.RatingResult;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

/**
 * J4 step 3: rating. Delegates the base premium to whichever engine {@link PremiumEngineRouter} selects, then
 * applies the rules Corvane keeps outside both engines: excess and Insurance Premium Tax (IPT).
 *
 * <p>The excess rule is duplicated elsewhere: COBOL PRMCALC paragraph 3000-APPLY-EXCESS and claims-service
 * ClaimSettlementCalculator.applyExcess. Keep them in step (POL-977).</p>
 */
@Service
public class RatingService {

    /** Compulsory excess in GBP, added to the customer's voluntary excess. */
    public static final BigDecimal COMPULSORY_EXCESS = new BigDecimal("250");

    private final PremiumEngineRouter router;
    private final BigDecimal iptStandard;
    private final BigDecimal iptHigher;
    private final List<String> higherRateLines;

    public RatingService(PremiumEngineRouter router,
                         @Value("${policy.ipt.standard-rate}") BigDecimal iptStandard,
                         @Value("${policy.ipt.higher-rate}") BigDecimal iptHigher,
                         @Value("${policy.ipt.higher-rate-lines}") List<String> higherRateLines) {
        this.router = router;
        this.iptStandard = iptStandard;
        this.iptHigher = iptHigher;
        this.higherRateLines = higherRateLines;
    }

    public RatingResult rate(RatingInput input) {
        PremiumEngine engine = router.select();
        PremiumEngine.Priced priced = engine.price(input);
        BigDecimal base = priced.basePremium().setScale(2, RoundingMode.HALF_UP);
        BigDecimal ipt = base.multiply(iptRate(input.line())).setScale(2, RoundingMode.HALF_UP);
        BigDecimal excess = applyExcess(input.voluntaryExcess());
        return new RatingResult(base, ipt, base.add(ipt), excess, priced.referralReason(), engine.name());
    }

    /**
     * Total excess = compulsory 250 + voluntary, rounded HALF_UP to whole pounds.
     * (claims-service rounds DOWN and the mainframe still uses a compulsory 200.)
     */
    public BigDecimal applyExcess(BigDecimal voluntary) {
        BigDecimal v = voluntary == null ? BigDecimal.ZERO : voluntary.max(BigDecimal.ZERO);
        return COMPULSORY_EXCESS.add(v).setScale(0, RoundingMode.HALF_UP);
    }

    BigDecimal iptRate(ProductLine line) {
        return higherRateLines.contains(line.name()) ? iptHigher : iptStandard;
    }
}
