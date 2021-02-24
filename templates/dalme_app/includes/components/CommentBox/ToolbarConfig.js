[
  [
    {
      type: 'button',
      icon: 'fas fa-heading',
      hint: 'Add heading',
      handler: this.insert_enclosure,
      payload: ['### ', '']
    },
    {
      type: 'button',
      icon: 'fas fa-bold',
      hint: 'Add bold text',
      handler: this.insert_enclosure,
      payload: ['**', '**']
    },
    {
      type: 'button',
      icon: 'fas fa-italic',
      hint: 'Add italic text',
      handler: this.insert_enclosure,
      payload: ['*', '*']
    },
    {
      type: 'button',
      icon: 'fas fa-strikethrough',
      hint: 'Add strike-through text',
      handler: this.insert_enclosure,
      payload: ['~~', '~~']
    },
  ],
  [
    {
      type: 'button',
      icon: 'fas fa-highlighter',
      hint: 'Highlight text',
      handler: this.insert_enclosure,
      payload: ['==', '==']
    },
  ],
  [
    {
      type: 'button',
      icon: 'fas fa-quote-right',
      hint: 'Insert a quote',
      handler: this.insert_prefix,
      payload: '> '
    },
    {
      type: 'code_select',
      icon: 'fas fa-code',
      hint: 'Insert code'
    },
    {
      type: 'button',
      icon: 'fas fa-link',
      hint: 'Insert a link',
      handler: this.insert_enclosure,
      payload: ['[', '](url)']
    },
    {
      type: 'button',
      icon: 'fas fa-sticky-note',
      hint: 'Insert a note',
      handler: this.insert_enclosure,
      payload: [':::\n', '\n:::']
    },
  ],
  [
    {
      type: 'button',
      icon: 'fas fa-list-ul',
      hint: 'Add a bulleted list',
      handler: this.insert_prefix,
      payload: '- '
    },
    {
      type: 'button',
      icon: 'fas fa-list-ol',
      hint: 'Add a numbered list',
      handler: this.insert_prefix,
      payload: 'numbered'
    },
    {
      type: 'button',
      icon: 'far fa-check-square',
      hint: 'Add a task list',
      handler: this.insert_prefix,
      payload: '- [ ] '
    },
  ],
  [
    {
      type: 'user',
      icon: 'fas fa-at',
      hint: 'Directly mention a user or team',
      model: 'userMenu',
      list: 'userList',
      key: 'username'
    },
    {
      type: 'ticket',
      icon: 'fas fa-bug',
      hint: 'Reference another issue ticket',
      model: 'ticketMenu',
      list: 'ticketList',
      key: 'id'
    },
  ]
]
