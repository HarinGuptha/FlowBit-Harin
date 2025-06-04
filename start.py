#!/usr/bin/env python3
"""
Startup script for the Multi-Format Autonomous AI System.
Handles initialization, health checks, and graceful startup.
"""
import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from core.memory_store import get_memory_store


def setup_logging():
    """Setup logging configuration."""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/startup.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


async def check_dependencies():
    """Check system dependencies and external services."""
    logger = logging.getLogger(__name__)
    
    logger.info("Checking system dependencies...")
    
    # Check Redis connection
    try:
        memory_store = await get_memory_store()
        await memory_store.redis_client.ping()
        logger.info("✅ Redis connection successful")
        await memory_store.disconnect()
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.error("Please ensure Redis is running on the configured host/port")
        return False
    
    # Check required directories
    required_dirs = ['logs', 'uploads', 'static', 'templates']
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"✅ Directory created/verified: {directory}")
    
    # Check environment variables
    required_env_vars = ['REDIS_HOST', 'REDIS_PORT']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Using default values - consider setting these in .env file")
    
    logger.info("✅ All dependency checks completed")
    return True


async def initialize_system():
    """Initialize all system components."""
    logger = logging.getLogger(__name__)
    
    logger.info("Initializing Multi-Format Autonomous AI System...")
    
    try:
        # Import and initialize core components
        from core.memory_store import get_memory_store
        from core.action_router import get_action_router
        
        # Initialize memory store
        memory_store = await get_memory_store()
        logger.info("✅ Memory store initialized")
        
        # Initialize action router
        action_router = await get_action_router()
        logger.info("✅ Action router initialized")
        
        # Import and initialize agents
        from agents import (
            get_classifier_agent, get_email_agent, 
            get_json_agent, get_pdf_agent
        )
        
        await get_classifier_agent()
        logger.info("✅ Classifier agent initialized")
        
        await get_email_agent()
        logger.info("✅ Email agent initialized")
        
        await get_json_agent()
        logger.info("✅ JSON agent initialized")
        
        await get_pdf_agent()
        logger.info("✅ PDF agent initialized")
        
        # Initialize system counters
        await memory_store.increment_counter("system_startups")
        start_time = time.time()
        await memory_store.store_agent_state("system", {
            "status": "running",
            "start_time": start_time,
            "version": "1.0.0"
        })
        
        logger.info("🚀 System initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {e}")
        return False


def print_banner():
    """Print system banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    Multi-Format Autonomous AI System                        ║
║    Contextual Decisioning & Chained Actions                 ║
║                                                              ║
║    🤖 Advanced Multi-Agent Processing                        ║
║    📧 Email Analysis & Escalation                           ║
║    📊 JSON Validation & Anomaly Detection                   ║
║    📄 PDF Parsing & Compliance Checking                     ║
║    🔗 Dynamic Action Chaining                               ║
║                                                              ║
║    Built for Flowbit AI Assessment                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_startup_info():
    """Print startup information."""
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', 8000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"""
🌐 Server Configuration:
   Host: {host}
   Port: {port}
   Debug Mode: {debug}
   
🔗 Access URLs:
   Web Interface: http://localhost:{port}
   API Documentation: http://localhost:{port}/api/docs
   Health Check: http://localhost:{port}/api/health
   
📊 Monitoring:
   Redis Commander: http://localhost:8081 (if enabled)
   System Stats: http://localhost:{port}/api/stats
   
🚀 System Status: Starting...
""")


async def main():
    """Main startup function."""
    # Setup logging
    logger = setup_logging()
    
    # Print banner
    print_banner()
    print_startup_info()
    
    # Check dependencies
    logger.info("Starting dependency checks...")
    if not await check_dependencies():
        logger.error("❌ Dependency checks failed. Exiting.")
        sys.exit(1)
    
    # Initialize system
    logger.info("Starting system initialization...")
    if not await initialize_system():
        logger.error("❌ System initialization failed. Exiting.")
        sys.exit(1)
    
    # Start the web server
    logger.info("Starting FastAPI server...")
    
    try:
        config = uvicorn.Config(
            "main:app",
            host=os.getenv('APP_HOST', '0.0.0.0'),
            port=int(os.getenv('APP_PORT', 8000)),
            reload=os.getenv('DEBUG', 'True').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'info').lower(),
            access_log=True
        )
        
        server = uvicorn.Server(config)
        
        logger.info("🎉 Multi-Format Autonomous AI System is ready!")
        logger.info("Press Ctrl+C to stop the server")
        
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown signal received")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)
    finally:
        logger.info("🔄 Performing cleanup...")
        try:
            memory_store = await get_memory_store()
            await memory_store.store_agent_state("system", {
                "status": "stopped",
                "stop_time": time.time()
            })
            await memory_store.disconnect()
            logger.info("✅ Cleanup completed")
        except:
            pass
        
        logger.info("👋 Multi-Format Autonomous AI System stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        sys.exit(1)
