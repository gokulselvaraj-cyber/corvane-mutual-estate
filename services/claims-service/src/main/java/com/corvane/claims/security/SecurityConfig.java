package com.corvane.claims.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

/** JWT resource server; roles CUSTOMER, ADJUSTER, CLAIMS_MANAGER, BROKER come from the token (see TokenClaims). */
@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http, TokenClaims tokenClaims) throws Exception {
        http.csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health/**", "/actuator/info").permitAll()
                // TEMP for the MI reporting box until it gets a client credential (SEC-418, opened 2025-09).
                .requestMatchers("/v1/claims/export").permitAll()
                .requestMatchers("/v1/**").authenticated()
                .anyRequest().denyAll())
            .oauth2ResourceServer(oauth -> oauth.jwt(jwt -> jwt.jwtAuthenticationConverter(tokenClaims.converter())));
        return http.build();
    }
}
