const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'], 

    data() {
        return {
            token: null,
            placements: [],
            role: null
        }
    }, 

    async mounted() {
        this.token = localStorage.getItem('access_token');
        this.role = localStorage.getItem('role');
        const storedRole = localStorage.getItem('role');

        if (!this.token || storedRole !== 'admin' && storedRole !== 'company') {
            localStorage.clear();
            window.location.href = '/api/auth/login/admin';
            return;
        }

        await this.loadPlacementData();
    },

    methods: {
        async loadPlacementData() {
            try {
                const response = await fetch(`/api/${this.role}/placement_drives`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error(`Data acquisition channel broken: Status ${response.status}`);
                }

                const data = await response.json();
                this.placements = data.placements || [];
            } catch (error) {
                console.error("Placement data engine failed to parse dataset payload:", error.message);
            }
        }
    }
}).mount('#placement-list-dashboard-app');