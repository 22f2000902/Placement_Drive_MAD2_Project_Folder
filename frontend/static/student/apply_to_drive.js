const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: '',
            drive: {},
            successMessage: '',
            errorMessage: ''
        };
    },

    mounted() {
        this.token = localStorage.getItem('access_token');
        const storedRole = localStorage.getItem('role');

        if (!this.token || storedRole !== 'student') {
            localStorage.clear();
            window.location.href = '/api/auth/login/student';
            return;
        }

        const root = document.getElementById('apply_to_drive_app');

        this.drive = {
            id: root.dataset.driveId,
            company_name: root.dataset.companyName,
            about_company: root.dataset.aboutCompany,
            job_title: root.dataset.jobTitle,
            job_description: root.dataset.jobDescription,
            key_skills: root.dataset.keySkills,
            salary_range: root.dataset.salaryRange,
            drive_date: root.dataset.driveDate,
            drive_end_date: root.dataset.driveEndDate
        };

    },

    methods: {
        async applyToDrive() {
            this.successMessage = '';
            this.errorMessage = '';

            try {
                const response = await fetch(
                    `/api/student/apply_to_drive/${this.drive.id}`,
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
                        'Failed to submit application.'
                    );
                }
                
                this.successMessage = data.message;
                setTimeout(() => {
                    window.location.href = '/api/student/dashboard';
                }, 1500);
            }
            catch (error) {
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#apply_to_drive_app');