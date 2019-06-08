function task_detail() {
}

function edit_task(id) {
      $.get("/api/options/?lists=active_staff,user_worksets,user_task_lists&format=json", function ( data ) {
          const staff = data.active_staff;
          const worksets = data.user_worksets;
          const lists = data.user_task_lists;
          editTaskForm = new $.fn.dataTable.Editor( {
                ajax: {
                  method: "PATCH",
                  url: "/api/tasks/_id_/",
                  headers: { 'X-CSRFToken': get_cookie("csrftoken") },
                  data: function (data) { return { "data": JSON.stringify( data ) }; }
                },
                fields: [
                    {
                      label: "Id",
                      name:  "id",
                      type: "hidden"
                    },
                    {
                      label: "Task",
                      name:  "title"
                    },
                    {
                      label: "Description",
                      name:  "description",
                      type: "textarea"
                    },
                    {
                      label: "List",
                      name:  "task_list",
                      type: "selectize",
                      opts: {'placeholder': "Select list"},
                      message: "Task list to which the task should be added",
                      options: lists
                    },
                    {
                      label: "Assigned to",
                      name:  "assigned_to",
                      type: "selectize",
                      opts: {'placeholder': "Select user"},
                      options: staff
                    },
                    {
                      label: "Due date",
                      name:  "due_date",
                      type: "datetime",
                      format: "YYYY-MM-DD"
                    },
                    {
                      label: "Workset",
                      name:  "workset",
                      message: "Workset to be used for the task, if applicable",
                      type: "selectize",
                      opts: {'placeholder': "Select workset"},
                      options: worksets
                    },
                    {
                      label: "URL",
                      name:  "url",
                      message: "URL related to the task, if applicable",
                      type: "text"
                    },
                    {
                      label: "Attachment",
                      name:  "file",
                      message: "A file to be attached to the task ",
                      type: "upload",
                      ajax: {
                        method: "POST",
                        url: "/api/attachments/",
                        headers: { 'X-CSRFToken': get_cookie("csrftoken")},
                      },
                      display: function (id) {
                        return editTaskForm.file('Attachment', id).filename;
                      },
                      clearText: "Remove File",
                      dragDrop: 'true',
                      dragDropText: "Drag file here",
                      uploadText: "Choose file..."
                    }
                ]
          });
          editTaskForm.on('submitSuccess', function(e, json, data, action) {
            show_message('success', 'The task was updated successfully.');
            location.reload();
          });
          editTaskForm.buttons({
            text: "Update",
            className: "btn btn-primary",
            action: function () { this.submit(); }
          }).title('Edit Task').edit(id, false);
          let file_obj = {}
          file_obj[task['file']] = { id: task['file'], filename: $('.attachment-file-label').text() };
          $.fn.dataTable.Editor.files['Attachment'] = file_obj;
          for (const prop in task) {
              if (task.hasOwnProperty(prop)) {
                  editTaskForm.set(prop, task[prop]);
              }
          };
          editTaskForm.open();
      }, 'json');
}

function task_change_state(task, action) {
    $.ajax({
      method: "GET",
      url: "/api/tasks/"+task+"/set_state/?action="+action,
    }).done(function(data, textStatus, jqXHR) {
          switch (action) {
            case 'mark_undone':
              $('#task_'+task).html('<i class="far fa-square fa-lg"></i>');
              $('.task-d_status').html('Not completed.');
              break;
            case 'mark_done':
              $('#task_'+task).html('<i class="far fa-check-square fa-lg"></i>');
              let today = new Date();
              $('.task-d_status').html('Completed: '+ today.toLocaleDateString("en-GB", { year: 'numeric', month: 'short', day: 'numeric' }));
          }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        show_message('danger', 'There was an error communicating with the server: '+errorThrown);
    });
}