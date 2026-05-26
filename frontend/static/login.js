const { createApp } = Vue;

createApp({
    // Keeps Jinja '{{ }}' separate from Vue '[[ ]]'
    delimiters: ['[[', ']]'],
    
    data() {
        return {
            role: 'student', // Default choice in the dropdown
            email: '',
            password: '',
            errorMessage: ''
        }
    },
    
    methods: {
        async handleLogin() {
            this.errorMessage = ''; // Clear previous errors

            // 1. Pack up the data from the form
            const credentials = {
                email: this.email,
                password: this.password
            };

            try {
                // 2. Call your Flask API endpoint dynamically using the role string
                const response = await fetch(`/login/${this.role}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(credentials)
                });

                const data = await response.json();

                // 3. If Flask responds with an error (like 401), catch it
                if (!response.ok) {
                    throw new Error(data.error || 'Invalid credentials');
                }

                // 4. SUCCESS: Save the JWT token into browser storage
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user_role', this.role);

                // 5. PAGE ROUTING: Connect and jump to the correct dashboard template
                if (this.role === 'admin') {
                    window.location.href = '/dashboard/admin';
                } else if (this.role === 'student') {
                    window.location.href = '/dashboard/student';
                } else if (this.role === 'company') {
                    window.location.href = '/dashboard/company';
                }

            } catch (error) {
                // Display the backend error on the screen automatically
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#login-app');