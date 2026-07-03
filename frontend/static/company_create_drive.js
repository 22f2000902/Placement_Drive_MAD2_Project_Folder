const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            job_title: '',
            job_description: '',
            drive_date: '',
            drive_end_date: '',
            salary_range: '',
            key_skills: '',
            successMessage: '',
            errorMessage: ''
        };
    },

    async mounted() {
        // Recover user payload authentication states 
        this.token = localStorage.getItem('access_token');
        const storedRole = localStorage.getItem('role');

        // Security fallback validation interceptor
        if (!this.token || storedRole !== 'company') {
            localStorage.clear();
            window.location.href = '/api/auth/login/company';
            return;
        }
    },

    methods: {
        async handleCreateDrive() {
            this.errorMessage = '';

            const driveData = {
                job_title: this.job_title,
                job_description: this.job_description,
                drive_date: this.drive_date,
                drive_end_date: this.drive_end_date,
                salary_range: this.salary_range,
                key_skills: this.key_skills
            }

            try {
                const response = await fetch(`/api/company/create_drive`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(driveData)
                });
                  
                const data = await response.json();

            } catch (error) {
                console.error('Error creating placement drive:', error);
                this.errorMessage = 'Failed to create placement drive.';
            }
        }
    }
}).mount('#company-create-drive-app')