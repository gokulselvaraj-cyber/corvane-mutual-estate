package com.corvane.policy.config;

import com.zaxxer.hikari.HikariDataSource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;
import java.time.Clock;

@Configuration
public class LedgerDataSourceConfig {

    @Bean(name = "ledgerDataSource")
    DataSource ledgerDataSource(@Value("${ledger.url}") String url, @Value("${ledger.username}") String user,
                                @Value("${ledger.password}") String password) {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl(url);
        ds.setUsername(user);
        ds.setPassword(password);
        ds.setMaximumPoolSize(5);
        ds.setPoolName("ledger");
        return ds;
    }

    @Bean
    Clock clock() { return Clock.systemUTC(); }
}
