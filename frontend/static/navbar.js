const app = Vue.createApp({

    data() {
        return {
            token: null,
            role: null
        };
    },

    computed: {

        isLoggedIn() {
            return this.token !== null && this.token !== '';
        }

    },

    mounted() {

        console.log('Navbar mounted');

        this.token = localStorage.getItem('access_token');
        this.role = localStorage.getItem('role');

        console.log('Token:', this.token);
        console.log('Role:', this.role);
        console.log('Logged In:', this.isLoggedIn);
    },

    methods: {

        logout() {

            localStorage.removeItem('access_token');
            localStorage.removeItem('role');

            window.location.href = '/';
        }

    }

});

app.config.compilerOptions.delimiters = ['[[', ']]'];

app.mount('#navbar-app');