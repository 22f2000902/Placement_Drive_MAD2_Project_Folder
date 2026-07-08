const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: null,
            role: '',
            drive: {},
            successMessage: '',
            errorMessage: ''
        };
    },

    computed: {
        roleAdmin() {
            return this.role === 'admin';
        }, 

        roleCompany() {
            return this.role === 'company';
        }
    },

    mounted() {
        this.token = localStorage.getItem('access_token');
        this.role = localStorage.getItem('role');

        if (!this.token || !['admin', 'company'].includes(this.role)) {
            localStorage.clear();
            window.location.href = '/';
            return;
        }

        const root = document.getElementById('change-drive-status');
        this.drive = {
            id: root.dataset.driveId,
            company_name: root.dataset.companyName,
            job_title: root.dataset.jobTitle,
            job_description: root.dataset.jobDescription,
            drive_date: root.dataset.driveDate,
            drive_end_date: root.dataset.driveEndDate,
            key_skills: root.dataset.keySkills,
            salary_range: root.dataset.salaryRange,
            status: root.dataset.currentStatus,
            is_approved: root.dataset.isApproved === "True" || root.dataset.isApproved === "true"
        };
    },

    methods: {
        async changeStatus() {

        this.successMessage = '';
        this.errorMessage = '';

        let payload = {};

        if (this.role === "company") {
            const newStatus =
                this.drive.status === "active"
                    ? "inactive"
                    : "active";
            payload = {
                status: newStatus
            };

        } else {
            payload = {
                is_approved: !this.drive.is_approved
            };
        }

        try {
            const response = await fetch(
                `/api/${this.role}/change_placement_drive_status/${this.drive.id}`,
                {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${this.token}`,
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(payload)
                }
            );

            const data = await response.json();
            if (!response.ok) {
                throw new Error(
                    data.error ||
                    data.message ||
                    "Failed to update drive."
                );
            }

            if (this.role === "company") {
                this.drive.status = data.current_status;
            } else {
                this.drive.is_approved = data.is_approved;
            }

            this.successMessage = data.message;

            } catch (error) {
                console.error(error);
                this.errorMessage = error.message;

            }
        }
    }
}).mount('#change-drive-status');