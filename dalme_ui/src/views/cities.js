import Vue from "vue/dist/vue.js";
import Vuex from "vuex";
import PersistedStore from "@/store/StorePersistedPlugin";
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import datat from '@/components/dt.vue';
import 'primevue/resources/primevue.min.css';
import 'primevue/resources/themes/saga-blue/theme.css';
import 'primeflex/primeflex.css';
import 'primeicons/primeicons.css';
import '@/styles/layout.scss';

Vue.use(Vuex);
Vue.use(PersistedStore);

Vue.config.productionTip = false;

Vue.component('DataTable', DataTable);
Vue.component('Column', Column);

new Vue({
  el: "#datatable",
  components: { datat },
  data() {
        return { endpoint: 'cities', title: 'List of Cities' }
  }
});
