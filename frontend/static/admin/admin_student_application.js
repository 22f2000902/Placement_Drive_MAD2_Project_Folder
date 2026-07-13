const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: '',
            studentId: null,
            applications: [],
            successMessage: '',
            errorMessage: ''
        };
    },

    async mounted() {
        this.token = localStorage.getItem('access_token');
        const role = localStorage.getItem('role');

        if (!this.token || role !== 'admin') {
            localStorage.clear();
            window.location.href = '/';
            return;
        }

        const root = document.getElementById('student-applications-app');
        this.studentId = root.dataset.studentId;

        await this.loadApplications();
    },

    methods: {
        async loadApplications() {
            this.successMessage = '';
            this.errorMessage = '';

            try {
                const response = await fetch(
                    `/api/admin/student_applications/${this.studentId}`,
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
                this.applications = data.applications || [];

            } catch (error) {
                console.error(error);
                this.errorMessage = error.message;

            }
        }
    }
}).mount('#student-applications-app');