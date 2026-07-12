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
        },
        canApply() {
            if (!this.drive.drive_date || !this.drive.drive_end_date) {
                return false;
            }
        const today = new Date();
            today.setHours(0, 0, 0, 0);

            const startDate = new Date(this.drive.drive_date);
            startDate.setHours(0, 0, 0, 0);

            const endDate = new Date(this.drive.drive_end_date);
            endDate.setHours(0, 0, 0, 0);

            return today >= startDate && today <= endDate;
        },
        applicationMessage() {
            if (!this.drive.drive_date || !this.drive.drive_end_date) {
                return '';
            }

            const today = new Date();
            today.setHours(0, 0, 0, 0);

            const startDate = new Date(this.drive.drive_date);
            startDate.setHours(0, 0, 0, 0);

            const endDate = new Date(this.drive.drive_end_date);
            endDate.setHours(0, 0, 0, 0);

            if (today < startDate) {
                return 'Applications for this drive have not opened yet.';
            }

            if (today > endDate) {
                return 'Applications for this drive have closed.';
            }

            return '';
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