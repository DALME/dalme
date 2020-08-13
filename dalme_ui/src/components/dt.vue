<template>
  <DataTable :value="entries" :paginator="true" :rows="10">
    <Column v-for="col of headers" :field="col.field" :header="col.header" :key="col.field"></Column>
  </DataTable>
</template>
<script>
import api from '@/api/ApiRouter'

export default {
  props: {
    endpoint: String,
    title: String,
  },
  methods: {
    getData() {
      this.loading = true;
      if (this.search) {
        this.options.search = this.search
      }
      api.get(this.endpoint, 'list', this.options).then(res => {
        this.entries = res.data.results
        this.headers = res.data.headers
        this.total_entries = res.data.itemsPerPage
        this.loading = false
      })
    },
    editItem(item) {
      this.editedIndex = this.entries.indexOf(item)
      this.editedItem = Object.assign({}, item)
      this.dialog = true
    },
    deleteItem(item) {
      const index = this.entries.indexOf(item)
      confirm('Are you sure you want to delete this city?') && this.entries.splice(index, 1)
    },
    close() {
      this.dialog = false
      setTimeout(() => {
        this.editedItem = Object.assign({}, this.defaultItem)
        this.editedIndex = -1
      }, 300)
    },
    save() {
      if (this.editedIndex > -1) {
        Object.assign(this.entries[this.editedIndex], this.editedItem)
      } else {
        this.entries.push(this.editedItem)
      }
      this.close()
    },
  },
  data() {
    return {
      dialog: false,
      notification: false,
      singleSelect: false,
      selected: [],
      search: '',
      total_entries: 0,
      options: {
        page: 1,
        itemsPerPage: 50,
      },
      entries: [],
      loading: true,
      headers: [],
      editedIndex: -1,
      editedItem: {
        name: '',
        administrative_region: '',
        country: '',
      },
      defaultItem: {
        name: '',
        administrative_region: '',
        country: '',
      },
    }
  },
  computed: {
      formTitle() {
        return this.editedIndex === -1 ? 'New City' : 'Edit City'
      },
  },
  watch: {
      options: {
        handler() {
          this.getData()
        }
      },
      search: {
        handler() {
          this.getData()
        }
      },
      dialog(val) {
        val || this.close()
      },
  },
  mounted() {
    this.getData();
  }
};
</script>
