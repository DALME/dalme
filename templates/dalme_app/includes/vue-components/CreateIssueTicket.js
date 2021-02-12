Vue.component('CreateIssueTicket', {
  template: `{% include "dalme_app/includes/vue-components/CreateIssueTicket.html" %}`,
  data: function () {
    return {
      issueTicket: false,
      subject: null,
      description: null,
      tags: [],
      url: null,
      file: null,
      hasFile: false,
      tagOptions: [
        { label: 'bug', value: 'bug', color: 'red-3' },
        { label: 'content', value: 'content', color: 'amber-3' },
        { label: 'documentation', value: 'documentation', color: 'light-blue-3' },
        { label: 'feature', value: 'feature', color: 'deep-purple-3' },
        { label: 'question', value: 'question', color: 'light-green-3' }
      ],
      uploadUrl: `${dalme_nav.$data.apiEndpoint}/attachments/`,
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
    submit_ticket() {
      const that = this;
      fetch(`${dalme_nav.$data.apiEndpoint}/tickets/`, {
        method: 'POST',
        mode: 'cors',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': that.$q.cookies.get('csrftoken')
        },
        redirect: 'follow',
        body: JSON.stringify({
          subject: that.subject,
          description: that.description,
          tags: that.tags,
          url: that.url,
          file: that.file
        })
      }).then(response => {
        if (response.status == 400) {
          return response.json()
        }
        else if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json()
      }).then(data => {
        if (data.fieldErrors) {
          for (let i = 0, len = data.fieldErrors.length; i < len; ++i) {
            if (data.fieldErrors[i].name in that.errors) {
              that.errors[data.fieldErrors[i].name] = data.fieldErrors[i].status;
            }
          }
        } else {
          that.$q.notify({
            message: 'The ticket was created successfully',
            icon: 'fas fa-check',
            color: 'light-green-5',
          });
          that.hide()
        }
      })
      .catch((error) => {
        that.$q.notify({
          message: `There was a problem communicating with the server. ${error}`,
          icon: 'fas fa-times',
          color: 'red-3',
        });
        that.hide()
      });
    },
    onCancelClick() {
      this.hide()
    },
    uploadHeaders() {
      return [{name: 'X-CSRFToken', value: this.$q.cookies.get('csrftoken')}]
    },
    upload_completed(info) {
      let response = JSON.parse(info.xhr.response);
      this.file = response.id;
      this.submit_ticket();
    },
    upload_failed(info) {
      let response = JSON.parse(info.xhr.response);
      let message = '<div class="text-body2">There was a problem uploading the attachment.';
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
