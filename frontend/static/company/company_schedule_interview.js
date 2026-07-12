const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: '',
            applicationId: null,
            application: {},
            interview_date: '',
            selectedSlot: '',
            successMessage: '',
            errorMessage: ''
        };
    },

    async mounted() {
        this.token = localStorage.getItem('access_token');
        const role = localStorage.getItem('role');

        if (!this.token || role !== 'company') {
            localStorage.clear();
            window.location.href = '/api/auth/login/company';
            return;
        }

        const root = document.getElementById('schedule-interview-app');
        this.applicationId = root.dataset.applicationId;

        await this.loadApplication();
    },

    methods: {
        async loadApplication() {
            this.errorMessage = '';
            try {
                const response = await fetch(
                    `/api/company/schedule_interview/${this.applicationId}`,
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
                        'Failed to load application.'
                    );
                }

                this.application = data.application;
            } catch (error) {
                console.error(error);
                this.errorMessage = error.message;
            }
        },

        async scheduleInterview() {
            if (!this.selectedSlot) {
                this.errorMessage = 'Please select an interview slot.';
                return;
            }

            if (!this.interview_date) {
                this.errorMessage = 'Please select an interview date.';
                return;
            }

            this.successMessage = '';
            this.errorMessage = '';

            try {

                const slotMap = {
                    "12:00-13:00": "12:00",
                    "13:00-14:00": "13:00",
                    "14:00-15:00": "14:00",
                    "15:00-16:00": "15:00",
                    "16:00-17:00": "16:00"
                };

                const response = await fetch(
                    `/api/company/create_interview/${this.applicationId}`,
                    {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${this.token}`,
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({
                            interview_date: this.interview_date,
                            interview_time: slotMap[this.selectedSlot]
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        'Failed to schedule interview.'
                    );
                }

                this.successMessage = data.message;

            } catch (error) {

                console.error(error);
                this.errorMessage = error.message;

            }
        }
    }
}).mount('#schedule-interview-app');