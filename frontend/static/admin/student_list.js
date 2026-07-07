const {createApp} = Vue;

createApp({
    delimiters: ['[[', ']]'], // Isolate Vue custom expression tokens from standard Jinja configurations

    data() {
        return {
            token: null, 
            students: []
        }
    }, 

    async mounted() {
        this.token = localStorage.getItem('access_token');
        const storedRole = localStorage.getItem('role');

        if (!this.token || storedRole !== 'admin') {
            localStorage.clear();
            window.location.href ='/api/auth/login/admin';
            return;
        }

        await this.loadStudentData();
    }, 

    methods: {
        async loadStudentData() {
            try {
                const response = await fetch('/api/admin/students', {
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
                this.students = data.students || [];
            } catch (error) {
                console.error("Student data engine failed to parse dataset payload:", error.message);
            }
        },

        handleStudentAction(studentId, action) {
            console.log(`Action "${action}" triggered for student ID: ${studentId}`);
        }
}
}).mount('#student-list-dashboard-app');