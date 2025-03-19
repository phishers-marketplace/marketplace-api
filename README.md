# Phishers Marketplace API

A FastAPI-based backend for the Phishers Marketplace platform.

## Project Overview

This API serves as the backend for the Phishers Marketplace, providing endpoints for user management, product listings, and transactions.

## Tech Stack

- **Python 3.11+**
- **FastAPI**: Modern, fast web framework for building APIs
- **MongoDB**: NoSQL database (via Motor and Beanie ODM)
- **OAuth2 with JWT**: Industry-standard authentication using JSON Web Tokens
- **Poetry**: Dependency management

## Project Structure

```
marketplace-api/
├── src/
│   ├── api.py                # Main FastAPI application
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Configuration settings
│   │   └── db.py             # Database connection
│   └── business/             # Business logic modules
│       └── user/             # User-related functionality
├── .env                      # Environment variables
├── pyproject.toml           # Project dependencies
└── poetry.lock              # Locked dependencies
```

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- Poetry (dependency management)
- MongoDB (local or cloud instance)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/phishers-marketplace/marketplace-api.git
   cd marketplace-api
   ```

2. Create a poetry environment:
    ```bash
    poetry env use python3
    ```

3. Activate the environment:
    ```bash
    eval $(poetry env activate)
    ```

4. Install dependencies using Poetry:
   ```bash
   poetry install --with-dev
   ```

5. Set up pre-commit hooks:
    ```bash
    pre-commit install
    ```

6. Create a `.env` file in the root directory (Look at the `.env.sample` file for an example)

### Running the API

1. Start the API server:
   ```bash
   python src/api.py
   ```

2. The API will be available at: `http://localhost:9000`

3. Access the API documentation at: `http://localhost:9000/docs`

## Docker Deployment

### Prerequisites

- Docker and Docker Compose installed on your system
- Git for cloning the repository

### Deploying with Docker Compose

1. Clone the repository:
   ```bash
   git clone https://github.com/phishers-marketplace/marketplace-api.git
   cd marketplace-api
   ```

2. Create a `.env` file in the root directory (Look at the `.env.sample` file for an example)

3. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

4. The API will be available at: `http://localhost:9000`

5. Access the API documentation at: `http://localhost:9000/docs`

### Viewing Logs

To see the logs from the running containers:
```bash
docker-compose logs -f
```

To see logs for a specific service:
```bash
docker-compose logs -f api
```

### Stopping the Services

To stop the running containers:
```bash
docker-compose down
```

To stop the containers and remove the volumes (will delete all data):
```bash
docker-compose down -v
```

### Rebuilding the API

If you make changes to the code and need to rebuild the API:
```bash
docker-compose build api
docker-compose up -d
```

## Development

### Adding New Endpoints

The project follows a modular structure to organize code. Here's a step-by-step guide for adding new functionality:

1. **Create a new module directory** in the `src/business` directory
   ```bash
   mkdir -p src/business/your_feature
   touch src/business/your_feature/__init__.py
   ```

2. **Define your database models** in `models.py`
   - These are MongoDB document models created using Beanie ODM
   - They represent the structure of your data in the database
   - Example:
   ```python
   # src/business/your_feature/models.py
   from beanie import Document
   from pydantic import Field
   from datetime import datetime
   
   class Product(Document):
       name: str
       description: str
       price: float
       created_at: datetime = Field(default_factory=datetime.utcnow)
       
       class Settings:
           name = "products"  # Collection name in MongoDB
   ```

3. **Create API schemas** in `schemas.py`
   - These are Pydantic models that define the structure of request/response data
   - They provide automatic validation and documentation
   - Example:
   ```python
   # src/business/your_feature/schemas.py
   from pydantic import BaseModel, Field
   from datetime import datetime
   
   class ProductCreate(BaseModel):
       name: str
       description: str
       price: float
   
   class ProductResponse(BaseModel):
       id: str
       name: str
       description: str
       price: float
       created_at: datetime
   ```

4. **Create service functions** in `service.py` (optional)
   - These handle dependency injections mainly

5. **Define your API routes** in `routes.py`
   - Create a FastAPI router with your endpoints
   - Use your schemas for request/response models
   - Example:
   ```python
   # src/business/your_feature/routes.py
   from fastapi import APIRouter, HTTPException, Depends
   from .schemas import ProductCreate, ProductResponse
   from .service import get_product_by_id, create_product
   
   router = APIRouter(prefix="/products", tags=["Products"])
   
   @router.post("/", response_model=ProductResponse)
   async def create_new_product(product_data: ProductCreate):
       product = Product(name=product_data.name, description=product_data.description, price=product_data.price)
       await product.insert()
       return product
   
   @router.get("/{product_id}", response_model=ProductResponse)
   async def get_product(product_id: str):
       product = await Product.get(product_id)
       if not product:
           raise HTTPException(status_code=404, detail="Product not found")
       return product
   ```

6. Export this router using `__init__.py`
    - Example:
    ```python
    # src/business/__init__.py
    from .routes import router
    ```

7. **Include your router in the main API file**
   - Open `src/api.py`
   - Import your router and add it to the FastAPI app
   - Example:
   ```python
   # In src/api.py
   from business import router as product_router
   
   # Add this line after the app is created
   app.include_router(product_router)
   ```

8. **Register your models with Beanie**
   - Update the `init_db` function in `src/core/db.py` to include your models
   - Example:
   ```python
   # In src/core/db.py, update the init_beanie call:
   from business.your_feature.models import Product
   
   # Inside init_db function:
   await init_beanie(database=db, document_models=[Product])
   ```

After completing these steps, your new endpoints will be available through the API and automatically documented in the Swagger UI.

## API Documentation

Once the server is running, you can access the auto-generated API documentation:

- Swagger UI: `http://localhost:9000/docs`
- ReDoc: `http://localhost:9000/redoc`