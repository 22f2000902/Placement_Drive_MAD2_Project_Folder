const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            token: null, 
            activePlacements: [],
            inactivePlacements: [],
            studentApplications: [],
            company: []
        }
    }, 

    async mounted() {
        this.token = localStorage.getItem('access_token');
        if (!this.token) {
            localStorage.clear();
            window.location.href = '/api/auth/login/company';
            return;
        }
        this.loadCompanyDashboardData();
    }, 

    methods: {
        async loadCompanyDashboardData() {
            try {
                const response = await fetch(`/api/company/dashboard`, {
                    method: 'POST', 
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });

                const data = await response.json();
                this.activePlacements = data.active_placements || [];
                this.inactivePlacements = data.inactive_placements || [];
                this.studentApplications = data.student_applications || [];
                this.company = data.company || {};
            } catch (error) {
                console.error('Error loading company dashboard data:', error);
            }
        }, 

        handleLogout() {
            localStorage.clear();
            window.location.href = '/api/auth/login/company';
        }
    }
}).mount('#company-dashboard-app');