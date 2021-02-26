Vue.component('user-popover', {
  template: `{% include "dalme_app/includes/components/UserPopover/UserPopover.html" %}`,
  props: ['id', 'username', 'full_name', 'avatar'],
});
