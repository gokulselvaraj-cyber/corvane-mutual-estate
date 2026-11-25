package com.corvane.policy.repository;

import com.corvane.policy.domain.Policy;
import com.corvane.policy.domain.PolicyStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface PolicyRepository extends JpaRepository<Policy, Long> {

    Optional<Policy> findByPolicyNumber(String policyNumber);

    @Query("select p from Policy p where p.status = :status and p.expiryDate between :from and :to")
    List<Policy> findExpiring(PolicyStatus status, LocalDate from, LocalDate to);

    @Query(value = "select nextval('policy_number_seq')", nativeQuery = true)
    long nextPolicySequence();
}
