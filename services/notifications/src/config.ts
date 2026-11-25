export const config = {
  kafkaBrokers: (process.env.KAFKA_BOOTSTRAP ?? "kafka.corvane.internal:9092").split(","),
  smtp: {
    host: process.env.SMTP_HOST ?? "smtp.corvane.internal",
    port: Number(process.env.SMTP_PORT ?? 587),
    user: process.env.SMTP_USER ?? "notifications",
    password: process.env.SMTP_PASSWORD ?? "", // ${SMTP_PASSWORD}
    from: "Corvane Mutual Claims <claims@corvane.example>",
  },
  smsUrl: process.env.SMS_URL ?? "https://sms.textwave.example/v3/messages",
  smsApiKey: process.env.SMS_API_KEY ?? "", // ${SMS_API_KEY}
  portalUrl: process.env.PORTAL_URL ?? "https://my.corvane.example",
};
