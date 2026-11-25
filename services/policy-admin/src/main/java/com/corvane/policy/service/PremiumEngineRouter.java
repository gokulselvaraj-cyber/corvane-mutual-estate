package com.corvane.policy.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Migration seam (ADR-0009 "strangle the mainframe rating engine").
 *
 * <p>{@code policy.premium-engine} chooses the engine at runtime: {@code mainframe} sends the request through the
 * CICS Transaction Gateway to PRMCALC0; {@code java} uses the Java port. Profiles: dev=java, test=java,
 * prod=mainframe.</p>
 */
@Component
public class PremiumEngineRouter {

    private static final Logger log = LoggerFactory.getLogger(PremiumEngineRouter.class);

    private final JavaRatingService javaEngine;
    private final MainframePremiumAdapter mainframeEngine;
    private final String selected;

    public PremiumEngineRouter(JavaRatingService javaEngine, MainframePremiumAdapter mainframeEngine,
                               @Value("${policy.premium-engine:java}") String selected) {
        this.javaEngine = javaEngine;
        this.mainframeEngine = mainframeEngine;
        this.selected = selected;
        log.info("Premium engine selected: {}", selected);
    }

    public PremiumEngine select() {
        return switch (selected) {
            case "mainframe" -> mainframeEngine;
            case "java" -> javaEngine;
            default -> throw new IllegalStateException("Unknown policy.premium-engine: " + selected);
        };
    }
}
