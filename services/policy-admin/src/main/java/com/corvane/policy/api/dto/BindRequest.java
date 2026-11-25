package com.corvane.policy.api.dto;

import java.time.LocalDate;

public record BindRequest(LocalDate inceptionDate, String brokerCode) {
}
