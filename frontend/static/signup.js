const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            role: '',
            name: '',
            email: '',
            password: '',
            confirm_password: '',
            phone_number: '',
            company_name: '',
            about_company: '',
            department: '',
            roll_number: '',
            errorMessage: ''
        };
    },

    computed: {
        roleAdmin() {
            return this.role === 'admin';
        },

        roleCompany() {
            return this.role === 'company';
        },

        roleStudent() {
            return this.role === 'student';
        }
    },

    mounted() {
        const pathSegments = window.location.pathname.split('/');
        this.role = pathSegments[pathSegments.length - 1];

        console.log("Detected role:", this.role);
    },

    methods: {
        async handleSignup() {
            this.errorMessage = '';

            // Prevent admin signup
            if (this.roleAdmin) {
                this.errorMessage = 'Admin registration is not allowed.';
                return;
            }

            // Password validation
            if (this.password !== this.confirm_password) {
                this.errorMessage = 'Passwords do not match.';
                return;
            }

            const signupData = {
                full_name: this.name,
                email: this.email,
                password: this.password,
                confirm_password: this.confirm_password,
                phone_number: this.phone_number
            };

            // Add role-specific fields
            if (this.roleCompany) {
                signupData.company_name = this.company_name;
                signupData.about_company = this.about_company;
            }

            if (this.roleStudent) {
                signupData.department = this.department;
                signupData.roll_number = this.roll_number;
            }

            try {
                const response = await fetch(`/api/auth/signup/${this.role}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(signupData)
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        data.message ||
                        'Signup failed.'
                    );
                }
                window.location.href = `/api/auth/login/${this.role}`;

            } catch (error) {
                console.error('Signup error:', error);
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#signup-app');