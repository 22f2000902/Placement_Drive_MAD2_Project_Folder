const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: null,
            companyId: null,
            placementDrives: []
            };
        },

    async mounted() {
        this.token = localStorage.getItem('access_token');
        const storedRole = localStorage.getItem('role');

        if (!this.token || storedRole !== 'admin') {
            localStorage.clear();
            window.location.href = '/api/auth/login/admin';
            return;
        }

        const root = document.getElementById('admin_view_company_drive_app');
        this.companyId = root.dataset.companyId;
        await this.loadPlacementDrives();
    },

    methods: {
        async loadPlacementDrives() {
            try {
                const response = await fetch(
                    `/api/admin/view_company_drives/${this.companyId}`,
                    {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${this.token}`,
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        }}
                );

                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to load placement drives.');
                }

                this.placementDrives = data.placement_drives || [];
            }
            catch (error) {
                console.error(error);
            }
        }
    }
}).mount('#admin_view_company_drive_app');