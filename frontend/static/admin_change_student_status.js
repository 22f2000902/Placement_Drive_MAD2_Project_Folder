const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: null, 
            studentId: null,
            student: {},
            selectedStatus: null,
            successMessage: null,
            errorMessage: null

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

        const root = document.getElementById('change-student-status');

        this.student = {
            id: root.dataset.studentId,
            full_name: root.dataset.studentName,
            is_active: root.dataset.studentStatus === 'active'
        };
    }, 

    methods: {
        async changeStatus() {
            let newStatus = 'active';

            if (this.student.is_active) {
                newStatus = 'inactive';
            }

            try {
                const response = await fetch(`/api/admin/change_student_status/${this.student.id}`, {
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
                this.successMessage = data.message || "Student status updated successfully.";
            } catch (error) {
                console.error("Error during status change operation:", error.message);
                this.errorMessage = error.message || "An unexpected error occurred while changing the student status.";
            }
        }
    }
}).mount('#change-student-status');