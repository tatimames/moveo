# Inventory managment Application

## Overview
This project is a Kafka-powered microservice architecture designed as a inventory management service that allows creating, updating, retrieving, and deleting items from the inventory.

### Architecture Overview
The application follows a microservice architecture with the following components:

1. **App Service**:
   - A FastAPI application that exposes RESTful endpoints for operations on inventory items.
   - Sends messages to a Kafka broker upon creating or updating items.

2. **Consumer Service**:
   - A Kafka consumer service that listens to item-related events (e.g., `item_created` and `item_updated`) and processes them.

3. **PostgreSQL Database**:
   - A PostgreSQL container that serves as the persistent storage for the inventory data.
   - Contains an `items` table where inventory data is stored.

4. **Kafka Broker**:
   - A Kafka broker container that facilitates message queuing and event-driven communication between services.
   - Handles the `item_created` and `item_updated` topics.

5. **Zookeeper**:
   - A Zookeeper container required by Kafka for managing and coordinating the Kafka broker.


All services run in Docker containers, managed via `docker-compose` in the same network.

---

## Setup Instructions

### Prerequisites
Ensure you have the docker engine running.

### Steps to Run the Application

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Build and Start the Services**:
   ```bash
   docker-compose up --build
   ```
   This command will:
   - Build the Docker images for the app and consumer.
   - Start all containers (App, PostgreSQL, Kafka, Zookeeper, Consumer).

3. **Verify Services**:
   - Access the app at [http://localhost:5000] (Request the endpoints through Postman - endpoint info below)
   - Check the consumer container logs to check logs for the Kafka consumer.

---

## Testing the Application
### API Endpoints (App Service)
The App Service exposes the following endpoints:
You can test them using tools like [Postman] or `curl`.

#### 1. Get All Items
- **Endpoint**: `GET /items`
- **Description**: Retrieve a list of all inventory items.
- **Response**:
  ```json
  [
    {
      "id": 1,
      "name": "Laptop",
      "description": "A high-performance laptop"
    },
    {
      "id": 2,
      "name": "Smartphone",
      "description": "A modern smartphone"
    }
  ]
  ```

#### 2. Get Item by ID
- **Endpoint**: `GET /items/{id}`
- **Description**: Retrieve an item by its ID.
- **Response**:
  ```json
  {
    "id": 1,
    "name": "Laptop",
    "description": "A high-performance laptop"
  }
  ```

#### 3. Create Item
- **Endpoint**: `POST /items`
- **Description**: Create a new item and send a Kafka message to the `item_created` topic.
- **Request Body**:
  ```json
  {
    "name": "Tablet",
    "description": "A lightweight tablet"
  }
  ```
- **Response**:
  ```json
  {
    "id": 3,
    "name": "Tablet",
    "description": "A lightweight tablet"
  }
  ```

#### 4. Update Item
- **Endpoint**: `PUT /items/{id}`
- **Description**: Update an existing item and send a Kafka message to the `item_updated` topic.
- **Request Body**:
  ```json
  {
    "name": "Updated Laptop",
    "description": "An updated description"
  }
  ```
- **Response**:
  ```json
  {
    "id": 1,
    "name": "Updated Laptop",
    "description": "An updated description"
  }
  ```

#### 5. Delete Item
- **Endpoint**: `DELETE /items/{id}`
- **Description**: Delete an item by its ID.
- **Response**:
  ```json
  {
    "message": "Item deleted"
  }
  ```


## Notes
- Use the FastAPI Swagger UI ([http://localhost:5000/docs](http://localhost:5000/docs)) for interactive testing of endpoints.
- The app auto-creates kafka topics (`item_created`, `item_updated`) if they don’t exist.

