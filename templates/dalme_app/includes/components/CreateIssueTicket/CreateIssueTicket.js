Vue.component('CreateIssueTicket', {
  template: `{% include "dalme_app/includes/components/CreateIssueTicket/CreateIssueTicket.html" %}`,
  data: function () {
    return {
      issueTicket: false,
      subject: null,
      description: null,
      tags: [],
      url: null,
      file: null,
      hasFile: false,
      errors: {
        subject: null,
        description: null,
        tags: null,
        url: null,
        file: null,
      },
    }
  },
  methods: {
    show() {
      this.$refs.issue_ticket_dialogue.show()
    },
    hide() {
      this.$refs.issue_ticket_dialogue.hide()
    },
    onDialogHide() {
      this.$emit('hide')
    },
    onOKClick() {
      this.$emit('ok')
      if (this.hasFile) {
        this.$refs.file_uploader.upload();
      } else {
        this.submit_ticket();
      }
    },
    process_response(data) {
      if (data.fieldErrors) {
        for (let i = 0, len = data.fieldErrors.length; i < len; ++i) {
          if (data.fieldErrors[i].name in this.errors) {
            this.errors[data.fieldErrors[i].name] = data.fieldErrors[i].status;
          }
        }
      } else {
        this.$q.notify({
          message: 'The ticket was created successfully',
          icon: 'fas fa-check',
          color: 'light-green-5',
        });
        this.hide()
      }
    },
    submit_ticket() {
      const form_data = {
        subject: this.subject,
        description: this.description,
        tags: this.tags,
        url: this.url,
        file: this.file
      }
      dalme_base.api_post('tickets', null, form_data, 'POST', this.process_response);
    },
    onCancelClick() {
      this.hide()
    },
    upload_completed(info) {
      let response = JSON.parse(info.xhr.response);
      this.file = response.id;
      this.submit_ticket();
    },
    upload_failed(info) {
      let response = JSON.parse(info.xhr.response);
      let message = '<div class="text-body2">There was a problem uploading the file.';
      if ('error' in response) {
        message += ` The server responded:</div><div class="q-my-sm text-weight-bold text-red-9">${response.error}</div>`;
      } else {
        message += '</div>'
      }
      message += ' <div class="text-body2">Would you like to submit the ticket without it?</div>'
      this.$q.dialog({
        title: 'Upload Failed',
        message: message,
        ok: {
          label: 'Submit ticket',
          flat: true,
          color: 'light-blue-10',
          dense: true,
          'no-caps': true
        },
        cancel: {
          label: 'Cancel',
          flat: true,
          color: 'grey-6',
          dense: true,
          'no-caps': true
        },
        persistent: true,
        html: true,
        'content-class': 'custom-dialogue'
      }).onOk(() => {
        this.file = null;
        this.submit_ticket();
      }).onCancel(() => {
        this.hide();
      })
    }
  }
});
