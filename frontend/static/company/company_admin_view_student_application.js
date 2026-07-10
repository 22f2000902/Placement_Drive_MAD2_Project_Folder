const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: '',
            role: '',
            driveId: null,
            placementDrive: {},
            applications: [],
            successMessage: '',
            errorMessage: ''
        };
    },

    computed: {
        isStaff() {
            return this.role === 'admin' || this.role === 'company';
        }
    },

    async mounted() {
        this.token = localStorage.getItem('access_token');
        this.role = localStorage.getItem('role');

        if (!this.token || !['admin', 'company'].includes(this.role)) {
            localStorage.clear();
            window.location.href = '/';
            return;
        }

        const root = document.getElementById('student-application-view-drive-app');
        this.driveId = root.dataset.driveId;

        await this.loadApplications();

    },

    methods: {
        async loadApplications() {
            this.successMessage = '';
            this.errorMessage = '';

            try {
                const response = await fetch(
                    `/api/${this.role}/view_student_applications/${this.driveId}`,
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
                        'Failed to load student applications.'
                    );
                }

                this.placementDrive = data.placement_drive || {};
                this.applications = data.applications || [];
            } catch (error) {
                console.error(error);
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#student-application-view-drive-app');