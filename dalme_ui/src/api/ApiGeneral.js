import api_connect from './ApiConnect'

export default {
  list(request, options) {
    let params = new URLSearchParams()
    for (const option in options) {
      if (options[option] != '') {
        params.append(option, options[option])
      }
    }
    request.method = "get"
    request.url = request.baseurl + params.toString()
    return api_connect(request)
  }
}
