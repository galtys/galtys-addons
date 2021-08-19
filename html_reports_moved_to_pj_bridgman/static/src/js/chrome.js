openerp.web_voip_redirect = function(instance) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    
    instance.web.Menu.include({
    	menu_loaded: function(data) {
            var self = this;
            this.data = {data: data};
            this.renderElement();
            this.$secondary_menus.html(QWeb.render("Menu.secondary", { widget : this }));
            this.$el.on('click', 'a[data-menu]', this.on_top_menu_click);
            // Hide second level submenus
            this.$secondary_menus.find('.oe_menu_toggler').siblings('.oe_secondary_submenu').hide();
            if (self.current_menu) {
                self.open_menu(self.current_menu);
            }
            this.trigger('menu_loaded', data);
            this.has_been_loaded.resolve();
            this.rpc("/web/redirect/get_url", {}).done(function(result) {
            	if (result != false){
            		instance.web.redirect(result,{});
            	}
            });
        },
     });
     
};

