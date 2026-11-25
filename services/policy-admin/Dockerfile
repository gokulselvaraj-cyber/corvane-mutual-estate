FROM eclipse-temurin:17-jre-alpine
LABEL org.opencontainers.image.source="services/policy-admin" team="policy-core"
RUN addgroup -S corvane && adduser -S policy -G corvane
WORKDIR /app
COPY target/policy-admin-*.jar app.jar
USER policy
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/actuator/health/readiness || exit 1
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app/app.jar"]
