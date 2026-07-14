const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: null, 
            companyId: null,
            company: {},
            selectedStatus: null,
            successMessage: null,
            errorMessage: null,
            number_of_placement_drives: null

        }
    },

    async mounted() {
        this.token = localStorage.getItem('access_token');
        const storedRole = localStorage.getItem('role');

        if (!this.token || storedRole !== 'admin') {
            localStorage.clear();
            window.location.href = '/api/auth/login/admin';
            return;
        }

        const root = document.getElementById('change-company-status');

        this.number_of_placement_drives = root.dataset.numberOfPlacementDrives || 0;
        this.company = {
            id: root.dataset.companyId,
            company_name: root.dataset.companyName,
            status: root.dataset.companyStatus,
            full_name: root.dataset.fullName,
            about_company: root.dataset.aboutCompany
        };
    }, 

    methods: {
        async changeStatus() {
            let newStatus = 'active';

            if (this.company.status === 'active') {
                newStatus = 'inactive';
            }

            try {
                const response = await fetch(`/api/admin/change_company_status/${this.company.id}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ status: newStatus })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || `Status update failed: ${response.status}`);
                }

                const data = await response.json();
                this.successMessage = data.message || "Company status updated successfully.";
            } catch (error) {
                console.error("Error during status change operation:", error.message);
                this.errorMessage = error.message || "An unexpected error occurred while changing the company status.";
            }
        }
    }
}).mount('#change-company-status');