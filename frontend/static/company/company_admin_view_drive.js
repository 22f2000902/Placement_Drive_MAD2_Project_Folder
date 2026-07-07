const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    
    data() {
        return {
            token: '',
            role: '',
            driveId: null,
            drive: {},
            applications: [],
            successMessage: '',
            errorMessage: ''
        };
    },

    computed: {
        isStaff() {
            return this.role === 'admin' || this.role === 'company';
        },
        isStudent() {
            return this.role === 'student';
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

        const root = document.getElementById('company-view-drive-app');
        this.driveId = root.dataset.driveId;
        await this.loadDrive();
    },

    methods: {
        async loadDrive() {
            this.errorMessage = '';
            try {
                const response = await fetch(
                    `/api/${this.role}/view_drive/${this.driveId}`,
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
                    throw new Error(data.error || 'Failed to load placement drive.');
                }
                this.drive = data;
                this.applications = data.applications || [];
            }
            catch (error) {
                console.error(error);
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#company-view-drive-app');