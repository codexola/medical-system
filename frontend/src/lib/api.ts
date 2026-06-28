import { clearAuthCookies, setAuthCookies } from './auth-cookies';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface AILog {
  id: string;
  provider: string;
  model: string;
  agent?: string;
  tokens?: number;
  latency_ms?: number;
  created_at?: string;
}

export interface FAQ {
  id: string;
  question: string;
  question_en?: string;
  answer: string;
  answer_en?: string;
  category: string;
}

export interface HospitalListItem {
  id: string;
  name: string;
  prefecture: string;
  city: string;
  departments: string[];
  emergency_available: boolean;
}

export interface HospitalRecommendation {
  id: string;
  name: string;
  address: string;
  distance_km?: number;
  phone?: string;
  departments?: string[];
  emergency_available?: boolean;
  rating?: number;
  reason?: string;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
      setAuthCookies(token, this.getRole());
    }
  }

  setRole(role: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('role', role);
      const token = localStorage.getItem('token');
      if (token) setAuthCookies(token, role);
    }
  }

  getRole(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('role');
    }
    return null;
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('role');
      clearAuthCookies();
    }
  }

  syncAuthCookies() {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    if (token) setAuthCookies(token, role);
  }

  isAuthenticated(): boolean {
    return Boolean(this.getToken());
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const isFormData = options.body instanceof FormData;
    const headers: Record<string, string> = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers as Record<string, string>),
    };
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (res.status === 401) {
      this.clearToken();
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        const next = encodeURIComponent(window.location.pathname);
        window.location.href = `/login?next=${next}`;
      }
      throw new Error('Session expired. Please log in again.');
    }
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(typeof error.detail === 'string' ? error.detail : 'Request failed');
    }
    return res.json();
  }

  // Auth
  login(email: string, password: string) {
    return this.request<{ access_token: string; user_id: string; role: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  register(formData: FormData) {
    return this.request<{ access_token: string; user_id: string; role: string }>('/auth/register', {
      method: 'POST',
      body: formData,
    });
  }

  uploadProfilePhoto(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request<{ id: string; url: string; checksum: string }>('/media/profile-photo', {
      method: 'POST',
      body: formData,
    });
  }

  adminLogin(email: string, password: string) {
    return this.request<{ access_token: string; user_id: string; role: string }>('/auth/admin/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  getProfile() {
    return this.request<{
      id: string;
      name: string;
      email: string;
      phone?: string;
      preferred_language: string;
      address?: string;
      job_function?: string;
      profile_photo_id?: string;
      profile_photo_url?: string;
    }>('/auth/me');
  }

  updateProfile(data: {
    name?: string;
    email?: string;
    phone?: string;
    address?: string;
    job_function?: string;
    preferred_language?: string;
    allergies?: string;
  }) {
    return this.request<{
      id: string;
      name: string;
      email: string;
      phone?: string;
      preferred_language: string;
      address?: string;
      job_function?: string;
      profile_photo_id?: string;
      profile_photo_url?: string;
    }>('/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Chat
  chat(message: string) {
    return this.request<{
      reply: string;
      user_id: string;
      hospitals?: Array<{
        id?: string;
        name: string;
        address: string;
        distance_km?: number;
        phone?: string;
        rating?: number;
        reason?: string;
        travel_time_minutes?: number;
        directions_url?: string;
        emergency_available?: boolean;
      }>;
      suggested_department?: string;
      cannot_diagnose?: boolean;
      show_hospital_finder?: boolean;
      show_pharmacy_finder?: boolean;
      plan?: string;
      features?: string[];
      specialists?: Array<{
        name?: string;
        rank?: string;
        specialty?: string;
        experience_years?: number;
        phone?: string;
        office_address?: string;
        hospital_name?: string;
        route_summary?: string;
        directions_url?: string;
      }>;
      pharmacies?: Array<{
        id?: string;
        name: string;
        address: string;
        distance_km?: number;
        phone?: string;
        rating?: number;
      }>;
    }>('/chat/', {
      method: 'POST',
      body: JSON.stringify({ message, channel: 'web' }),
    });
  }

  getChatHistory() {
    return this.request<Array<{ role: string; content: string; created_at: string }>>('/chat/history');
  }

  clearChatHistory() {
    return this.request<{ cleared: boolean; message: string }>('/chat/history', { method: 'DELETE' });
  }

  assessSymptoms(symptoms: string) {
    return this.request<{ urgency: string; summary: string; disclaimer: string }>('/chat/assess', {
      method: 'POST',
      body: JSON.stringify({ symptoms }),
    });
  }

  // Reservations
  getReservations(upcoming = false) {
    return this.request<Array<{ id: string; date: string; time: string; status: string; department?: string }>>(
      `/reservation/?upcoming=${upcoming}`
    );
  }

  createReservation(data: { doctor_id?: string; date: string; time: string; symptoms?: string }) {
    return this.request('/reservation/', { method: 'POST', body: JSON.stringify(data) });
  }

  // Hospitals
  searchHospitals(lat: number, lng: number, department?: string) {
    return this.request<HospitalRecommendation[]>('/hospital/search', {
      method: 'POST',
      body: JSON.stringify({ latitude: lat, longitude: lng, department }),
    });
  }

  filterHospitals(params: {
    symptoms: string;
    sort_by: 'nearest' | 'specialty' | 'rating';
    excellence_only?: boolean;
    department?: string;
  }) {
    return this.request<Array<{
      id?: string;
      name: string;
      address: string;
      distance_km?: number;
      phone?: string;
      departments?: string[];
      emergency_available?: boolean;
      rating?: number;
      reason?: string;
      directions_url?: string;
      travel_time_minutes?: number;
      route_summary?: string;
      routes?: Record<string, { duration_text?: string; maps_url?: string }>;
    }>>('/hospital/filter', {
      method: 'POST',
      body: JSON.stringify({ ...params, language: 'ja' }),
    });
  }

  recommendHospitals(symptoms: string, lat?: number, lng?: number) {
    return this.request<Array<{
      id?: string;
      name: string;
      address: string;
      distance_km?: number;
      phone?: string;
      departments?: string[];
      emergency_available?: boolean;
      rating?: number;
      reason?: string;
      directions_url?: string;
      travel_time_minutes?: number;
      route_summary?: string;
      routes?: Record<string, { duration_text?: string; distance_text?: string; maps_url?: string; summary?: string }>;
    }>>('/hospital/recommend', {
      method: 'POST',
      body: JSON.stringify({
        symptoms,
        ...(lat != null && lng != null ? { latitude: lat, longitude: lng } : {}),
      }),
    });
  }

  getHospitalDirections(hospitalName: string, hospitalAddress?: string) {
    const params = new URLSearchParams({ hospital_name: hospitalName });
    if (hospitalAddress) params.set('hospital_address', hospitalAddress);
    return this.request<{
      routes: Record<string, { duration_text?: string; distance_text?: string; maps_url?: string }>;
      fastest?: { duration_text?: string; maps_url?: string };
    }>(`/hospital/directions?${params}`);
  }

  listHospitals(prefecture?: string) {
    const params = prefecture ? `?prefecture=${prefecture}` : '';
    return this.request<HospitalListItem[]>(`/hospital/list${params}`);
  }

  // Subscription
  getSubscriptionStatus() {
    return this.request<{
      active: boolean;
      plan?: string;
      status?: string;
      subscription_id?: string;
      trial_end?: string;
      current_period_end?: string;
      cancelled_at?: string;
    }>('/subscription/status');
  }

  createCheckout(plan: 'standard' | 'premium') {
    return this.request<{ checkout_url: string }>(`/subscription/checkout?plan=${plan}`, { method: 'POST' });
  }

  cancelSubscription(atPeriodEnd = false) {
    return this.request('/subscription/cancel', {
      method: 'POST',
      body: JSON.stringify({ at_period_end: atPeriodEnd }),
    });
  }

  changeSubscriptionPlan(plan: string) {
    return this.request<{ checkout_url?: string; requires_payment?: boolean; plan?: string }>('/subscription/plan', {
      method: 'PATCH',
      body: JSON.stringify({ plan, admin_override: false }),
    });
  }

  // Admin
  getDashboardStats() {
    return this.request<{
      today_reservations: number;
      total_patients: number;
      active_subscriptions: number;
      ai_calls_today: number;
    }>('/admin/dashboard');
  }

  getTodayReservations() {
    return this.request<Array<{ id: string; time: string; patient_name?: string; status: string; department?: string }>>(
      '/admin/reservations/today'
    );
  }

  searchPatients(q: string) {
    return this.request<Array<{
      id: string;
      name?: string;
      email?: string;
      phone?: string;
      created_at?: string;
      subscription?: {
        id: string;
        plan: string;
        status: string;
        active: boolean;
        trial_end?: string;
        current_period_end?: string;
      };
    }>>(`/admin/patients?q=${encodeURIComponent(q)}`);
  }

  adminDeleteChatHistory(userId: string) {
    return this.request<{ deleted: boolean; deleted_messages: number; deleted_memories: number }>(
      `/admin/users/${userId}/chat-history`,
      { method: 'DELETE' }
    );
  }

  getAILogs() {
    return this.request<AILog[]>('/admin/ai-logs');
  }

  getAnalytics() {
    return this.request<{
      total_users: number;
      total_reservations: number;
      confirmed_reservations: number;
      total_ai_calls: number;
      total_tokens_used: number;
    }>('/admin/analytics');
  }

  getFAQs() {
    return this.request<FAQ[]>('/admin/faqs');
  }

  getAdminSubscriptions(params?: { status?: string; plan?: string; q?: string }) {
    const search = new URLSearchParams();
    if (params?.status) search.set('status', params.status);
    if (params?.plan) search.set('plan', params.plan);
    if (params?.q) search.set('q', params.q);
    const qs = search.toString();
    return this.request<Array<{
      id: string;
      user_id: string;
      patient_name?: string;
      patient_email?: string;
      plan: string;
      status: string;
      active: boolean;
      trial_end?: string;
      current_period_end?: string;
      cancelled_at?: string;
      stripe_subscription_id?: string;
    }>>(`/admin/subscriptions${qs ? `?${qs}` : ''}`);
  }

  adminCancelSubscription(subscriptionId: string, atPeriodEnd = false) {
    return this.request(`/admin/subscriptions/${subscriptionId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ at_period_end: atPeriodEnd }),
    });
  }

  adminUpdateSubscription(subscriptionId: string, plan: string) {
    return this.request(`/admin/subscriptions/${subscriptionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ plan, admin_override: true }),
    });
  }

  // Developer (project configuration — developer role only)
  getDeveloperDashboard() {
    return this.request<{
      stats: {
        total_users: number;
        total_staff: number;
        active_subscriptions: number;
        total_ai_calls: number;
        total_tokens_used: number;
      };
      recent_audit: Array<{ action: string; resource?: string; actor_email?: string; created_at?: string }>;
    }>('/developer/dashboard');
  }

  getDeveloperSettings() {
    return this.request<Array<{ key: string; value: Record<string, unknown>; category: string; description?: string }>>(
      '/developer/settings'
    );
  }

  updateDeveloperSetting(key: string, value: Record<string, unknown>) {
    return this.request(`/developer/settings/${encodeURIComponent(key)}`, {
      method: 'PUT',
      body: JSON.stringify({ value }),
    });
  }

  getDeveloperUsage() {
    return this.request<{
      ai_by_provider: Array<{ provider: string; calls: number; tokens: number }>;
      ai_by_model: Array<{ model: string; calls: number; tokens: number }>;
      users_by_role: Array<{ role: string; count: number }>;
      subscriptions_by_plan: Array<{ plan: string; count: number }>;
    }>('/developer/usage');
  }

  getDeveloperAuditLogs() {
    return this.request<Array<{
      id: string;
      actor_email?: string;
      actor_role: string;
      action: string;
      resource?: string;
      created_at?: string;
    }>>('/developer/audit-logs');
  }

  getDeveloperSystemInfo() {
    return this.request<Record<string, unknown>>('/developer/system');
  }

  getDeveloperStaff() {
    return this.request<Array<{
      id: string;
      email: string;
      name: string;
      role: string;
      is_active: boolean;
      last_login?: string;
    }>>('/developer/staff');
  }

  getDeveloperUsers(q: string) {
    return this.request<Array<{
      id: string;
      name?: string;
      email?: string;
      phone?: string;
      created_at?: string;
      message_count: number;
    }>>(`/developer/users?q=${encodeURIComponent(q)}`);
  }

  developerDeleteChatHistory(userId: string) {
    return this.request<{ deleted: boolean; deleted_messages: number; deleted_memories: number }>(
      `/developer/users/${userId}/chat-history`,
      { method: 'DELETE' }
    );
  }

  getStaffProfile() {
    return this.request<{ id: string; email: string; name: string; role: string }>('/auth/staff/me');
  }

  // RAG
  ragQuery(query: string, language = 'ja') {
    return this.request('/rag/query', {
      method: 'POST',
      body: JSON.stringify({ query, language }),
    });
  }
}

export const api = new ApiClient();
