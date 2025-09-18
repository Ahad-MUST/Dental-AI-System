"""
Enhanced Employee List Management Service
Manages employees with hide/show functionality for temporary exclusions (vacations, etc.)
"""
import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

class EmployeeListService:
    """Enhanced service to manage dental office employees with hide/show functionality"""
    
    def __init__(self):
        self.employees_file = settings.OUTPUT_DIR / "employees.json"
        self.default_employees = [
            {"name": "Aminah Jafri", "active": True, "hidden": False},
            {"name": "Jovana Vanegas", "active": True, "hidden": False}, 
            {"name": "Melina Rodriguez", "active": True, "hidden": False},
            {"name": "Whitney Minor", "active": True, "hidden": False},
            {"name": "Yuseli Saldana", "active": True, "hidden": False}
        ]
        self.ensure_employees_file_exists()
    
    def ensure_employees_file_exists(self):
        """Create employees file with default list if it doesn't exist"""
        if not self.employees_file.exists():
            self.save_employees_data(self.default_employees)
            logger.info(f"Created employees file with {len(self.default_employees)} default employees")
        else:
            # Migrate old format if needed
            self._migrate_old_format_if_needed()
    
    def _migrate_old_format_if_needed(self):
        """Migrate from old simple list format to new object format"""
        try:
            with open(self.employees_file, 'r') as f:
                data = json.load(f)
            
            # Check if it's old format (simple list)
            if 'employees' in data and isinstance(data['employees'], list):
                if data['employees'] and isinstance(data['employees'][0], str):
                    # Old format - convert to new format
                    new_employees = []
                    for emp_name in data['employees']:
                        new_employees.append({
                            "name": emp_name,
                            "active": True,
                            "hidden": False
                        })
                    self.save_employees_data(new_employees)
                    logger.info(f"Migrated {len(new_employees)} employees to new format with hide/show support")
        except Exception as e:
            logger.error(f"Error migrating employee format: {str(e)}")
    
    def get_employees_data(self) -> List[Dict]:
        """Get complete employees data with all fields"""
        try:
            if self.employees_file.exists():
                with open(self.employees_file, 'r') as f:
                    data = json.load(f)
                    return data.get('employees', self.default_employees)
            else:
                return self.default_employees
        except Exception as e:
            logger.error(f"Error loading employees: {str(e)}")
            return self.default_employees
    
    def get_employees(self) -> List[str]:
        """Get current list of employee names (all employees since we permanently delete inactive ones)"""
        employees_data = self.get_employees_data()
        return [emp["name"] for emp in employees_data]
    
    def get_visible_employees(self) -> List[str]:
        """Get list of employees that are not hidden (for LLM prompts)"""
        employees_data = self.get_employees_data()
        return [emp["name"] for emp in employees_data if not emp.get("hidden", False)]
    
    def get_hidden_employees(self) -> List[str]:
        """Get list of employees that are currently hidden"""
        employees_data = self.get_employees_data()
        return [emp["name"] for emp in employees_data if emp.get("hidden", False)]
    
    def save_employees_data(self, employees_data: List[Dict]):
        """Save complete employees data to file"""
        try:
            data = {
                'employees': employees_data,
                'count': len(employees_data),
                'visible_count': len([emp for emp in employees_data if emp.get("active", True) and not emp.get("hidden", False)]),
                'hidden_count': len([emp for emp in employees_data if emp.get("active", True) and emp.get("hidden", False)]),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.employees_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(employees_data)} employees to file")
        except Exception as e:
            logger.error(f"Error saving employees: {str(e)}")
    
    def add_employee(self, employee_name: str) -> bool:
        """Add a new employee to the list"""
        try:
            employees_data = self.get_employees_data()
            
            # Check if employee already exists (including inactive ones since we now permanently delete)
            existing_names = [emp["name"] for emp in employees_data]
            if employee_name in existing_names:
                logger.warning(f"Employee already exists: {employee_name}")
                return False
            
            # Add new employee
            new_employee = {
                "name": employee_name,
                "active": True,
                "hidden": False,
                "added_date": datetime.now().isoformat()
            }
            employees_data.append(new_employee)
            self.save_employees_data(employees_data)
            logger.info(f"Added employee: {employee_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding employee: {str(e)}")
            return False
    
    def remove_employee(self, employee_name: str) -> bool:
        """Permanently remove an employee from the list (delete from JSON)"""
        try:
            employees_data = self.get_employees_data()
            
            # Find and remove the employee completely
            original_count = len(employees_data)
            employees_data = [emp for emp in employees_data if emp["name"] != employee_name]
            
            if len(employees_data) < original_count:
                self.save_employees_data(employees_data)
                logger.info(f"Permanently removed employee: {employee_name}")
                return True
            else:
                logger.warning(f"Employee not found: {employee_name}")
                return False
        except Exception as e:
            logger.error(f"Error removing employee: {str(e)}")
            return False
    
    def hide_employee(self, employee_name: str) -> bool:
        """Hide an employee temporarily (e.g., vacation, sick leave)"""
        try:
            employees_data = self.get_employees_data()
            
            for emp in employees_data:
                if emp["name"] == employee_name:
                    emp["hidden"] = True
                    emp["hidden_date"] = datetime.now().isoformat()
                    self.save_employees_data(employees_data)
                    logger.info(f"Hidden employee: {employee_name}")
                    return True
            
            logger.warning(f"Employee not found: {employee_name}")
            return False
        except Exception as e:
            logger.error(f"Error hiding employee: {str(e)}")
            return False
    
    def show_employee(self, employee_name: str) -> bool:
        """Show a previously hidden employee"""
        try:
            employees_data = self.get_employees_data()
            
            for emp in employees_data:
                if emp["name"] == employee_name:
                    emp["hidden"] = False
                    if "hidden_date" in emp:
                        del emp["hidden_date"]
                    emp["shown_date"] = datetime.now().isoformat()
                    self.save_employees_data(employees_data)
                    logger.info(f"Showed employee: {employee_name}")
                    return True
            
            logger.warning(f"Employee not found: {employee_name}")
            return False
        except Exception as e:
            logger.error(f"Error showing employee: {str(e)}")
            return False
    
    def get_employees_formatted_for_prompt(self) -> str:
        """Get visible employees list formatted for LLM prompt (excludes hidden employees)"""
        visible_employees = self.get_visible_employees()
        if not visible_employees:
            return "No visible employees configured"
        
        return "\n".join([f"- {employee}" for employee in visible_employees])
    
    def get_employee_stats(self) -> Dict:
        """Get statistics about employees"""
        employees_data = self.get_employees_data()
        # Since we now permanently delete, all employees in the file are active
        visible_employees = [emp for emp in employees_data if not emp.get("hidden", False)]
        hidden_employees = [emp for emp in employees_data if emp.get("hidden", False)]
        
        return {
            "total_employees": len(employees_data),
            "active_employees": len(employees_data),  # All are active since we delete inactive ones
            "visible_employees": len(visible_employees),
            "hidden_employees": len(hidden_employees),
            "inactive_employees": 0  # Always 0 since we permanently delete
        }