<template>
	<div class="layout-menu-container">
		<SidebarSubmenu :items="model" class="layout-menu" :root="true" @menuitem-click="onMenuItemClick" />
	</div>
</template>

<script>
import SidebarSubmenu from './SidebarSubmenu';

export default {
	props: {
		model: Array
	},
    methods: {
        onMenuItemClick(event) {
            this.$emit('menuitem-click', event);
        }
    },
	components: {
		'SidebarSubmenu': SidebarSubmenu
	}
}
</script>

<style scoped>

</style>
