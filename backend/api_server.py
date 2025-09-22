"""
Enhanced API Server for Dental Call Analysis Dashboard
Now includes Coaching Library functionality
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import List, Dict
import uvicorn
import sys
import os
from contextlib import asynccontextmanager

# Add the current directory to Python path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import settings and services
from config.settings import settings
from services.employee_list_service import EmployeeListService
from services.llm_analyzer import LLMAnalyzer
from services.data_loader import DataLoader

# Try to import coaching routes - with error handling
try:
    from api.coaching_api_routes import coaching_router
    COACHING_AVAILABLE = True
    print("✅ Coaching routes imported successfully")
except ImportError as e:
    print(f"❌ Failed to import coaching routes: {e}")
    COACHING_AVAILABLE = False
    coaching_router = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
employee_service = EmployeeListService()
llm_analyzer = LLMAnalyzer()
data_loader = DataLoader()

# Initialize coaching service
coaching_service = None

async def initialize_coaching_service():
    """Initialize coaching service with LLM analyzer"""
    global coaching_service
    try:
        await llm_analyzer.initialize()
        # Import CoachingService here to avoid circular imports
        from services.coaching_service import CoachingService
        coaching_service = CoachingService(llm_analyzer)
        logger.info("Coaching service initialized successfully")
    except Exception as e:
        logger.warning(f"Coaching service initialization failed: {str(e)}")
        coaching_service = None

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("Starting Dental Call Analysis API with Coaching Library...")
    
    # Initialize coaching service
    await initialize_coaching_service()
    
    # Log initial status
    employee_stats = employee_service.get_employee_stats()
    visible_employees = employee_service.get_visible_employees()
    hidden_employees = employee_service.get_hidden_employees()
    
    logger.info(f"Employee service: {employee_stats['active_employees']} active employees")
    logger.info(f"Visible employees: {len(visible_employees)}")
    if hidden_employees:
        logger.info(f"Hidden employees: {len(hidden_employees)}")
    
    logger.info(f"Coaching service: {'Available' if coaching_service else 'Unavailable'}")
    logger.info(f"Coaching routes: {'Available' if COACHING_AVAILABLE else 'Unavailable'}")
    logger.info("API server startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API server...")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Dental Call Analysis API",
    description="API for dental call analysis dashboard with coaching library",
    version="3.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for existing API
from pydantic import BaseModel

class EmployeeRequest(BaseModel):
    name: str

class EmployeeActionRequest(BaseModel):
    name: str

class EmployeeData(BaseModel):
    name: str
    active: bool
    hidden: bool
    added_date: str = None
    hidden_date: str = None
    shown_date: str = None
    removed_date: str = None

class EmployeeListResponse(BaseModel):
    employees: List[EmployeeData]
    stats: Dict
    visible_employees: List[str]
    hidden_employees: List[str]

class EmployeeActionResponse(BaseModel):
    success: bool
    message: str
    employees: List[EmployeeData]
    stats: Dict

# Include coaching routes ONLY if available
if COACHING_AVAILABLE and coaching_router:
    app.include_router(coaching_router)
    logger.info("Coaching routes registered successfully")
else:
    logger.warning("Coaching routes not available - running without coaching features")

# Existing API Routes

@app.get("/")
async def root():
    """API health check"""
    stats = employee_service.get_employee_stats()
    coaching_status = "available" if (COACHING_AVAILABLE and coaching_service) else "unavailable"
    
    return {
        "status": "running",
        "message": "Dental Call Analysis API v3.0 with Coaching Library",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "employee_management", 
            "hide_show_employees", 
            "dashboard_data",
            "coaching_library" if COACHING_AVAILABLE else None,
            "case_study_generation" if COACHING_AVAILABLE else None,
            "pdf_training_materials" if COACHING_AVAILABLE else None
        ],
        "employee_stats": stats,
        "coaching_service": coaching_status,
        "coaching_routes_imported": COACHING_AVAILABLE,
        "endpoints": {
            "employees": "/api/employees",
            "dashboard": "/api/dashboard/data",
            "coaching": "/api/coaching/*" if COACHING_AVAILABLE else "unavailable"
        }
    }

# Test endpoint for coaching system
@app.get("/api/coaching/test")
async def test_coaching_system():
    """Test endpoint to verify coaching system is working"""
    try:
        # Test data loader
        calls = await data_loader.load_all_calls()
        
        return {
            "status": "success",
            "coaching_available": COACHING_AVAILABLE,
            "coaching_service": coaching_service is not None,
            "data_loader_working": True,
            "calls_found": len(calls),
            "sample_call": calls[0] if calls else None,
            "message": "Coaching system is working correctly"
        }
    except Exception as e:
        logger.error(f"Coaching system test failed: {str(e)}")
        return {
            "status": "error",
            "coaching_available": COACHING_AVAILABLE,
            "coaching_service": coaching_service is not None,
            "data_loader_working": False,
            "error": str(e),
            "message": "Coaching system has issues"
        }

# Enhanced Employee Management Endpoints

@app.get("/api/employees", response_model=EmployeeListResponse)
async def get_employees():
    """Get complete employee list with all data"""
    try:
        employees_data = employee_service.get_employees_data()
        stats = employee_service.get_employee_stats()
        visible_employees = employee_service.get_visible_employees()
        hidden_employees = employee_service.get_hidden_employees()
        
        employees = [EmployeeData(**emp) for emp in employees_data]
        
        logger.info(f"Retrieved {len(employees)} employees ({stats['visible_employees']} visible, {stats['hidden_employees']} hidden)")
        
        return EmployeeListResponse(
            employees=employees,
            stats=stats,
            visible_employees=visible_employees,
            hidden_employees=hidden_employees
        )
    except Exception as e:
        logger.error(f"Error getting employees: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve employees")

@app.get("/api/employees/visible")
async def get_visible_employees():
    """Get only visible employees (for LLM prompts and coaching)"""
    try:
        visible_employees = employee_service.get_visible_employees()
        return {
            "visible_employees": visible_employees,
            "count": len(visible_employees)
        }
    except Exception as e:
        logger.error(f"Error getting visible employees: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve visible employees")

@app.get("/api/employees/stats")
async def get_employee_stats():
    """Get employee statistics"""
    try:
        stats = employee_service.get_employee_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting employee stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve employee stats")

@app.post("/api/employees", response_model=EmployeeActionResponse)
async def add_employee(employee: EmployeeRequest):
    """Add a new employee to the list"""
    try:
        if not employee.name or not employee.name.strip():
            raise HTTPException(status_code=400, detail="Employee name cannot be empty")
        
        employee_name = employee.name.strip()
        success = employee_service.add_employee(employee_name)
        
        employees_data = employee_service.get_employees_data()
        stats = employee_service.get_employee_stats()
        employees = [EmployeeData(**emp) for emp in employees_data]
        
        if success:
            logger.info(f"Added employee: {employee_name}")
            return EmployeeActionResponse(
                success=True,
                message=f"Employee '{employee_name}' added successfully",
                employees=employees,
                stats=stats
            )
        else:
            return EmployeeActionResponse(
                success=False,
                message=f"Employee '{employee_name}' already exists",
                employees=employees,
                stats=stats
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add employee")

@app.delete("/api/employees/{employee_name}", response_model=EmployeeActionResponse)
async def remove_employee(employee_name: str):
    """Remove an employee from the list"""
    try:
        if not employee_name or not employee_name.strip():
            raise HTTPException(status_code=400, detail="Employee name cannot be empty")
        
        # URL decode the name (in case of spaces)
        from urllib.parse import unquote
        employee_name = unquote(employee_name).strip()
        
        success = employee_service.remove_employee(employee_name)
        
        employees_data = employee_service.get_employees_data()
        stats = employee_service.get_employee_stats()
        employees = [EmployeeData(**emp) for emp in employees_data]
        
        if success:
            logger.info(f"Removed employee: {employee_name}")
            return EmployeeActionResponse(
                success=True,
                message=f"Employee '{employee_name}' removed successfully",
                employees=employees,
                stats=stats
            )
        else:
            return EmployeeActionResponse(
                success=False,
                message=f"Employee '{employee_name}' not found",
                employees=employees,
                stats=stats
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove employee")

@app.put("/api/employees/{employee_name}/hide", response_model=EmployeeActionResponse)
async def hide_employee(employee_name: str):
    """Hide an employee (for vacation/temporary absence)"""
    try:
        from urllib.parse import unquote
        employee_name = unquote(employee_name).strip()
        
        success = employee_service.hide_employee(employee_name)
        
        employees_data = employee_service.get_employees_data()
        stats = employee_service.get_employee_stats()
        employees = [EmployeeData(**emp) for emp in employees_data]
        
        if success:
            logger.info(f"Hidden employee: {employee_name}")
            return EmployeeActionResponse(
                success=True,
                message=f"Employee '{employee_name}' hidden successfully",
                employees=employees,
                stats=stats
            )
        else:
            return EmployeeActionResponse(
                success=False,
                message=f"Employee '{employee_name}' not found or already hidden",
                employees=employees,
                stats=stats
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error hiding employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to hide employee")

@app.put("/api/employees/{employee_name}/show", response_model=EmployeeActionResponse)
async def show_employee(employee_name: str):
    """Show a hidden employee (return from vacation/absence)"""
    try:
        from urllib.parse import unquote
        employee_name = unquote(employee_name).strip()
        
        success = employee_service.show_employee(employee_name)
        
        employees_data = employee_service.get_employees_data()
        stats = employee_service.get_employee_stats()
        employees = [EmployeeData(**emp) for emp in employees_data]
        
        if success:
            logger.info(f"Shown employee: {employee_name}")
            return EmployeeActionResponse(
                success=True,
                message=f"Employee '{employee_name}' shown successfully",
                employees=employees,
                stats=stats
            )
        else:
            return EmployeeActionResponse(
                success=False,
                message=f"Employee '{employee_name}' not found or not hidden",
                employees=employees,
                stats=stats
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to show employee")

@app.put("/api/employees/bulk-update", response_model=EmployeeActionResponse)
async def bulk_update_employees(employees_list: List[str]):
    """Bulk update employee list (replace entire list)"""
    try:
        if not employees_list:
            raise HTTPException(status_code=400, detail="Employee list cannot be empty")
        
        # Clean and validate employee names
        cleaned_employees = []
        for name in employees_list:
            if isinstance(name, str) and name.strip():
                cleaned_employees.append(name.strip())
        
        if not cleaned_employees:
            raise HTTPException(status_code=400, detail="No valid employee names provided")
        
        # Update employee list
        new_employees_data = employee_service.bulk_update_employees(cleaned_employees)
        
        stats = employee_service.get_employee_stats()
        employees = [EmployeeData(**emp) for emp in new_employees_data]
        
        logger.info(f"Updated employee list with {len(cleaned_employees)} employees")
        return EmployeeActionResponse(
            success=True,
            message=f"Employee list updated with {len(cleaned_employees)} employees",
            employees=employees,
            stats=stats
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating employee list: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update employee list")

# Dashboard Data Endpoints

@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """Get dashboard data"""
    try:
        # Load all call data using the data loader
        dashboard_data = await data_loader.load_dashboard_data()
        
        return {
            "status": "success",
            "data": dashboard_data,
            "last_update": datetime.now().isoformat(),
            "coaching_available": coaching_service is not None
        }
    except Exception as e:
        logger.error(f"Error loading dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard data")

@app.get("/api/dashboard/calls")
async def get_all_calls():
    """Get all processed calls"""
    try:
        calls = await data_loader.load_all_calls()
        return {
            "calls": calls,
            "total_calls": len(calls),
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error loading calls: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load calls")

# System Information Endpoints

@app.get("/api/system/status")
async def get_system_status():
    """Get comprehensive system status"""
    try:
        # Check service availability
        services_status = {
            "employee_service": "available",
            "data_loader": "available" if data_loader else "unavailable",
            "llm_analyzer": "available" if llm_analyzer.is_initialized else "unavailable",
            "coaching_service": "available" if coaching_service else "unavailable",
            "coaching_routes": "available" if COACHING_AVAILABLE else "unavailable"
        }
        
        # Get employee stats
        employee_stats = employee_service.get_employee_stats()
        
        # Get call statistics if data loader is available
        call_stats = {}
        try:
            if data_loader:
                calls = await data_loader.load_all_calls()
                call_stats = {
                    "total_calls": len(calls),
                    "recent_calls": len([c for c in calls if c.get('analysis_date', '') > (datetime.now().isoformat()[:10])]),
                    "processed_today": len([c for c in calls if c.get('analysis_date', '').startswith(datetime.now().isoformat()[:10])])
                }
        except Exception as e:
            call_stats = {"error": f"Failed to load call stats: {str(e)}"}
        
        return {
            "system_status": "healthy" if all(status == "available" for status in [services_status["employee_service"], services_status["data_loader"]]) else "partial",
            "services": services_status,
            "employee_stats": employee_stats,
            "call_stats": call_stats,
            "features": {
                "employee_management": True,
                "call_analysis": data_loader is not None,
                "coaching_library": coaching_service is not None and COACHING_AVAILABLE,
                "pdf_generation": coaching_service is not None and COACHING_AVAILABLE
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return {
            "system_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Run the enhanced API server"""
    print("\n🦷 Enhanced Dental Call Analysis API Server v3.0")
    print("="*60)
    print(f"🚀 Starting API server with Coaching Library...")
    print(f"📡 Employee management endpoints available")
    
    if COACHING_AVAILABLE:
        print(f"🎓 Coaching library endpoints available")
        print(f"📄 PDF generation for training materials")
    else:
        print(f"⚠️  Coaching library endpoints NOT available")
    
    print(f"📊 Dashboard data endpoints available")
    print(f"🌐 CORS enabled for React frontend")
    print(f"💼 Hide/Show feature for employee vacation management")
    
    # Log initial employee status
    stats = employee_service.get_employee_stats()
    visible_employees = employee_service.get_visible_employees()
    hidden_employees = employee_service.get_hidden_employees()
    
    print(f"👥 {stats['active_employees']} active employees:")
    print(f"   📋 Visible: {len(visible_employees)} ({', '.join(visible_employees)})")
    if hidden_employees:
        print(f"   🔒 Hidden: {len(hidden_employees)} ({', '.join(hidden_employees)})")
    
    print("="*60)
    print(f"📍 Available endpoints:")
    print(f"   🏠 Health check: http://localhost:8000/")
    print(f"   👥 Employees: http://localhost:8000/api/employees")
    print(f"   📊 Dashboard: http://localhost:8000/api/dashboard/data")
    if COACHING_AVAILABLE:
        print(f"   🎓 Coaching: http://localhost:8000/api/coaching/*")
        print(f"   🧪 Coaching Test: http://localhost:8000/api/coaching/test")
    else:
        print(f"   ❌ Coaching: Not Available")
    print(f"   📋 API docs: http://localhost:8000/docs")
    print("="*60)
    
    # Run the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()