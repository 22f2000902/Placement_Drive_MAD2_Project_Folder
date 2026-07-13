const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: '',
            role: '',
            applicationId: null,
            application: {
                student: {},
                placement_drive: {},
                company: {},
                status: {}
            },
            successMessage: '',
            errorMessage: ''
        };
    },

    computed: {
        roleStudent() {
            return this.role === 'student';
        },

        roleCompany() {
            return this.role === 'company';
        },

        roleAdmin() {
            return this.role === 'admin';
        }
    },

    async mounted() {
        this.token = localStorage.getItem('access_token');
        this.role = localStorage.getItem('role');

        if (!this.token) {
            localStorage.clear();
            window.location.href = '/';
            return;
        }

        const root = document.getElementById('view-application-app');
        this.applicationId = root.dataset.applicationId;

        await this.loadApplication();
    },

    methods: {
        async loadApplication() {
            this.errorMessage = '';
            this.successMessage = '';

            try {
                const response = await fetch(
                    `/api/${this.role}/view_application/${this.applicationId}`,
                    {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${this.token}`,
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        }
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        data.message ||
                        'Failed to load application.'
                    );
                }
                this.application = data;
            }

            catch (error) {
                console.error(error);
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#view-application-app');