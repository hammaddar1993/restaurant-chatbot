# Restaurant WhatsApp Chatbot

A production-ready, AI-powered WhatsApp chatbot for restaurant operations built with FastAPI, PostgreSQL, Redis, and Google Gemini AI.

## Features

- 🤖 **AI-Powered Conversations**: Natural language understanding using Gemini 2.0 Flash
- 📱 **WhatsApp Integration**: Full WhatsApp Cloud API support for text and location messages
- 🍔 **Order Management**: Handle dine-in, takeaway, and delivery orders
- 📅 **Table Reservations**: Manage restaurant table bookings
- 💬 **Complaint Handling**: Track and respond to customer complaints
- 📊 **Order Tracking**: Real-time order status updates with estimated completion times
- ⭐ **Feedback Collection**: Automatic feedback requests after order completion
- 🔄 **Session Management**: Redis-based conversation context with configurable timeouts
- 💾 **Persistent Storage**: PostgreSQL for all customer data and transaction history
- 🐳 **Containerized**: Docker and Docker Compose for easy deployment

## Architecture

```
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   └── database.py        # Database setup
│   ├── models/
│   │   └── database_models.py # SQLModel database models
│   ├── routes/
│   │   └── webhook.py         # WhatsApp webhook handler
│   └── services/
│       ├── redis_service.py   # Session management
│       ├── whatsapp_service.py # WhatsApp API integration
│       ├── gemini_service.py  # AI response generation
│       ├── customer_service.py # Customer data management
│       ├── order_service.py   # Order management
│       ├── complaint_service.py # Complaint handling
│       └── reservation_service.py # Reservation management
├── scripts/
│   └── init_menu.py           # Menu initialization script
├── main.py                    # Application entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- WhatsApp Business API account
- Google Gemini API key

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd restaurant-chatbot
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://restaurant_user:restaurant_pass@postgres:5432/restaurant_db

# Redis
REDIS_URL=redis://redis:6379/0

# WhatsApp Cloud API
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_VERIFY_TOKEN=your_verify_token

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite

# Session Configuration
SESSION_TIMEOUT_MINUTES=60
FEEDBACK_DELAY_MINUTES=30
```

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis server
- FastAPI application

### 4. Initialize Menu

```bash
docker-compose exec app python scripts/init_menu.py
```

### 5. Configure WhatsApp Webhook

Set your webhook URL in WhatsApp Business API dashboard:
```
https://your-domain.com/webhook/
```

Verify token: Use the same value as `WHATSAPP_VERIFY_TOKEN` in your `.env` file

## API Endpoints

### Webhook Endpoints

- `GET /webhook/` - Webhook verification
- `POST /webhook/` - Receive WhatsApp messages

### Health Check

- `GET /` - Root endpoint
- `GET /health` - Health check

## Database Schema

### Customers
- Stores customer information (phone, name, address, location)
- Links to all orders, complaints, reservations, and conversations

### Orders
- Order details with items, pricing, and status
- Supports dine-in, takeaway, and delivery
- Tracks estimated completion time and feedback

### Complaints
- Customer complaint tracking
- Status management (open, in_progress, resolved)

### Reservations
- Table reservation management
- Date, party size, and special requests

### Conversation History
- Full conversation logs for each customer
- Enables context-aware responses

### Menu Items
- Complete menu with categories, prices, and descriptions
- Supports synonyms for better AI understanding

## Session Management

Sessions are stored in Redis with the following features:

- **Auto-expiry**: Sessions expire after 60 minutes of inactivity (configurable)
- **Context retention**: Maintains conversation history and order state
- **Efficient storage**: Only recent context kept in Redis, full history in PostgreSQL

## AI Capabilities

The Gemini AI integration provides:

1. **Natural Language Understanding**: Interprets customer intent
2. **Contextual Responses**: Maintains conversation flow
3. **Structured Action Extraction**: Identifies when to create orders, reservations, etc.
4. **Menu Knowledge**: Full awareness of available items and pricing
5. **Order Tracking**: Provides status updates and estimates

## Order Tracking Flow

1. Customer places order → Status: PENDING
2. Order preparation begins → Status: PREPARING
3. Order ready → Status: READY
4. Order completed → Status: COMPLETED
5. After 30 minutes → Automatic feedback request

## Delivery Order Flow

1. Customer requests delivery order
2. Bot asks for delivery address
3. Bot requests location sharing (GPS coordinates)
4. Address and location stored with order
5. Order created with delivery details

## Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/restaurant_db
export REDIS_URL=redis://localhost:6379/0
# ... other variables

# Run the application
uvicorn main:app --reload
```

### Running Tests

```bash
# Add your test commands here
pytest
```

## Monitoring and Logs

### View Application Logs

```bash
docker-compose logs -f app
```

### View Database Logs

```bash
docker-compose logs -f postgres
```

### View Redis Logs

```bash
docker-compose logs -f redis
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Connect to database
docker-compose exec postgres psql -U restaurant_user -d restaurant_db
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Webhook Not Receiving Messages

1. Verify webhook URL is correctly configured in WhatsApp dashboard
2. Ensure your server is publicly accessible
3. Check verify token matches your configuration
4. Review application logs for errors

## Production Deployment

### Security Considerations

1. Use strong passwords for database
2. Keep API keys secure and never commit to version control
3. Use HTTPS for webhook endpoint
4. Implement rate limiting
5. Monitor for unusual activity

### Scaling

- **Horizontal scaling**: Run multiple app instances behind a load balancer
- **Database**: Use connection pooling and read replicas
- **Redis**: Use Redis Cluster for high availability
- **Caching**: Implement cachiZng for menu items

### Backup

```bash
# Backup PostgreSQL database
docker-compose exec postgres pg_dump -U restaurant_user restaurant_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U restaurant_user restaurant_db < backup.sql
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub or contact the development team.

## Acknowledgments

- FastAPI for the excellent web framework
- Google Gemini for AI capabilities
- WhatsApp Cloud API for messaging infrastructure