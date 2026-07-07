const { createApp } = Vue;

createApp({
    // Isolate Vue custom expression tokens from standard Jinja configurations
    delimiters: ['[[', ']]'],
    
    data() {
        return {
            token: null,
            // Core component context arrays mapped directly to HTML loop configurations
            requestedCompanies: [],
            activeCompanies: [],
            students: [],
            placements: []
        }
    },

    async mounted() {
        // Recover user payload authentication states 
        this.token = localStorage.getItem('access_token');
        const storedRole = localStorage.getItem('role');

        // Security fallback validation interceptor
        if (!this.token || storedRole !== 'admin') {
            localStorage.clear();
            window.location.href = '/api/auth/login/admin';
            return;
        }

        // Initialize asynchronous data retrieval sequence
        await this.loadDashboardData();
    },

    methods: {
        async loadDashboardData() {
            try {
                // Post mapping targets unified routing switchboard context
                const response = await fetch('/api/admin/dashboard', {
                    method: 'POST', 
                    headers: { 
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error(`Data acquisition channel broken: Status ${response.status}`);
                }

                const data = await response.json();

                // Hydrate Reactive View Objects 
                this.requestedCompanies = data.requested_companies || [];
                this.activeCompanies = data.active_companies || [];
                this.students = data.students || [];
                this.placements = data.placements || [];

            } catch (error) {
                console.error("Dashboard engine failed to parse dataset payload:", error.message);
            }
        },

        handleLogout() {
            localStorage.clear();
            window.location.href = '/api/index';
        }
    }
}).mount('#admin-dashboard-app');