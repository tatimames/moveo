from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel
from confluent_kafka import Producer
import uvicorn
import os
import json

DATABASE_URL = 'postgresql+psycopg2://user:password@postgres_db_container/inventory_db'

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

try:
    with engine.connect() as connection:
        print("Connection successful")
except Exception as e:
    print("Connection failed:", e)

# Model
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# Pydantic schemas
class ItemBase(BaseModel):
    name: str
    description: str | None = None

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: int

    class Config:
        from_attributes = True

# Kafka producer setup
kafka_config = {
    'bootstrap.servers': 'kafka:9092'
}
producer = Producer(kafka_config)

def send_kafka_message(topic: str, message: dict):
    try:
        producer.produce(topic, value=json.dumps(message))
        producer.flush()
        print(f"Message sent to Kafka topic {topic}: {message}")
    except Exception as e:
        print(f"Failed to send Kafka message: {e}")

# FastAPI app
app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@app.get("/items", response_model=list[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items

@app.post("/items", response_model=ItemResponse)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    send_kafka_message("item_created", {"id": db_item.id, "name": db_item.name, "description": db_item.description})
    return db_item

@app.get("/items/{id}", response_model=ItemResponse)
def get_item(id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.delete("/items/{id}", status_code=204)
def delete_item(id: int, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}

@app.put("/items/{id}", response_model=ItemResponse)
def update_item(id: int, item: ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(Item).filter(Item.id == id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.name = item.name
    db_item.description = item.description
    db.commit()
    db.refresh(db_item)

    send_kafka_message("item_updated", {"id": db_item.id, "name": db_item.name, "description": db_item.description})
    return db_item


@app.on_event("startup")
def startup_event():
    retries = 5
    while retries > 0:
        try:
            db = SessionLocal()
            if not db.query(Item).count():
                initial_items = [
                    Item(name="Laptop", description="A high-performance laptop"),
                    Item(name="Smartphone", description="A modern smartphone"),
                    Item(name="Tablet", description="A lightweight tablet"),
                ]
                db.bulk_save_objects(initial_items)
                db.commit()
                print("Database initialized with initial items.")
            else:
                print("Database already initialized.")
            db.close()
            break
        except OperationalError:
            print("Database not ready, retrying...")
            retries -= 1
        except Exception as e:
            print(f"Unexpected error during initialization: {e}")
            break


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
