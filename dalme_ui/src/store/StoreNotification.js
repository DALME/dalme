import Vue from 'vue'
//const notificationTimeout = callback => setTimeout(callback, 300000);

export default {
    name: 'notifications',
    namespaced: true,
    state: [],
    actions: {
        add({ commit }, notification) {
            // add the new notification to the queue
            //const id = Math.floor(Date.now() + Math.random())
            commit('enqueue', [ notification ]);

            // if there isn't already an active notification, dispatch the
            // processQueue action immediately show it and will
            // continue handling any notification that gets added after
            //if (!state.active) dispatch('processQueue');
        },
        remove({ commit }) {
            commit('dequeue');
        }
        // processQueue({ state, commit, dispatch }, ) {
        //       // In case this action gets dispatched with nothing to do
        //       if (!state.queue.length && !state.active) return;
        //
        //       // If the queue is empty, but there's an active notification,
        //       // we just need to reset the state after the display timeout
        //       if (!state.queue.length && state.active)
        //         return notificationTimeout(() => commit('reset'));
        //
        //       // This just uses setTimeout to recursively dispatch this
        //       // action to display each notification 1 at a time until the queue
        //       // is empty
        //       const timeoutId = notificationTimeout(() => dispatch('processQueue'));
        //
        //       // Dequeue the next notification and add the timeoutId to the
        //       // store so it can be cancelled if necessary
        //       commit('dequeue', { timeoutId });
        // },
    },
    mutations: {
        enqueue(state, notification) {
            //const queue = [...state.queue, notification];
            this.state.notifications = Object.assign([], this.state.notifications, notification)
            //Vue.set(state.queue, notification)
            //state = { ...state, queue };
        },
        dequeue(state) {
            // const [active, ...queue] = state.queue;
            // state = {
            //   ...state,
            //   queue,
            //   active,
            //   timeoutId,
            // };
            //delete state[id];
            Vue.delete(state, 0)
        },
        // reset(state) {
        //     state = {
        //       queue: [],
        //       active: undefined,
        //       timeoutId: undefined,
        //     };
        //},
    }
}
