import axios from 'axios'
// import store from '../store'
//import store from "@/store/StoreAsPlugin";
// import router from '../router'

// Make Axios play nice with Django CSRF
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const base_header = {
     baseURL: "https://127.0.0.1.xip.io:8443/api/",
    //  headers: {
    //     Authorization: `Bearer ${store.state.auth.jwt.access}`,
    //     'Content-Type': 'application/json'
    // },
    //xhrFields: { withCredentials: true }
};

const connect = axios.create(base_header)

// error handling
// connect.interceptors.response.use((response) => {
//   return Promise.resolve(response)
// }, (error) => {
//   if (401 === error.response.status) {
      //router.push('/login')
  //     return Promise.resolve(error)
  // } else {
      // store.dispatch('notifications/add', {
      //     message: "Can't retrieve data",
      //     options: {
      //       color: 'error',
      //       dismissable: true,
      //       showClose: true
      //     }
      // });
//       return Promise.resolve(error)
//   }
// });

export default connect
