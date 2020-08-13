import general_api from './ApiGeneral'

const routes = {
  cities: (call, options) => { return general_api[call]({ baseurl: "cities/?" }, options)},
}

export default {
  get: (endpoint, call, options) => routes[endpoint](call, options)
}
