const { createApp } = Vue;

createApp({

    delimiters: ['[[', ']]'],
    
    data() {
        return {
            token: null,
            student: {},
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

        const root = document.getElementById('change-student-status');
        this.student = {
            id: root.dataset.studentId,
            full_name: root.dataset.studentName,
            roll_number: root.dataset.rollNumber,
            department: root.dataset.department,
            is_active: root.dataset.studentStatus.toLowerCase() === 'true'
        };
    },

    methods: {
        async changeStatus() {
            this.successMessage = '';
            this.errorMessage = '';
            try {
                const newStatus = !this.student.is_active;
                const response = await fetch(
                    `/api/admin/change_student_status/${this.student.id}`,
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
                    throw new Error(
                        data.error ||
                        data.message ||
                        'Failed to update student status.'
                    );
                }
                this.student.is_active = data.current_status;
                this.successMessage = data.message;
            }

            catch (error) {
                console.error(error);
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#change-student-status');