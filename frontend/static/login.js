const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    
    data() {
        return {
            role: '', 
            email: '',
            password: '',
            errorMessage: ''
        }
    },
    mounted() {
        // Automatically fetch the role path parameter out of the browser address bar
        const pathSegments = window.location.pathname.split('/');
        this.role = pathSegments[pathSegments.length - 1];
    },
    methods: {
        async handleLogin() {
            this.errorMessage = ''; 

            const credentials = {
                email: this.email,
                password: this.password
            };

            try {
                const response = await fetch(`/api/auth/login/${this.role}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json', 
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(credentials)
                });

                // 1. Check if the server encountered any HTTP validation failure FIRST
                if (!response.ok) {
                    let textError = 'Invalid credentials';
                    try {
                        // Attempt to extract structured JSON error string if it exists
                        const errorData = await response.json();
                        textError = errorData.error || errorData.message || textError;
                    } catch (e) {
                        // Fallback context if the server generated an HTML layout block
                        textError = `Server responded with status code ${response.status}`;
                    }
                    throw new Error(textError);
                }

                // 2. Safe to parse now that we know status code is 200 OK
                const data = await response.json();

                // 3. SUCCESS: Save the values required by your home page script 
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('role', this.role);
                localStorage.setItem('name', data.name || this.role.toUpperCase());

                // 4. ROUTING: Navigate smoothly to dashboards
                window.location.href = `/api/${this.role}/dashboard`;

            } catch (error) {
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#login-app');