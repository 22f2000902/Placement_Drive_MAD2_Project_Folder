const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: '',
            role: '',
            query: '',
            students: [],
            companies: [],
            drives: [],
            applications: [],
            successMessage: '',
            errorMessage: ''
        };
    },

    async mounted() {
        this.token = localStorage.getItem('access_token');
        this.role = localStorage.getItem('role');

        if (!this.token) {
            localStorage.clear();
            window.location.href = '/';
            return;
        }

        const params = new URLSearchParams(window.location.search);
        this.query = params.get("q") || "";

        if (this.query) {
            await this.search();
        }
    },

    methods: {
        async search() {

            this.successMessage = '';
            this.errorMessage = '';

            if (!this.query.trim()) {
                this.students = [];
                this.companies = [];
                this.drives = [];
                this.applications = [];
                return;
            }

            try {
                const response = await fetch(
                    '/api/auth/search',
                    {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${this.token}`,
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({
                            query: this.query
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        data.message ||
                        'Search failed.'
                    );
                }

                this.students = data.students || [];
                this.companies = data.companies || [];
                this.drives = data.drives || [];
                this.applications = data.applications || [];

            } catch (error) {
                console.error(error);
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#search-app');