//skipper/frontend/src/components/agents/AgentManagement.js

import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, RefreshCw, Play, Pause, 
    CheckCircle, AlertTriangle, X, LogIn, LogOut, 
    ChevronDown, ChevronUp, Search } from 'lucide-react';

function AgentManagement({ agents: initialAgents, serviceAccounts: initialAccounts }) {
  const [tabIndex, setTabIndex] = useState(0);
  const [agents, setAgents] = useState(initialAgents);
  const [serviceAccounts, setServiceAccounts] = useState(initialAccounts);
  const [loading, setLoading] = useState(true);
  const [error] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});
  const [agentToDelete, setAgentToDelete] = useState(null);
  const [agentFormData, setAgentFormData] = useState({
    name: '',
    machine_id: '',
    tags: [],
    status: 'offline'
  });
  
  // Service account dialog
  const [accountDialogOpen, setAccountDialogOpen] = useState(false);
  const [serviceAccountFormData, setServiceAccountFormData] = useState({
    username: '',
    display_name: '',
    description: '',
    password: '',
    account_type: 'robot'
  });
  
  // Auto-login dialog
  const [autoLoginDialogOpen, setAutoLoginDialogOpen] = useState(false);
  const [autoLoginData, setAutoLoginData] = useState({
    agent_id: '',
    service_account_id: '',
    session_type: 'windows'
  });

  useEffect(() => {
        // When initialAgents / initialAccounts change, load them
       setAgents(initialAgents);
        setServiceAccounts(initialAccounts);
        setLoading(false);
      }, [initialAgents, initialAccounts]);

  const handleTabChange = (newValue) => {
    setTabIndex(newValue);
  };

  const toggleRowExpand = (agentId) => {
    setExpandedRows(prev => ({
      ...prev,
      [agentId]: !prev[agentId]
    }));
  };

  const handleRefresh = () => {
    setLoading(true);
    // In a real app, this would refresh the data from the API
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  const handleOpenDialog = (agent = null) => {
    if (agent) {
      // Edit mode
      setSelectedAgent(agent);
      setAgentFormData({
        name: agent.name,
        machine_id: agent.machine_id,
        tags: agent.tags || [],
        status: agent.status
      });
    } else {
      // Create mode
      setSelectedAgent(null);
      setAgentFormData({
        name: '',
        machine_id: '',
        tags: [],
        status: 'offline'
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedAgent(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setAgentFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTagsChange = (e) => {
    setAgentFormData(prev => ({
      ...prev,
      tags: e.target.value.split(',').map(tag => tag.trim())
    }));
  };

  const handleSubmitAgent = () => {
    // In a real app, this would call the API to create/update an agent
    if (selectedAgent) {
      // Update existing agent
      setAgents(prevAgents => 
        prevAgents.map(agent => 
          agent.agent_id === selectedAgent.agent_id 
            ? { ...agent, ...agentFormData } 
            : agent
        )
      );
    } else {
      // Create new agent
      const newAgent = {
        agent_id: Date.now().toString(), // Mock ID generation
        ...agentFormData,
        ip_address: '',
        version: '1.0.0',
        last_heartbeat: null,
        capabilities: {},
        auto_login_enabled: false
      };
      setAgents(prev => [...prev, newAgent]);
    }
    
    handleCloseDialog();
  };

  const handleDeleteClick = (agent) => {
    setAgentToDelete(agent);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    // In a real app, this would call the API to delete the agent
    setAgents(prevAgents => 
      prevAgents.filter(agent => agent.agent_id !== agentToDelete.agent_id)
    );
    setDeleteDialogOpen(false);
  };

  // Service account handlers
  const handleOpenAccountDialog = () => {
    setServiceAccountFormData({
      username: '',
      display_name: '',
      description: '',
      password: '',
      account_type: 'robot'
    });
    setAccountDialogOpen(true);
  };

  const handleCloseAccountDialog = () => {
    setAccountDialogOpen(false);
  };

  const handleAccountInputChange = (e) => {
    const { name, value } = e.target;
    setServiceAccountFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmitAccount = () => {
    // In a real app, this would call the API to create a service account
    const newAccount = {
      account_id: Date.now().toString(), // Mock ID generation
      ...serviceAccountFormData,
      status: 'active',
      created_at: new Date().toISOString()
    };
    setServiceAccounts(prev => [...prev, newAccount]);
    handleCloseAccountDialog();
  };

  // Auto-login handlers
  const handleOpenAutoLoginDialog = (agent) => {
    setAutoLoginData({
      agent_id: agent.agent_id,
      service_account_id: '',
      session_type: 'windows'
    });
    setAutoLoginDialogOpen(true);
  };

  const handleCloseAutoLoginDialog = () => {
    setAutoLoginDialogOpen(false);
  };

  const handleAutoLoginChange = (e) => {
    const { name, value } = e.target;
    setAutoLoginData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmitAutoLogin = () => {
    // In a real app, this would call the API to enable auto-login
    setAgents(prevAgents => 
      prevAgents.map(agent => 
        agent.agent_id === autoLoginData.agent_id 
          ? { 
              ...agent, 
              auto_login_enabled: true,
              service_account: serviceAccounts.find(acc => acc.account_id === autoLoginData.service_account_id)
            } 
          : agent
      )
    );
    handleCloseAutoLoginDialog();
  };

  const handleDisableAutoLogin = (agent) => {
    // In a real app, this would call the API to disable auto-login
    setAgents(prevAgents => 
      prevAgents.map(a => 
        a.agent_id === agent.agent_id 
          ? { ...a, auto_login_enabled: false, service_account: null } 
          : a
      )
    );
  };

  // Filter agents based on search term
  const filteredAgents = agents.filter(agent => 
    agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.machine_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (agent.ip_address && agent.ip_address.includes(searchTerm))
  );

  // Filter service accounts based on search term
  const filteredAccounts = serviceAccounts.filter(account => 
    account.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    account.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (account.description && account.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Render agent status badge with appropriate color
  const renderAgentStatus = (status) => {
    let color, icon;
    
    switch (status) {
      case 'online':
        color = 'bg-green-100 text-green-800 border-green-300';
        icon = <CheckCircle size={14} className="text-green-500 mr-1" />;
        break;
      case 'offline':
        color = 'bg-red-100 text-red-800 border-red-300';
        icon = <X size={14} className="text-red-500 mr-1" />;
        break;
      case 'busy':
        color = 'bg-yellow-100 text-yellow-800 border-yellow-300';
        icon = <AlertTriangle size={14} className="text-yellow-500 mr-1" />;
        break;
      default:
        color = 'bg-gray-100 text-gray-800 border-gray-300';
        icon = null;
    }
    
    return (
      <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full border ${color}`}>
        {icon}
        {status}
      </span>
    );
  };

  return (
    <div className="w-full">
      {/* Tabs */}
      <div className="bg-white rounded-t-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => handleTabChange(0)}
              className={`py-4 px-6 ${
                tabIndex === 0
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Agents
            </button>
            <button
              onClick={() => handleTabChange(1)}
              className={`py-4 px-6 ${
                tabIndex === 1
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Service Accounts
            </button>
          </nav>
        </div>
      </div>

      {/* Agent Tab Content */}
      {tabIndex === 0 && (
        <div className="mt-6">
          <div className="flex justify-between mb-6">
            <h2 className="text-2xl font-semibold text-gray-800">Agent Management</h2>
            <div className="flex space-x-2">
              <button 
                onClick={handleRefresh}
                className="flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50"
              >
                <RefreshCw size={18} className="mr-2" />
                Refresh
              </button>
              <button 
                onClick={() => handleOpenDialog()}
                className="flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus size={18} className="mr-2" />
                Add Agent
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="mb-6 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={18} className="text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 block w-full rounded-md border border-gray-300 shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Loading, Error, and Empty States */}
          {loading ? (
            <div className="flex justify-center my-12">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4 mb-6">
              {error}
            </div>
          ) : filteredAgents.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <p className="text-gray-500">No agents found. Add a new agent to get started.</p>
            </div>
          ) : (
            /* Agents Table */
            <div className="bg-white shadow overflow-hidden border-b border-gray-200 rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="w-12 px-4 py-3"></th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Machine ID</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Version</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Heartbeat</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredAgents.map((agent) => (
                    <React.Fragment key={agent.agent_id}>
                      <tr className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <button
                            onClick={() => toggleRowExpand(agent.agent_id)}
                            className="text-gray-400 hover:text-gray-500"
                          >
                            {expandedRows[agent.agent_id] ? (
                              <ChevronUp size={18} />
                            ) : (
                              <ChevronDown size={18} />
                            )}
                          </button>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{agent.machine_id}</div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          {renderAgentStatus(agent.status)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{agent.ip_address || '-'}</div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{agent.version || '-'}</div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <div className="text-sm text-gray-500">
                            {agent.last_heartbeat 
                              ? new Date(agent.last_heartbeat).toLocaleString() 
                              : 'Never'
                            }
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleOpenDialog(agent)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                            title="Edit Agent"
                          >
                            <Edit size={18} />
                          </button>
                          {agent.status === 'online' ? (
                            <button
                              className="text-yellow-600 hover:text-yellow-900 mr-3"
                              title="Send Pause Command"
                            >
                              <Pause size={18} />
                            </button>
                          ) : (
                            <button
                              className="text-green-600 hover:text-green-900 mr-3"
                              title="Send Start Command"
                            >
                              <Play size={18} />
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteClick(agent)}
                            className="text-red-600 hover:text-red-900"
                            title="Delete Agent"
                          >
                            <Trash2 size={18} />
                          </button>
                        </td>
                      </tr>
                      {/* Expanded Row Content */}
                      {expandedRows[agent.agent_id] && (
                        <tr>
                          <td colSpan="8" className="px-4 py-4 bg-gray-50">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {/* Capabilities Card */}
                              <div className="bg-white p-4 rounded border border-gray-200">
                                <h3 className="text-lg font-medium text-gray-900 mb-2">Capabilities</h3>
                                {agent.capabilities && Object.keys(agent.capabilities).length > 0 ? (
                                  <ul className="divide-y divide-gray-200">
                                    {Object.entries(agent.capabilities).map(([key, value]) => (
                                      <li key={key} className="py-2">
                                        <div className="flex items-center">
                                          <span className="font-medium mr-2">{key}:</span>
                                          <span>{value}</span>
                                        </div>
                                      </li>
                                    ))}
                                  </ul>
                                ) : (
                                  <p className="text-gray-500">No capabilities reported</p>
                                )}
                              </div>
                              
                              {/* Auto-Login Card */}
                              <div className="bg-white p-4 rounded border border-gray-200">
                                <div className="flex justify-between items-center mb-4">
                                  <h3 className="text-lg font-medium text-gray-900">Auto-Login Configuration</h3>
                                  {agent.auto_login_enabled ? (
                                    <button 
                                      className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                                      onClick={() => handleDisableAutoLogin(agent)}
                                    >
                                      <LogOut size={16} className="mr-1" />
                                      Disable
                                    </button>
                                  ) : (
                                    <button 
                                      className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                                      onClick={() => handleOpenAutoLoginDialog(agent)}
                                    >
                                      <LogIn size={16} className="mr-1" />
                                      Enable
                                    </button>
                                  )}
                                </div>
                                
                                {agent.auto_login_enabled && agent.service_account ? (
                                  <div className="bg-blue-50 p-3 rounded-md">
                                    <p className="text-sm font-medium text-blue-800">Auto-login is enabled with:</p>
                                    <p className="mt-1 text-sm text-blue-700">
                                      <span className="font-medium">Account:</span> {agent.service_account.display_name} ({agent.service_account.username})
                                    </p>
                                    <p className="mt-1 text-sm text-blue-700">
                                      <span className="font-medium">Session Type:</span> {agent.session_type || 'windows'}
                                    </p>
                                  </div>
                                ) : (
                                  <p className="text-gray-500">Auto-login is not configured for this agent.</p>
                                )}
                                
                                {agent.tags && agent.tags.length > 0 && (
                                  <div className="mt-4">
                                    <h4 className="text-sm font-medium text-gray-900 mb-2">Tags</h4>
                                    <div className="flex flex-wrap gap-2">
                                      {agent.tags.map(tag => (
                                        <span 
                                          key={tag} 
                                          className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full border border-gray-300"
                                        >
                                          {tag}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Agent Form Dialog */}
          {dialogOpen && (
            <div className="fixed inset-0 z-10 overflow-y-auto">
              <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                  <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
                </div>
                
                {/* Modal content */}
                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                  <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      {selectedAgent ? 'Edit Agent' : 'Add Agent'}
                    </h3>
                    <div className="mt-2 space-y-4">
                      <div>
                        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                          Agent Name
                        </label>
                        <input
                          type="text"
                          name="name"
                          id="name"
                          value={agentFormData.name}
                          onChange={handleInputChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          required
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="machine_id" className="block text-sm font-medium text-gray-700">
                          Machine ID
                        </label>
                        <input
                          type="text"
                          name="machine_id"
                          id="machine_id"
                          value={agentFormData.machine_id}
                          onChange={handleInputChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          required
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="tags" className="block text-sm font-medium text-gray-700">
                          Tags (comma-separated)
                        </label>
                        <input
                          type="text"
                          name="tags"
                          id="tags"
                          value={agentFormData.tags.join(', ')}
                          onChange={handleTagsChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      
                      {selectedAgent && (
                        <div>
                          <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                            Status
                          </label>
                          <select
                            name="status"
                            id="status"
                            value={agentFormData.status}
                            onChange={handleInputChange}
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          >
                            <option value="online">Online</option>
                            <option value="offline">Offline</option>
                            <option value="busy">Busy</option>
                          </select>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button
                      type="button"
                      onClick={handleSubmitAgent}
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                    >
                      {selectedAgent ? 'Save Changes' : 'Create Agent'}
                    </button>
                    <button
                      type="button"
                      onClick={handleCloseDialog}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Delete Confirmation Dialog */}
          {deleteDialogOpen && (
            <div className="fixed inset-0 z-10 overflow-y-auto">
              <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                  <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
                </div>
                
                {/* Modal content */}
                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                  <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <div className="sm:flex sm:items-start">
                      <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                        <Trash2 size={24} className="text-red-600" />
                      </div>
                      <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">
                          Delete Agent
                        </h3>
                        <div className="mt-2">
                          <p className="text-sm text-gray-500">
                            Are you sure you want to delete the agent <strong>{agentToDelete?.name}</strong>? 
                            This action cannot be undone.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button
                      type="button"
                      onClick={handleConfirmDelete}
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
                    >
                      Delete
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteDialogOpen(false)}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {/* Auto Login Dialog */}
          {autoLoginDialogOpen && (
            <div className="fixed inset-0 z-10 overflow-y-auto">
              <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                  <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
                </div>
                
                {/* Modal content */}
                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                  <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Enable Auto-Login
                    </h3>
                    <div className="mt-2 space-y-4">
                      <div>
                        <label htmlFor="service_account_id" className="block text-sm font-medium text-gray-700">
                          Service Account
                        </label>
                        <select
                          name="service_account_id"
                          id="service_account_id"
                          value={autoLoginData.service_account_id}
                          onChange={handleAutoLoginChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          required
                        >
                          <option value="">Select a service account</option>
                          {serviceAccounts.map(account => (
                            <option key={account.account_id} value={account.account_id}>
                              {account.display_name} ({account.username})
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div>
                        <label htmlFor="session_type" className="block text-sm font-medium text-gray-700">
                          Session Type
                        </label>
                        <select
                          name="session_type"
                          id="session_type"
                          value={autoLoginData.session_type}
                          onChange={handleAutoLoginChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="windows">Windows</option>
                          <option value="web">Web</option>
                          <option value="custom">Custom</option>
                        </select>
                      </div>
                      
                      <div className="bg-yellow-50 p-4 rounded-md">
                        <div className="flex">
                          <div className="flex-shrink-0">
                            <AlertTriangle size={20} className="text-yellow-400" />
                          </div>
                          <div className="ml-3">
                            <h3 className="text-sm font-medium text-yellow-800">Important Note</h3>
                            <div className="mt-2 text-sm text-yellow-700">
                              <p>
                                Auto-login will allow the agent to run background processes with the
                                configured service account credentials. Make sure to follow proper
                                security protocols.
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button
                      type="button"
                      onClick={handleSubmitAutoLogin}
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                    >
                      Enable Auto-Login
                    </button>
                    <button
                      type="button"
                      onClick={handleCloseAutoLoginDialog}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Service Accounts Tab Content */}
      {tabIndex === 1 && (
        <div className="mt-6">
          <div className="flex justify-between mb-6">
            <h2 className="text-2xl font-semibold text-gray-800">Service Accounts</h2>
            <div className="flex space-x-2">
              <button 
                onClick={handleRefresh}
                className="flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50"
              >
                <RefreshCw size={18} className="mr-2" />
                Refresh
              </button>
              <button 
                onClick={handleOpenAccountDialog}
                className="flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus size={18} className="mr-2" />
                Add Account
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="mb-6 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={18} className="text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search service accounts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 block w-full rounded-md border border-gray-300 shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Loading, Error, and Empty States */}
          {loading ? (
            <div className="flex justify-center my-12">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4 mb-6">
              {error}
            </div>
          ) : filteredAccounts.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <p className="text-gray-500">No service accounts found. Add a new account to get started.</p>
            </div>
          ) : (
            /* Service Accounts Table */
            <div className="bg-white shadow overflow-hidden border-b border-gray-200 rounded-lg">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Display Name</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredAccounts.map((account) => (
                    <tr key={account.account_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{account.username}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{account.display_name}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{account.account_type}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-500 truncate max-w-xs">{account.description || '-'}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full border ${
                          account.status === 'active' 
                            ? 'bg-green-100 text-green-800 border-green-300' 
                            : 'bg-red-100 text-red-800 border-red-300'
                        }`}>
                          {account.status === 'active' ? 
                            <><CheckCircle size={14} className="text-green-500 mr-1" />{account.status}</> : 
                            <><X size={14} className="text-red-500 mr-1" />{account.status}</>
                          }
                        </span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          title="Edit Account"
                        >
                          <Edit size={18} />
                        </button>
                        <button
                          className="text-red-600 hover:text-red-900"
                          title="Delete Account"
                        >
                          <Trash2 size={18} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          
          {/* Create Service Account Dialog */}
          {accountDialogOpen && (
            <div className="fixed inset-0 z-10 overflow-y-auto">
              <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                  <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
                </div>
                
                {/* Modal content */}
                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                  <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Add Service Account
                    </h3>
                    <div className="mt-2 space-y-4">
                      <div>
                        <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                          Username
                        </label>
                        <input
                          type="text"
                          name="username"
                          id="username"
                          value={serviceAccountFormData.username}
                          onChange={handleAccountInputChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          required
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="display_name" className="block text-sm font-medium text-gray-700">
                          Display Name
                        </label>
                        <input
                          type="text"
                          name="display_name"
                          id="display_name"
                          value={serviceAccountFormData.display_name}
                          onChange={handleAccountInputChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          required
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                          Password
                        </label>
                        <input
                          type="password"
                          name="password"
                          id="password"
                          value={serviceAccountFormData.password}
                          onChange={handleAccountInputChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          required
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                          Description
                        </label>
                        <textarea
                          name="description"
                          id="description"
                          rows="3"
                          value={serviceAccountFormData.description}
                          onChange={handleAccountInputChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      
                      <div>
                        <label htmlFor="account_type" className="block text-sm font-medium text-gray-700">
                          Account Type
                        </label>
                        <select
                          name="account_type"
                          id="account_type"
                          value={serviceAccountFormData.account_type}
                          onChange={handleAccountInputChange}
                          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="robot">Robot</option>
                          <option value="service">Service</option>
                        </select>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button
                      type="button"
                      onClick={handleSubmitAccount}
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                    >
                      Create Account
                    </button>
                    <button
                      type="button"
                      onClick={handleCloseAccountDialog}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default AgentManagement;