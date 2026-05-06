import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const fetchDashboard = () => api.get('/work-items/dashboard')
export const fetchWorkItem = (id) => api.get(`/work-items/${id}`)
export const fetchSignals = (id) => api.get(`/work-items/${id}/signals`)
export const updateStatus = (id, status) => api.patch(`/work-items/${id}/status`, { status })
export const submitRCA = (id, data) => api.post(`/work-items/${id}/rca`, data)
export const fetchHealth = () => axios.get('/health')

export default api
