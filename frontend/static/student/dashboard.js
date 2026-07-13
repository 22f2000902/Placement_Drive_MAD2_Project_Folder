const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            token: null, 
            ongoing_drives: [],
            upcoming_drives: [],
            applications: [],
            interviews: [],
            user_id: null
        }
    }, 

    async mounted() {
        this.token = localStorage.getItem('access_token');
        const storedRole = localStorage.getItem('role');
        if (!this.token || storedRole !== 'student') {
            localStorage.clear();
            window.location.href = '/api/auth/login/student';
            return;
        }
        this.loadStudentDashboardData();
    }, 

    methods: {
        async loadStudentDashboardData() {
            try {
                const response = await fetch(`/api/student/dashboard`, {
                    method: 'POST', 
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });

                const data = await response.json();
                
                this.ongoing_drives = data.ongoing_drives || [];
                this.upcoming_drives = data.upcoming_drives || [];
                this.applications = data.applications || [];
                this.interviews = data.interviews || [];
                this.user_id = data.user_id || null;
            } catch (error) {
                console.error('Error loading student dashboard data:', error);
            }
        }, 

        handleLogout() {
            localStorage.clear();
            window.location.href = '/api/auth/login/student';
        }
    }
}).mount('#student-dashboard-app');