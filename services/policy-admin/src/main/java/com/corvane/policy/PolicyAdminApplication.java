package com.corvane.policy;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@ConfigurationPropertiesScan
@EnableScheduling
public class PolicyAdminApplication {
    public static void main(String[] args) {
        SpringApplication.run(PolicyAdminApplication.class, args);
    }
}
