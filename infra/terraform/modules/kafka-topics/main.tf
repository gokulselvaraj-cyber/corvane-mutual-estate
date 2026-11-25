variable "environment" {
  type = string
}

variable "topics" {
  type = map(object({ partitions = number, retention_hours = number }))
}

resource "confluent_kafka_topic" "this" {
  for_each         = var.topics
  topic_name       = each.key
  partitions_count = each.value.partitions
  config = {
    "retention.ms"   = tostring(each.value.retention_hours * 3600000)
    "cleanup.policy" = "delete"
  }
}
