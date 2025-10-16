from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderType(str, Enum):
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Customer(SQLModel, table=True):
    __tablename__ = "customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    phone_number: str = Field(unique=True, index=True)
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    orders: List["Order"] = Relationship(back_populates="customer")
    complaints: List["Complaint"] = Relationship(back_populates="customer")
    reservations: List["Reservation"] = Relationship(back_populates="customer")
    conversations: List["ConversationHistory"] = Relationship(back_populates="customer")


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id")
    order_type: OrderType
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    items: str  # JSON string of items
    total_price: float
    delivery_address: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    estimated_completion_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    feedback_requested: bool = Field(default=False)
    feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: Customer = Relationship(back_populates="orders")


class Complaint(SQLModel, table=True):
    __tablename__ = "complaints"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id")
    description: str
    status: str = Field(default="open")  # open, in_progress, resolved
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    # Relationships
    customer: Customer = Relationship(back_populates="complaints")


class Reservation(SQLModel, table=True):
    __tablename__ = "reservations"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id")
    reservation_date: datetime
    number_of_people: int
    special_requests: Optional[str] = None
    status: str = Field(default="pending")  # pending, confirmed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: Customer = Relationship(back_populates="reservations")


class ConversationHistory(SQLModel, table=True):
    __tablename__ = "conversation_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customers.id")
    role: str  # user, assistant, or system
    message: str
    prompt_sent: Optional[str] = None  # Full prompt sent to Gemini (for assistant messages)
    tokens_input: Optional[int] = None  # Input tokens used
    tokens_output: Optional[int] = None  # Output tokens used
    cost_pkr: Optional[float] = None  # Cost in PKR
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: Customer = Relationship(back_populates="conversations")


class MenuItem(SQLModel, table=True):
    __tablename__ = "menu_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    category: str
    item_name: str
    price: float
    price_with_tax: float
    description: Optional[str] = None
    options: Optional[str] = None
    synonyms: Optional[str] = None
    serving: float
    created_at: datetime = Field(default_factory=datetime.utcnow)