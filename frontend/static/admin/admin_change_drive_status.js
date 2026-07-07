const { createApp } = Vue; 

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: null,
            placement: {},
            successMessage: '',
            errorMessage: ''
        };
    },

    mounted() {
        this.token = localStorage.getItem('access_token');
        const role = localStorage.getItem('role');

        if (!this.token || role !== 'admin') {
            localStorage.clear();
            window.location.href = '/api/auth/login/admin';
            return;
        }

        const root = document.getElementById('change-placement-status');
        this.placement = {
            id: root.dataset.placementId,
            company_name: root.dataset.companyName,
            job_title: root.dataset.jobTitle,
            drive_date: root.dataset.driveDate,
            drive_end_date: root.dataset.driveEndDate,
            department: root.dataset.department,
            status: root.dataset.placementStatus.toLowerCase() === 'true',
            is_approved: root.dataset.isApproved.toLowerCase() === 'true'
        };
    },

    methods: {
        async changeStatus() {
            this.successMessage = '';
            this.errorMessage = '';
            try {
                const newStatus = !this.placement.status;
                const response = await fetch(
                    `/api/admin/change_placement_status/${this.placement.id}`,
                    {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${this.token}`,
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({
                            status: newStatus
                        })
                    }
                );

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.message || 'Failed to change placement status');
                }

                this.placement.status = newStatus;
                this.successMessage = data.message || 'Placement status changed successfully';
            } catch (error) {
                this.errorMessage = error.message || 'An error occurred while changing placement status';
            }
        }
    }
}).mount('#change-placement-status');