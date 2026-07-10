const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: '',
            role: '',
            applicationId: null,
            application: {
                id: '',
                status: '',
                new_status: '',
                student: {
                    full_name: '',
                    department: '',
                    resume_path: ''
                }
            },
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

        const root = document.getElementById('change-student-application-status');
        this.applicationId = root.dataset.applicationId;

        await this.loadApplication();
    },

    methods: {
        async loadApplication() {
            this.successMessage = '';
            this.errorMessage = '';

            try {
                const response = await fetch(
                    `/api/${this.role}/get_student_application/${this.applicationId}`,
                    {
                        method: 'GET',
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

                this.application = {
                    ...data,
                    new_status: ''
                };

            } catch (error) {

                console.error(error);
                this.errorMessage = error.message;

            }

        },

        getAvailableStatuses(currentStatus) {

            switch (currentStatus.toLowerCase()) {
                case 'applied':
                    return ['shortlisted', 'rejected'];
                case 'shortlisted':
                    return ['interview', 'rejected'];
                case 'interview':
                    return ['selected', 'rejected'];
                case 'selected':
                case 'rejected':
                    return [];
                default:
                    return [];
            }
        },

        async changeStatus() {
            if (!this.application.new_status) {
                this.errorMessage = 'Please select a status.';
                return;
            }

            this.successMessage = '';
            this.errorMessage = '';

            try {
                const response = await fetch(
                    `/api/${this.role}/change_student_application_status/${this.applicationId}`,
                    {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${this.token}`,
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({
                            status: this.application.new_status
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        data.message ||
                        'Failed to update application status.'
                    );
                }

                this.application.status = this.application.new_status;
                this.application.new_status = '';

                this.successMessage = data.message;

            } catch (error) {

                console.error(error);
                this.errorMessage = error.message;

            }
        }
    }
}).mount('#change-student-application-status');