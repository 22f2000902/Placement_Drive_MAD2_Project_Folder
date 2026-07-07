const app = Vue.createApp({

    delimiters: ['[[', ']]'],

    data() {

        const root = document.getElementById('change-student-application-status');

        return {

            application_id: root.dataset.applicationId,
            student_id: root.dataset.studentId,
            placement_drive_id: root.dataset.placementDriveId,

            current_status: root.dataset.currentStatus,
            company: root.dataset.company,
            job_title: root.dataset.jobTitle,

            student_name: '',
            roll_number: '',
            department: '',

            selectedStatus: '',

            availableStatuses: [
                'shortlisted',
                'interview complete',
                'offer',
                'rejected',
                'inactive',
                'placed'
            ],

            successMessage: '',
            errorMessage: ''
        };
    },

    mounted() {

        this.selectedStatus = this.current_status;

        console.log('Application ID:', this.application_id);
        console.log('Current Status:', this.current_status);

    },

    methods: {

        async changeStatus() {

            this.successMessage = '';
            this.errorMessage = '';

            try {

                const token = localStorage.getItem('access_token');
                const role = localStorage.getItem('role');

                if (!token) {
                    this.errorMessage = 'Please login again.';
                    return;
                }

                const response = await fetch(
                    `/api/${role}/student_application_status/${this.application_id}`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            status: this.selectedStatus
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to update status');
                }

                this.current_status = data.current_status;

                this.successMessage = data.message;

                setTimeout(() => {
                    this.successMessage = '';
                }, 5000);

            }
            catch (error) {

                console.error(error);

                this.errorMessage = error.message;

                setTimeout(() => {
                    this.errorMessage = '';
                }, 5000);
            }
        }
    }

});

app.mount('#change-student-application-status');