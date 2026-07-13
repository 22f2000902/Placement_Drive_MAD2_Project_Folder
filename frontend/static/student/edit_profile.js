const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],

    data() {
        return {
            token: '',
            role: '',
            userId: null,
            profile: {},
            resume: null,
            successMessage: '',
            errorMessage: ''
        };
    },

    async mounted() {
        this.token = localStorage.getItem('access_token');
        this.role = localStorage.getItem('role');

        if (!this.token || !['student', 'company'].includes(this.role)) {
            localStorage.clear();
            window.location.href = '/';
            return;
        }

        const root = document.getElementById('edit-profile-app');
        this.userId = root.dataset.userId;

        await this.loadProfile();
    },

    methods: {
        async loadProfile() {
            this.successMessage = '';
            this.errorMessage = '';

            try {
                const response = await fetch(`/api/${this.role}/edit_profile/${this.userId}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    }
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to load profile.');
                }

                this.profile = data;

            } catch (error) {
                console.error(error);
                this.errorMessage = error.message;
            }
        },

        handleResumeUpload(event) {
            this.resume = event.target.files[0];
        },

        async handleEditProfile() {
            this.successMessage = '';
            this.errorMessage = '';

            try {
                const formData = new FormData();

                formData.append('full_name', this.profile.full_name);
                formData.append('email', this.profile.email);
                formData.append('phone_number', this.profile.phone_number);

                if (this.role === 'student') {
                    formData.append('cgpa', this.profile.cgpa);

                    if (this.resume) {
                        formData.append('resume', this.resume);
                    }
                }

                if (this.role === 'company') {
                    formData.append('about_company', this.profile.about_company);
                }

                const response = await fetch(`/api/${this.role}/edit_profile/${this.userId}`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    },
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to update profile.');
                }

                this.successMessage = data.message;

                await this.loadProfile();

            } catch (error) {
                console.error(error);
                this.errorMessage = error.message;
            }
        }
    }
}).mount('#edit-profile-app');