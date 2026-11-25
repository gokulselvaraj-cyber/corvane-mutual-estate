# Kafka runs on Confluent Cloud; topics are declared here through the Confluent provider module.
module "kafka_topics" {
  source      = "./modules/kafka-topics"
  environment = var.environment
  topics = {
    "policies.bound.v1"    = { partitions = 6, retention_hours = 168 }
    "claims.registered.v1" = { partitions = 12, retention_hours = 168 }
    "claims.approved.v1"   = { partitions = 6, retention_hours = 336 }
    "payments.settled.v1"  = { partitions = 6, retention_hours = 336 }
    "claims.closed.v1"     = { partitions = 6, retention_hours = 168 }
    "claims.reopened.v1"   = { partitions = 3, retention_hours = 168 }
  }
}
