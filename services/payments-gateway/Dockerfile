FROM golang:1.22 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=1 go build -o /out/payments-gateway ./cmd/payments-gateway

FROM gcr.io/distroless/base-debian12
COPY --from=build /out/payments-gateway /payments-gateway
EXPOSE 8085
USER 10001
ENTRYPOINT ["/payments-gateway"]
