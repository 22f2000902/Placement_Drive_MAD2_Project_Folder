const {createApp} = Vue;

createApp({ 
    delimiters: ['[[', ']]'], // Isolate Vue custom expression tokens from standard Jinja configurations
    
    data() {
        return {
            token:null,
            companies: []
        }
    },

    async mounted() {
        this.token = localStorage.getItem('access_token');
        const storedRole = localStorage.getItem('role');

        if (!this.token || storedRole !== 'admin') {
            localStorage.clear();
            window.location.href ='/api/auth/login/admin';
            return;
        }

        await this.loadCompanyData();
    },

    methods: {
        async loadCompanyData() {
            try {
                const response = await fetch('/api/admin/companies', {
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
                this.companies = data.companies || [];
            } catch (error) {
                console.error("Company data engine failed to parse dataset payload:", error.message);
            }
        },

        handleCompanyAction(companyId, action) {
            // Placeholder for company action handling logic (e.g., approve/reject)
            console.log(`Action "${action}" triggered for company ID: ${companyId}`);
        }
    }
}).mount('#company-list-dashboard-app');