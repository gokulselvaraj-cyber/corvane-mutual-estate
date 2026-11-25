FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/claims-service.jar app.jar
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=30s CMD wget -qO- http://localhost:8080/actuator/health/readiness || exit 1
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app/app.jar"]
