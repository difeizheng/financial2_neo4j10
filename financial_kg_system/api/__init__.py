"""
Main API Application
Sets up the FastAPI application and includes routes
"""

import os
from fastapi import FastAPI
from .routes import router

# Create the main application
app = FastAPI(
    title="Financial Knowledge Graph System API",
    description="API for Excel-based Financial Model Knowledge Graph System with LLM Integration",
    version="0.1.0"
)

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routes
app.include_router(router, prefix="/api/v1", tags=["financial-model"])

# Additional configuration can be added here
# For example, middleware, event handlers, etc.