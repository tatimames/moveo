import json
import signal
from confluent_kafka import Consumer, KafkaException, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KafkaConsumerService:
    def __init__(self, bootstrap_servers, group_id, topics):
        self.consumer_config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
        }
        self.topics = topics
        self.consumer = Consumer(self.consumer_config)
        self.running = False

    def create_topics(self, num_partitions=1, replication_factor=1):
        """Create Kafka topics if they don't already exist."""
        admin_client = AdminClient({'bootstrap.servers': self.consumer_config['bootstrap.servers']})

        existing_topics = admin_client.list_topics(timeout=10).topics

        # Define new topics to create
        new_topics = [
            NewTopic(topic, num_partitions=num_partitions, replication_factor=replication_factor)
            for topic in self.topics if topic not in existing_topics
        ]

        if not new_topics:
            logging.info("All topics already exist.")
            return

        logging.info(f"Creating topics: {[t.topic for t in new_topics]}")
        future = admin_client.create_topics(new_topics)

        for topic, f in future.items():
            try:
                f.result()
                logging.info(f"Topic '{topic}' created successfully.")
            except KafkaException as e:
                logging.error(f"Failed to create topic '{topic}': {e}")
            except Exception as e:
                logging.error(f"Unexpected error when creating topic '{topic}': {e}")

    def start(self):
        """Start the Kafka consumer service."""
        try:
            self.consumer.subscribe(self.topics)
            logging.info(f"Subscribed to topics: {self.topics}")
            self.running = True

            while self.running:
                msg = self.consumer.poll(1.0) 

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logging.info(f"End of partition reached: {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                    else:
                        logging.error(f"Kafka error: {msg.error()}")
                    continue

                try:
                    message_value = json.loads(msg.value().decode('utf-8'))
                    logging.info(f"Received message from topic {msg.topic()}: {message_value}")
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to deserialize message: {e}")

        except Exception as e:
            logging.error(f"Error in Kafka consumer: {e}")

    def stop(self):
        """Stop the Kafka consumer service."""
        logging.info("Stopping Kafka consumer service...")
        self.running = False
        self.consumer.close()
        logging.info("Kafka consumer service stopped.")


def signal_handler(sig, frame, consumer_service):
    """Handle termination signals."""
    logging.info(f"Signal {sig} received, shutting down...")
    consumer_service.stop()

if __name__ == "__main__":
    BOOTSTRAP_SERVERS = "kafka:9092"
    GROUP_ID = "inventory_group"
    TOPICS = ["item_created", "item_updated"]

    consumer_service = KafkaConsumerService(BOOTSTRAP_SERVERS, GROUP_ID, TOPICS)
    consumer_service.create_topics()

    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, consumer_service))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, consumer_service))

    consumer_service.start()

    try:
        while True:
            signal.pause()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down...")
        consumer_service.stop()
