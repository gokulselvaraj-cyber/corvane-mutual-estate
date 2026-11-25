package com.corvane.claims.repository;

import com.corvane.claims.domain.Claim;
import com.corvane.claims.domain.ClaimStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ClaimRepository extends JpaRepository<Claim, UUID> {
    Optional<Claim> findByClaimNumber(String claimNumber);
    List<Claim> findByStatus(ClaimStatus status);
    @Query("select c from Claim c where c.registeredAt >= ?1 order by c.registeredAt desc")
    List<Claim> findRegisteredSince(OffsetDateTime since);
    @Query(value = "select nextval('claims.claim_number_seq')", nativeQuery = true)
    long nextClaimNumber();
}
