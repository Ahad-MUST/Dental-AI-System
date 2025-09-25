import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Plus, 
  Trash2, 
  Eye, 
  EyeOff, 
  UserCheck,
  UserX,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

const EmployeeManagement = () => {
  const [employees, setEmployees] = useState([]);
  const [stats, setStats] = useState({});
  const [visibleEmployees, setVisibleEmployees] = useState([]);
  const [hiddenEmployees, setHiddenEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [newEmployeeName, setNewEmployeeName] = useState('');
  const [addingEmployee, setAddingEmployee] = useState(false);

  const API_BASE = 'http://localhost:8000/api';

  // Fetch employees data
  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/employees`);
      if (!response.ok) throw new Error('Failed to fetch employees');
      
      const data = await response.json();
      setEmployees(data.employees);
      setStats(data.stats);
      setVisibleEmployees(data.visible_employees);
      setHiddenEmployees(data.hidden_employees);
      setError('');
    } catch (err) {
      setError(`Error loading employees: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Add new employee
  const addEmployee = async () => {
    if (!newEmployeeName.trim()) {
      setError('Employee name cannot be empty');
      return;
    }

    try {
      setAddingEmployee(true);
      setError('');
      
      const response = await fetch(`${API_BASE}/employees`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newEmployeeName.trim() }),
      });

      const data = await response.json();
      
      if (data.success) {
        setSuccess(data.message);
        setNewEmployeeName('');
        setEmployees(data.employees);
        setStats(data.stats);
        await fetchEmployees();
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(`Error adding employee: ${err.message}`);
    } finally {
      setAddingEmployee(false);
    }
  };

  // Remove employee
  const removeEmployee = async (employeeName) => {
    if (!window.confirm(`Are you sure you want to remove ${employeeName}?`)) return;

    try {
      setError('');
      
      const response = await fetch(`${API_BASE}/employees/${encodeURIComponent(employeeName)}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      
      if (data.success) {
        setSuccess(data.message);
        setEmployees(data.employees);
        setStats(data.stats);
        await fetchEmployees();
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(`Error removing employee: ${err.message}`);
    }
  };

  // Hide employee - FIXED: Changed from POST to PUT
  const hideEmployee = async (employeeName) => {
    try {
      setError('');
      
      const response = await fetch(`${API_BASE}/employees/${encodeURIComponent(employeeName)}/hide`, {
        method: 'PUT', // FIXED: Changed from 'POST' to 'PUT'
      });

      const data = await response.json();
      
      if (data.success) {
        setSuccess(data.message);
        setEmployees(data.employees);
        setStats(data.stats);
        await fetchEmployees();
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(`Error hiding employee: ${err.message}`);
    }
  };

  // Show employee - FIXED: Changed from POST to PUT
  const showEmployee = async (employeeName) => {
    try {
      setError('');
      
      const response = await fetch(`${API_BASE}/employees/${encodeURIComponent(employeeName)}/show`, {
        method: 'PUT', // FIXED: Changed from 'POST' to 'PUT'
      });

      const data = await response.json();
      
      if (data.success) {
        setSuccess(data.message);
        setEmployees(data.employees);
        setStats(data.stats);
        await fetchEmployees();
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError(`Error showing employee: ${err.message}`);
    }
  };

  // Clear messages after 5 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // Load data on component mount
  useEffect(() => {
    fetchEmployees();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading employees...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
          <span className="text-red-800">{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center space-x-3">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
          <span className="text-green-800">{success}</span>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UserCheck className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Total</dt>
                <dd className="text-lg font-semibold text-gray-900">{stats.total_employees || 0}</dd>
              </dl>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Eye className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Visible</dt>
                <dd className="text-lg font-semibold text-gray-900">{stats.visible_employees || 0}</dd>
              </dl>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <EyeOff className="h-8 w-8 text-orange-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Hidden</dt>
                <dd className="text-lg font-semibold text-gray-900">{stats.hidden_employees || 0}</dd>
              </dl>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-8 w-8 text-gray-600" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">Active</dt>
                <dd className="text-lg font-semibold text-gray-900">{stats.active_employees || 0}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Add New Employee */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Add Employee</h3>
        <div className="flex space-x-3">
          <input
            type="text"
            value={newEmployeeName}
            onChange={(e) => setNewEmployeeName(e.target.value)}
            placeholder="Employee name"
            className="flex-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && addEmployee()}
          />
          <button
            onClick={addEmployee}
            disabled={addingEmployee || !newEmployeeName.trim()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {addingEmployee ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            ) : (
              <Plus className="h-4 w-4 mr-2" />
            )}
            {addingEmployee ? 'Adding...' : 'Add'}
          </button>
        </div>
      </div>

      {/* Employee Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Visible Employees */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <Eye className="h-5 w-5 text-green-600 mr-2" />
              Visible ({visibleEmployees.length})
            </h3>
          </div>
          <div className="p-6">
            {visibleEmployees.length === 0 ? (
              <p className="text-gray-500 italic">No visible employees</p>
            ) : (
              <div className="space-y-3">
                {employees
                  .filter(emp => !emp.hidden)
                  .map((employee) => (
                    <div key={employee.name} className="flex items-center justify-between py-2">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm font-medium text-gray-900">{employee.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => hideEmployee(employee.name)}
                          className="text-orange-600 hover:text-orange-800"
                          title="Hide employee"
                        >
                          <EyeOff className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => removeEmployee(employee.name)}
                          className="text-red-600 hover:text-red-800"
                          title="Remove employee"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>

        {/* Hidden Employees */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <EyeOff className="h-5 w-5 text-orange-600 mr-2" />
              Hidden ({hiddenEmployees.length})
            </h3>
          </div>
          <div className="p-6">
            {hiddenEmployees.length === 0 ? (
              <p className="text-gray-500 italic">No hidden employees</p>
            ) : (
              <div className="space-y-3">
                {employees
                  .filter(emp => emp.hidden)
                  .map((employee) => (
                    <div key={employee.name} className="flex items-center justify-between py-2">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                        <span className="text-sm font-medium text-gray-900">{employee.name}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => showEmployee(employee.name)}
                          className="text-green-600 hover:text-green-800"
                          title="Show employee"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => removeEmployee(employee.name)}
                          className="text-red-600 hover:text-red-800"
                          title="Remove employee"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmployeeManagement;