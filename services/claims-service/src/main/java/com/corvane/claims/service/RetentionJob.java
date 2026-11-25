package com.corvane.claims.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Monthly retention run for claimsdb. The retention period itself lives in the database routine
 * claims.purge_expired_claims(); this job only calls it. pg_cron runs the same routine weekly (see
 * data/postgres/003_claims_functions.sql); this call is the safety net for when pg_cron is paused, and it also
 * removes claim_document rows left without a claim by the 2024 migration (loaded with foreign keys disabled).
 */
@Service
public class RetentionJob {

    private static final Logger log = LoggerFactory.getLogger(RetentionJob.class);

    private final JdbcTemplate jdbc;

    public RetentionJob(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Scheduled(cron = "0 30 3 1 * *", zone = "Europe/London")
    @Transactional
    public void run() {
        Integer purged = jdbc.queryForObject("SELECT claims.purge_expired_claims()", Integer.class);
        int orphans = jdbc.update(
                "DELETE FROM claims.claim_document WHERE claim_id NOT IN (SELECT id FROM claims.claim)");
        log.info("retention run: {} claims purged, {} orphan document rows removed", purged, orphans);
    }
}
