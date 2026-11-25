import { Kafka } from "kafkajs";
import { ClaimRegisteredHandler } from "./handlers/claimRegisteredHandler";
import { PolicyBoundHandler } from "./handlers/policyBoundHandler";
import { Mailer } from "./channels/mailer";
import { SmsClient } from "./channels/smsClient";
import { config } from "./config";

async function main(): Promise<void> {
  const kafka = new Kafka({ clientId: "notifications", brokers: config.kafkaBrokers });
  const consumer = kafka.consumer({ groupId: "notifications" });
  const mailer = new Mailer(config.smtp);
  const sms = new SmsClient(config.smsUrl, config.smsApiKey);
  const handlers: Record<string, { handle(evt: any): Promise<void> }> = {
    "claims.registered.v1": new ClaimRegisteredHandler(mailer, sms),
    "policies.bound.v1": new PolicyBoundHandler(mailer),
  };
  await consumer.connect();
  await consumer.subscribe({ topics: Object.keys(handlers), fromBeginning: false });
  await consumer.run({
    eachMessage: async ({ topic, message }) => {
      const evt = JSON.parse(message.value?.toString() ?? "{}");
      await handlers[topic].handle(evt);
    },
  });
}

main().catch((err) => {
  console.error("notifications stopped", err);
  process.exit(1);
});
