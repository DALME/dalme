<template>
	<ul v-if="items">
		<template v-for="(item,i) of items">
			<li v-if="item.subheader" class="menu-subheader" :key="i"><span>{{item.label}}</span></li>
			<li v-else :key="i" :class="[{'active-menuitem': activeIndex === i && !item.to}]">
				<div v-if="item.items && root===true" class='arrow'></div>
				<a v-if="item.to" :to="item.to" :class="[{'active-route': activeIndex === i}]" @click="onMenuItemClick($event,item,i)" :target="item.target" exact>
					<i :class="item.icon"></i>
					<span>{{item.label}}</span>
					<i v-if="item.items" class="pi pi-fw pi-angle-down menuitem-toggle-icon"></i>
					<span v-if="item.badge" class="menuitem-badge">{{item.badge}}</span>
				</a>
				<a v-if="!item.to" :href="item.url||'#'" @click="onMenuItemClick($event,item,i)" target="item.target">
					<i :class="item.icon"></i>
					<span>{{item.label}}</span>
					<i v-if="item.items" class="pi pi-fw pi-angle-down menuitem-toggle-icon"></i>
					<span v-if="item.badge" class="menuitem-badge">{{item.badge}}</span>
				</a>
				<transition name="layout-submenu-wrapper">
					<SidebarSubmenu v-show="activeIndex === i" :items="item.items" @menuitem-click="$emit('menuitem-click', $event)"></SidebarSubmenu>
				</transition>
			</li>
		</template>
	</ul>
</template>
<script>
export default {
	name: 'SidebarSubmenu',
	props: {
		items: Array,
		root: {
			type: Boolean,
			default: false
		}
	},
	data() {
		return {
			activeIndex : null
		}
	},
	methods: {
		onMenuItemClick(event, item, index) {
			if (item.disabled) {
				event.preventDefault();
				return;
            }

            if (!item.to && !item.url) {
                event.preventDefault();
            }

			//execute command
			if (item.command) {
                item.command({originalEvent: event, item: item});
			}

			this.activeIndex = index === this.activeIndex ? null : index;

			this.$emit('menuitem-click', {
				originalEvent: event,
				item: item
			});
		}
	},
	components: {
		"SidebarSubmenu": this
	}
}
</script>

<style scoped>

</style>
