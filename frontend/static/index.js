const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'], // Prevents conflict with Jinja {{ }} brackets
    data() {
        return {
            isLoggedIn: false,
            userName: '',
            userRole: ''
        }
    },
    mounted() {
        // Look inside the browser storage for the user session details
        const token = localStorage.getItem('access_token');
        const role = localStorage.getItem('role');
        const name = localStorage.getItem('name');

        if (token && role) {
            this.isLoggedIn = true;
            this.userRole = role; // 'student', 'company', or 'admin'
            this.userName = name || role.toUpperCase(); // The user's actual display name
        } else {
            this.isLoggedIn = false;
        }
    }
}).mount('#home-app');