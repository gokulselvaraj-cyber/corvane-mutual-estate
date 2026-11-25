package com.corvane.policy.service;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;

class PremiumEngineRouterTest {

    private final JavaRatingService javaEngine = mock(JavaRatingService.class);
    private final MainframePremiumAdapter mainframe = mock(MainframePremiumAdapter.class);

    @Test
    void javaFlagSelectsJavaPort() {
        assertThat(new PremiumEngineRouter(javaEngine, mainframe, "java").select()).isSameAs(javaEngine);
    }

    @Test
    void mainframeFlagSelectsCtgAdapter() {
        assertThat(new PremiumEngineRouter(javaEngine, mainframe, "mainframe").select()).isSameAs(mainframe);
    }

    @Test
    void unknownFlagFailsFast() {
        assertThatThrownBy(() -> new PremiumEngineRouter(javaEngine, mainframe, "cobol").select())
                .isInstanceOf(IllegalStateException.class);
    }
}
