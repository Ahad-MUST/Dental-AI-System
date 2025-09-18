"""
Enhanced API Server for Dental Call Analysis Dashboard
Includes employee management with hide/show functionality
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import List, Dict
import uvicorn

# Import settings and services
from config.settings import settings
from services.employee_list_service import EmployeeListService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Dental Call Analysis API",
    description="API for dental call analysis dashboard with enhanced employee management",
    version="2.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
employee_service = EmployeeListService()

# Pydantic models
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

# API Routes

@app.get("/")
async def root():
    """API health check"""
    stats = employee_service.get_employee_stats()
    return {
        "status": "running",
        "message": "Dental Call Analysis API v2.0",
        "timestamp": datetime.now().isoformat(),
        "features": ["employee_management", "hide_show_employees", "dashboard_data"],
        "employee_stats": stats
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
    """Get only visible employees (for LLM prompts)"""
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

@app.post("/api/employees/{employee_name}/hide", response_model=EmployeeActionResponse)
async def hide_employee(employee_name: str):
    """Hide an employee temporarily (e.g., vacation, sick leave)"""
    try:
        if not employee_name or not employee_name.strip():
            raise HTTPException(status_code=400, detail="Employee name cannot be empty")
        
        from urllib.parse import unquote
        employee_name = unquote(employee_name).strip()
        
        success = employee_service.hide_employee(employee_name)
        
        employees_data = employee_service.get_employees_data()
        stats = employee_service.get_employee_stats()
        employees = [EmployeeData(**emp) for emp in employees_data if emp.get("active", True)]
        
        if success:
            logger.info(f"Hidden employee: {employee_name}")
            return EmployeeActionResponse(
                success=True,
                message=f"Employee '{employee_name}' hidden successfully (temporarily excluded from LLM prompts)",
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

@app.post("/api/employees/{employee_name}/show", response_model=EmployeeActionResponse)
async def show_employee(employee_name: str):
    """Show a previously hidden employee"""
    try:
        if not employee_name or not employee_name.strip():
            raise HTTPException(status_code=400, detail="Employee name cannot be empty")
        
        from urllib.parse import unquote
        employee_name = unquote(employee_name).strip()
        
        success = employee_service.show_employee(employee_name)
        
        employees_data = employee_service.get_employees_data()
        stats = employee_service.get_employee_stats()
        employees = [EmployeeData(**emp) for emp in employees_data if emp.get("active", True)]
        
        if success:
            logger.info(f"Showed employee: {employee_name}")
            return EmployeeActionResponse(
                success=True,
                message=f"Employee '{employee_name}' is now visible (included in LLM prompts)",
                employees=employees,
                stats=stats
            )
        else:
            return EmployeeActionResponse(
                success=False,
                message=f"Employee '{employee_name}' not found or already visible",
                employees=employees,
                stats=stats
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error showing employee: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to show employee")

@app.put("/api/employees", response_model=EmployeeActionResponse)
async def update_employee_list(employee_names: List[str]):
    """Update the entire employee list (advanced operation)"""
    try:
        # Validate input
        if not isinstance(employee_names, list):
            raise HTTPException(status_code=400, detail="Employee list must be an array")
        
        # Clean and validate employee names
        cleaned_employees = []
        for emp in employee_names:
            if isinstance(emp, str) and emp.strip():
                cleaned_employees.append(emp.strip())
        
        if not cleaned_employees:
            raise HTTPException(status_code=400, detail="At least one valid employee name is required")
        
        # Convert to new format
        new_employees_data = []
        for emp_name in cleaned_employees:
            new_employees_data.append({
                "name": emp_name,
                "active": True,
                "hidden": False,
                "added_date": datetime.now().isoformat()
            })
        
        # Save the new list
        employee_service.save_employees_data(new_employees_data)
        
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

# Dashboard Data Endpoints (placeholder for existing functionality)

@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """Get dashboard data - placeholder endpoint"""
    # This would integrate with your existing data loading logic
    return {
        "calls": [],
        "analytics": {},
        "last_update": datetime.now().isoformat(),
        "message": "Dashboard data endpoint - integrate with existing data service"
    }

def main():
    """Run the enhanced API server"""
    print("\n🦷 Enhanced Dental Call Analysis API Server v2.0")
    print("="*60)
    print(f"🚀 Starting API server with hide/show employee functionality...")
    print(f"📡 Employee management endpoints available")
    print(f"🌐 CORS enabled for React frontend")
    print(f"👁️  Hide/Show feature for employee vacation management")
    
    # Log initial employee status
    stats = employee_service.get_employee_stats()
    visible_employees = employee_service.get_visible_employees()
    hidden_employees = employee_service.get_hidden_employees()
    
    print(f"👥 {stats['active_employees']} active employees:")
    print(f"   📋 Visible: {len(visible_employees)} ({', '.join(visible_employees)})")
    if hidden_employees:
        print(f"   🔍 Hidden: {len(hidden_employees)} ({', '.join(hidden_employees)})")
    
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