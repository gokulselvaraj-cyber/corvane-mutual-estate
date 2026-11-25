package com.corvane.claims.security;

import org.springframework.core.convert.converter.Converter;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Reads the JWT claims (token claims, NOT insurance claims) issued by https://login.corvane.internal:
 * "corvane_roles" -> Spring roles, "broker_id" for BROKER users.
 */
@Component
public class TokenClaims {

    public static final String ROLES_CLAIM = "corvane_roles";
    public static final String BROKER_CLAIM = "broker_id";

    public Converter<Jwt, AbstractAuthenticationToken> converter() {
        return jwt -> {
            List<String> roles = jwt.getClaimAsStringList(ROLES_CLAIM);
            var authorities = (roles == null ? List.<String>of() : roles).stream()
                    .map(r -> new SimpleGrantedAuthority("ROLE_" + r)).toList();
            return new JwtAuthenticationToken(jwt, authorities, jwt.getSubject());
        };
    }
}
