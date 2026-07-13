const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: '',
            studentId: null,
            student: {},
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

        const root = document.getElementById('student-profile-app');
        this.studentId = root.dataset.studentId;

        await this.loadStudentProfile();
    },

    methods: {
        async loadStudentProfile() {
            this.successMessage = '';
            this.errorMessage = '';

            try {
                const response = await fetch(
                    `/api/admin/student_profile/${this.studentId}`,
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
                    throw new Error(data.error || 'Failed to load profile.');
                }

                this.student = data;
                this.applications = data.applications || [];

            } catch (error) {
                console.error(error);
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#student-profile-app');