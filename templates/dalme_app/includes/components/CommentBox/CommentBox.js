Vue.component('comment-box', {
  template: `{% include "dalme_app/includes/components/CommentBox/CommentBox.html" %}`,
  props: ['model', 'object'],
  mounted() {
    this.textareaEl = this.$refs.comment_input.$refs.input;
  },
  data: function () {
    return {
      tab: 'write',
      commentBody: '',
      textareaEl: null,
      userQuery: '',
      userList: [],
      userMenu: false,
      ticketQuery: '',
      ticketList: [],
      ticketMenu: false,
      insertMenuTarget: false,
      insertMenuOffset: null,
      codeOptions: [
        {label: 'CSS', value: 'css'},
        {label: 'HTML', value: 'html'},
        {label: 'JavaScript', value: 'js'},
        {label: 'JSON', value: 'json'},
        {label: 'Python', value: 'py'},
        {label: 'XML/TEI', value: 'xml'}
      ],
      toolbar: {% include "dalme_app/includes/components/CommentBox/ToolbarConfig.js" %},
    }
  },
  watch: {
    userQuery: 'filter_user_list',
    ticketQuery: 'filter_ticket_list'
  },
  methods: {
    insert_text(text) {
      const [start, end] = this.get_selection();
      this.commentBody = this.commentBody.slice(0, start) + text + this.commentBody.slice(end);
    },
    insert_enclosure(marks) {
      const [start, end] = this.get_selection();
      if (start == end || !this.commentBody) {
        this.commentBody = `${marks[0]}${marks[1]}`
        this.textareaEl.focus();
        setTimeout(()=> { this.textareaEl.setSelectionRange(marks[0].length, marks[0].length) }, 1)
      } else {
        const selected = this.commentBody.substring(start, end);
        this.commentBody = this.commentBody.slice(0, start) + `${marks[0]}${selected}${marks[1]}` + this.commentBody.slice(end);
        this.textareaEl.focus();
      }
    },
    insert_prefix(mark) {
      const [start, end] = this.get_selection();
      if (start == end || !this.commentBody) {
        this.commentBody = mark == 'numbered' ? '1. ' : mark;
        this.textareaEl.focus();
      } else {
        let lines = this.commentBody.substring(start, end).split('\n');
        lines.forEach((line, i) => {
          let lead = mark == 'numbered' ? `${i + 1}. ` : mark;
          lines[i] = `${lead}${line}`;
        });
        this.commentBody = this.commentBody.slice(0, start) + lines.join('\n') + this.commentBody.slice(end);
        this.textareaEl.focus();
      }
    },
    get_list(type) {
      const query = type == 'user' ? this.userQuery : this.ticketQuery;
      dalme_base.api_fetch(`${type}s`, null, { search: query }, this.set_list, type);
    },
    set_list(data, type) {
      if (type == 'user') {
        this.userList = data;
        this.insert_text('@')
      } else {
        this.ticketList = data.results;
        this.insert_text('#')
      }
      this.textareaEl.focus();
      let caret = window.getCaretCoordinates(this.textareaEl, this.textareaEl.selectionEnd);
      this.insertMenuTarget = true;
      this.insertMenuTarget = this.textareaEl;
      this.insertMenuOffset = [`-${caret.left + 15}`, `-${caret.top + caret.height + 5}`]
      this.$data[`${type}Menu`] = true;
    },
    get_selection() {
      return [this.textareaEl.selectionStart || 0, this.textareaEl.selectionEnd];
    },
    callback(data) {
      this.commentBody = null;
      this.$emit('created', data);
    },
    save_comment() {
      if (this.commentBody) {
        const form_data = {
          model: this.model,
          object: this.object,
          body: this.commentBody
        }
        dalme_base.api_post('comments', null, form_data, 'POST', this.callback);
      }
    }
  }
});
