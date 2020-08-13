import Vue from "vue/dist/vue.js";
import Vuex from "vuex";
import createPersistedState from "vuex-persistedstate";
// import asidemenu from './StoreAsideMenu'

Vue.use(Vuex);

let plugins = [];
plugins.push(createPersistedState({
        paths: ["auth.user"]
    }
));

let store = new Vuex.Store({
    state: {
      endpoints: {
        baseUrl: "https://127.0.0.1.xip.io:8443/",
        apiUrl: "https://127.0.0.1.xip.io:8443/api/",
      },
      user: {
        userName: "pizzorno",
        userId: "1",
        userGroups: "Administrators",
        userAvatar: "https://dalme.org/wp/wp-content/uploads/pizzorno_small.jpg",
        userFullName: "Gabe Pizzorno"
      }
    },
    plugins: plugins,
    // modules: {
    //     asidemenu,
    // },
    strict: process.env.NODE_ENV !== "production",
});

export default {
    store,
    install(Vue) { //resetting the default store to use this store
        Vue.prototype.$store = store;
    }
}
